"""Catalog schema tests."""

from cli.catalog import (
    clone_workflow,
    get_domain,
    get_workflow,
    load_domains,
    resolve_domain_id,
    select_ingest_source,
    validate_slug,
)


def test_all_domain_catalogs_validate():
    domains = load_domains()
    ids = {d.id for d in domains}
    assert ids == {"bfs", "hcls", "retail", "org", "other"}
    for domain in domains:
        assert domain.workflows
        seen = set()
        for workflow in domain.workflows:
            assert workflow.id not in seen
            seen.add(workflow.id)
            assert workflow.agents
            assert workflow.summary
            node_ids = {n.id for n in workflow.graph.nodes}
            assert workflow.graph.entry in node_ids


def test_other_domain_and_clone_workflow():
    assert resolve_domain_id("custom") == "other"
    other = get_domain("custom")
    assert other.id == "other"
    starter = get_workflow("other", "custom")
    assert len(starter.agents) == 3
    cloned = clone_workflow(starter, id="intake", name="Intake")
    assert cloned.id == "intake"
    assert cloned.name == "Intake"
    assert cloned.graph.entry == starter.graph.entry


def test_validate_slug_rejects_spaces_and_caps():
    import pytest

    with pytest.raises(ValueError, match="lowercase slug"):
        validate_slug("My Flow", kind="workflow")
    assert validate_slug("intake_v1", kind="workflow") == "intake_v1"


def test_bfs_workflows_and_alias():
    assert resolve_domain_id("banking") == "bfs"
    bfs = get_domain("banking")
    assert {w.id for w in bfs.workflows} == {"afi", "clu", "rca"}
    assert get_workflow("bfs", "fraud").id == "afi"


def test_retail_gsse_workflow():
    assert get_workflow("retail", "gsse").name == "Geospatial Site Suitability Engine"
    assert get_workflow("retail", "Geospatial Site Suitability Engine").id == "gsse"
    wf = get_workflow("retail", "site-suitability")
    assert {a.name for a in wf.agents} == {
        "gsse_ingest",
        "gsse_gold",
        "gsse_scorer",
        "gsse_analyst",
        "gsse_explainer",
        "gsse_confirm",
    }
    confirm = next(n for n in wf.graph.nodes if n.id == "confirm")
    assert confirm.requires_hitl is True
    assert wf.recommended_stack.assets is True
    assert wf.recommended_stack.asset_pack == "district_dine"
    assert wf.recommended_stack.adk is True
    assert wf.sdk is not None
    assert wf.sdk.query == "district_dine"


def test_workflows_have_mcp_evals_and_skills():
    for domain in load_domains():
        if domain.id != "org":
            assert domain.mcp_servers
        for workflow in domain.workflows:
            assert workflow.skills
            assert workflow.tools
            assert workflow.evals


def test_training_coordinator_catalog_and_tool_contracts():
    wf = get_workflow("hr", "training-coordinator")
    assert wf.id == "training-coordinator-agent"
    assert wf.sdk is not None
    assert "training" in wf.sdk.query
    assert get_workflow("org", "hr-onboarding-agent").id == "training-coordinator-agent"
    assert wf.name == "Training Coordinator Agent"
    assert len(wf.tool_specs) == 19
    assert {item["name"] for item in wf.tool_specs} == set(wf.tools)
    assert {item.path for item in wf.files} == {
        "governance.md",
        "trainings.md",
        "logic_tools.py",
    }
    review = next(node for node in wf.graph.nodes if node.id == "review")
    assert review.requires_hitl is True
    assert get_domain("org").mcp_servers == []
    assert wf.opa is not None
    assert wf.opa.data["training"]["drafts_only"] is True
    assert wf.opa.data["training"]["programs"]["OEM_Parts"]["min_tenure_days"] == 30
    assert {p.filename for p in wf.opa.policies} == {"eligibility.rego", "actions.rego"}
    assert "allow_send" in next(p.content for p in wf.opa.policies if p.filename == "actions.rego")
    assert "require_hitl" in next(
        p.content for p in wf.opa.policies if p.filename == "eligibility.rego"
    )
    eval_ids = [item.id for item in wf.evals]
    assert eval_ids == [
        "capability",
        "ingest_sharepoint",
        "ingest_workday",
        "deterministic_eligibility",
        "eligibility_below_tenure",
        "opa_hitl_exception",
        "reconcile_calendar_wins",
        "draft_only",
        "draft_no_send",
        "review_hitl",
        "tracker_read_only",
        "whats_due_scan",
    ]
    assert any("compute_eligibility" in item.query for item in wf.evals)
    assert any("do not send" in item.query.lower() for item in wf.evals)

    sharepoint = select_ingest_source(wf, "sharepoint")
    workday = select_ingest_source(wf, "workday")
    sharepoint_ingest = next(a for a in sharepoint.agents if a.name == "tca_ingest")
    workday_ingest = next(a for a in workday.agents if a.name == "tca_ingest")
    assert sharepoint_ingest.allowed_tools == ["sharepoint_workday_export_reader"]
    assert workday_ingest.allowed_tools == ["workday_new_hire_lookup"]


def test_retail_dispute_handler_workflow():
    wf = get_workflow("retail", "dispute_handler")
    assert wf.name == "Autonomous Dispute Processor"
    assert get_workflow("retail", "disputes").id == "dispute_handler"
    assert get_workflow("retail", "accr").id == "dispute_handler"
    assert {a.name for a in wf.agents} == {
        "dispute_triage",
        "dispute_audit",
        "dispute_review",
        "dispute_settle",
    }
    review = next(n for n in wf.graph.nodes if n.id == "review")
    assert review.requires_hitl is True
    assert wf.opa is not None
    assert wf.opa.data["dispute"]["max_auto_settle_usd"] == 100.0
    assert any(p.filename == "settle.rego" for p in wf.opa.policies)


def test_recommended_stacks_match_plan():
    expected = {
        ("bfs", "afi"): ("litellm", "redis", "memory"),
        ("bfs", "clu"): ("litellm", "memory", "opensearch"),
        ("bfs", "rca"): ("openai", "memory", "memory"),
        ("hcls", "epa"): ("litellm", "redis", "memory"),
        ("hcls", "ctpm"): ("litellm", "memory", "qdrant"),
        ("hcls", "addw"): ("ollama", "memory", "memory"),
        ("retail", "dispute_handler"): ("litellm", "memcached", "memory"),
        ("retail", "dcap"): ("litellm", "redis", "memory"),
        ("retail", "avmts"): ("litellm", "memory", "opensearch"),
        ("retail", "gsse"): ("litellm", "memory", "memory"),
    }
    for (domain, workflow), (gateway, cache, vector) in expected.items():
        stack = get_workflow(domain, workflow).recommended_stack
        assert (stack.gateway, stack.cache, stack.vector) == (gateway, cache, vector)
