"""Non-interactive init tests."""

import re
from pathlib import Path

from typer.testing import CliRunner

from cli.main import app

runner = CliRunner(env={"NO_COLOR": "1", "TERM": "dumb"})

REQUIRED = (
    "app",
    "agents",
    "factories",
    "config",
    "shared",
    "tests",
    "evals",
    "docs",
    "examples",
    "deployment",
)


def test_init_dry_run_writes_nothing(tmp_path: Path):
    dest = tmp_path / "demo"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "demo",
            "--output",
            str(dest),
            "--domain",
            "retail",
            "--workflow",
            "dispute_handler",
            "--framework",
            "none",
            "--yes",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Dry run" in result.output
    assert not dest.exists()


def test_init_yes_copies_full_tree_and_one_workflow(tmp_path: Path):
    dest = tmp_path / "hcls-epa"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "hcls-epa",
            "--output",
            str(dest),
            "--domain",
            "healthcare",
            "--workflow",
            "prior authorization",
            "--gateway",
            "litellm",
            "--cache",
            "memory",
            "--vector",
            "opensearch",
            "--opensearch-url",
            "http://localhost:9200",
            "--framework",
            "none",
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    for name in REQUIRED:
        assert (dest / name).is_dir(), name
    assert (dest / "factories" / "cache" / "memcached").is_dir()
    wf = dest / "domains" / "hcls" / "workflows"
    assert (wf / "epa" / "graph.yaml").exists()
    assert (wf / "epa" / "agents" / "epa_intake.yaml").exists()
    epa_readme = (wf / "epa" / "README.md").read_text(encoding="utf-8")
    assert "Prior" in epa_readme or "epa_intake" in epa_readme
    assert not (wf / "ctpm").exists()
    env = (dest / ".env").read_text(encoding="utf-8")
    assert "CACHE_BACKEND=memory" in env
    assert "VECTOR_BACKEND=opensearch" in env
    app_yaml = (dest / "config" / "app.yaml").read_text(encoding="utf-8")
    assert "domain: hcls" in app_yaml
    assert "workflow: epa" in app_yaml
    assert "plan: accepted" in app_yaml
    assert "mcp:" in app_yaml
    assert "hcls-interoperability" in app_yaml
    assert "CoverageRulesEngine" in app_yaml
    readme = (dest / "README.md").read_text(encoding="utf-8")
    assert readme.startswith("# hcls-epa")
    assert "list-domains" not in readme
    assert "Artifact Registry" not in readme
    assert "Generate a project" not in readme
    assert (dest / "evals" / "epa" / "app.evalset.json").exists()
    assert not (dest / "config" / "project.yaml").exists()
    assert (dest / "factory-choices.json").exists()
    assert not (dest / "catalogs").exists()
    assert not (dest / "cli").exists()
    assert not (dest / "agents_cli").exists()
    pyproject = (dest / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "hcls-epa"' in pyproject
    assert "66harness" not in pyproject
    assert "66degrees-factory" not in pyproject
    assert '"catalogs" = "catalogs"' not in pyproject
    assert 'packages = ["agents", "app", "shared", "factories", "config"]' in pyproject


def test_list_domains():
    result = runner.invoke(app, ["list-domains"])
    assert result.exit_code == 0
    assert "bfs" in result.output
    assert "hcls" in result.output
    assert "retail" in result.output
    assert "org" in result.output
    assert "other" in result.output


def test_list_workflows_bfs_alias():
    result = runner.invoke(app, ["list-workflows", "--domain", "banking"])
    assert result.exit_code == 0
    assert "afi" in result.output
    assert "clu" in result.output
    assert "rca" in result.output


def test_list_workflows_other():
    result = runner.invoke(app, ["list-workflows", "--domain", "other"])
    assert result.exit_code == 0
    assert "custom" in result.output


def test_init_training_coordinator_defaults_to_sharepoint(tmp_path: Path):
    dest = tmp_path / "training-coordinator"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "training-coordinator",
            "--output",
            str(dest),
            "--domain",
            "org",
            "--workflow",
            "training-coordinator-agent",
            "--framework",
            "none",
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    base = dest / "domains" / "org" / "workflows" / "training-coordinator-agent"
    manifest = (base / "agents" / "tca_ingest.yaml").read_text(encoding="utf-8")
    assert "sharepoint_workday_export_reader" in manifest
    assert "workday_new_hire_lookup" not in manifest
    assert (base / "governance.md").exists()
    assert (base / "trainings.md").exists()
    assert (base / "logic_tools.py").exists()
    toolspec = (base / "tools" / "toolspec.json").read_text(encoding="utf-8")
    assert '"draft_teams_message"' in toolspec
    assert '"requireConfirmation": true' in toolspec
    app_yaml = (dest / "config" / "app.yaml").read_text(encoding="utf-8")
    assert "ingest:\n  source: sharepoint" in app_yaml
    assert "servers: []" in app_yaml
    choices = (dest / "factory-choices.json").read_text(encoding="utf-8")
    assert '"ingest_source": "sharepoint"' in choices
    opa = dest / "domains" / "org" / "workflows" / "training-coordinator-agent" / "policies" / "opa"
    assert (opa / "eligibility.rego").exists()
    assert (opa / "actions.rego").exists()
    data = (opa / "data.json").read_text(encoding="utf-8")
    assert "drafts_only" in data
    assert "min_tenure_days" in data
    assert "allow_send" in (opa / "actions.rego").read_text(encoding="utf-8")
    assert "require_hitl" in (opa / "eligibility.rego").read_text(encoding="utf-8")
    evalset = (
        dest / "evals" / "training-coordinator-agent" / "app.evalset.json"
    ).read_text(encoding="utf-8")
    for eval_id in (
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
    ):
        assert eval_id in evalset
    assert "compute_eligibility" in evalset
    assert "do not send" in evalset
    assert "evals:" in app_yaml
    assert "deterministic_eligibility" in app_yaml
    assert "opa_hitl_exception" in app_yaml
    readme = (base / "README.md").read_text(encoding="utf-8")
    assert "policies/opa/eligibility.rego" in readme


def test_init_training_coordinator_selects_workday(tmp_path: Path):
    dest = tmp_path / "training-coordinator-workday"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "training-coordinator-workday",
            "--output",
            str(dest),
            "--domain",
            "hr",
            "--workflow",
            "training-coordinator",
            "--ingest-source",
            "workday",
            "--framework",
            "none",
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    manifest = (
        dest
        / "domains"
        / "org"
        / "workflows"
        / "training-coordinator-agent"
        / "agents"
        / "tca_ingest.yaml"
    ).read_text(encoding="utf-8")
    assert "workday_new_hire_lookup" in manifest
    assert "sharepoint_workday_export_reader" not in manifest
    app_yaml = (dest / "config" / "app.yaml").read_text(encoding="utf-8")
    assert "ingest:\n  source: workday" in app_yaml


def test_list_factories():
    result = runner.invoke(app, ["list-factories"])
    assert result.exit_code == 0
    assert "cache" in result.output
    assert "qdrant" in result.output
    assert "looker" in result.output
    assert "bqml" in result.output
    assert "assets" in result.output


def test_init_yes_looker_bqml(tmp_path: Path):
    dest = tmp_path / "demo-analytics"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "demo-analytics",
            "--output",
            str(dest),
            "--domain",
            "other",
            "--workflow",
            "site_selection",
            "--custom-domain",
            "district_dine",
            "--looker",
            "--bqml",
            "--framework",
            "none",
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    env = (dest / ".env").read_text(encoding="utf-8")
    assert "LOOKER_ENABLED=true" in env
    assert "LOOKERSDK_CLIENT_ID=CHANGE_ME" in env
    assert "BQML_ENABLED=true" in env
    app_yaml = (dest / "config" / "app.yaml").read_text(encoding="utf-8")
    assert "looker:" in app_yaml
    assert "bqml:" in app_yaml
    assert "enabled: true" in app_yaml


def test_init_yes_default_looker_bqml_off(tmp_path: Path):
    dest = tmp_path / "demo-afi"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "demo-off",
            "--output",
            str(dest),
            "--domain",
            "bfs",
            "--workflow",
            "afi",
            "--framework",
            "none",
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    env = (dest / ".env").read_text(encoding="utf-8")
    assert "LOOKER_ENABLED" not in env
    assert "BQML_ENABLED" not in env
    assert "ASSETS_ENABLED" not in env
    assert "ASSETS_CENSUS" not in env
    assert "AGENT_CLI_ENABLED=false" in env


def test_init_yes_assets(tmp_path: Path):
    dest = tmp_path / "demo-assets"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "demo-assets",
            "--output",
            str(dest),
            "--domain",
            "other",
            "--workflow",
            "intake",
            "--custom-domain",
            "acme",
            "--assets",
            "--framework",
            "none",
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    env = (dest / ".env").read_text(encoding="utf-8")
    assert "ASSETS_ENABLED=true" in env
    assert "ASSETS_PACK=core" in env
    assert "ASSETS_SQL_DB_URL=CHANGE_ME" in env
    assert "ASSETS_CENSUS_STATE_FIPS=17" in env
    assert "ASSETS_NAV_REGION_BOUNDARY=chicago_metro" in env
    app_yaml = (dest / "config" / "app.yaml").read_text(encoding="utf-8")
    assert "assets:" in app_yaml
    assert "asset-factory" in result.output


def test_init_dry_run_qdrant_env(tmp_path: Path):
    dest = tmp_path / "qdemo"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "qdemo",
            "--output",
            str(dest),
            "--domain",
            "bfs",
            "--workflow",
            "afi",
            "--vector",
            "qdrant",
            "--framework",
            "none",
            "--yes",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "VECTOR_BACKEND=qdrant" in result.output


def test_init_yes_writes_recommended_stack(tmp_path: Path):
    dest = tmp_path / "demo-afi"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "demo-afi",
            "--output",
            str(dest),
            "--domain",
            "bfs",
            "--workflow",
            "afi",
            "--framework",
            "none",
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    app_yaml = (dest / "config" / "app.yaml").read_text(encoding="utf-8")
    assert "domain: bfs" in app_yaml
    assert "workflow: afi" in app_yaml
    assert "backend: redis" in app_yaml
    assert "workflow:" in app_yaml
    assert "afi_intake" in app_yaml
    assert "evals:" in app_yaml
    assert "bfs-operations" in app_yaml
    assert "langfuse:" in app_yaml
    assert "host:" in app_yaml
    assert "hcls:" not in app_yaml
    env = (dest / ".env").read_text(encoding="utf-8")
    assert "CACHE_BACKEND=redis" in env
    assert "GATEWAY_PROVIDER=litellm" in env
    assert "BFS_MCP_TOKEN=CHANGE_ME" in env
    evalset = (dest / "evals" / "afi" / "app.evalset.json").read_text(encoding="utf-8")
    assert "capability" in evalset
    assert "account 4412" in evalset


def test_init_yes_other_custom_slugs(tmp_path: Path):
    dest = tmp_path / "demo-custom"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "demo-custom",
            "--output",
            str(dest),
            "--domain",
            "other",
            "--workflow",
            "intake",
            "--custom-domain",
            "acme",
            "--framework",
            "none",
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    assert (dest / "domains" / "acme" / "workflows" / "intake" / "graph.yaml").exists()
    assert (dest / "domains" / "acme" / "workflows" / "intake" / "agents" / "intake.yaml").exists()
    custom_readme = (
        dest / "domains" / "acme" / "workflows" / "intake" / "README.md"
    ).read_text(encoding="utf-8")
    assert "intake" in custom_readme.lower()
    app_yaml = (dest / "config" / "app.yaml").read_text(encoding="utf-8")
    assert "domain: acme" in app_yaml
    assert "workflow: intake" in app_yaml
    assert "other-operations" in app_yaml
    assert "OTHER_MCP_TOKEN=CHANGE_ME" in (dest / ".env").read_text(encoding="utf-8")
    readme = (dest / "README.md").read_text(encoding="utf-8")
    assert readme.startswith("# demo-custom")
    assert "hcls" not in app_yaml


def test_init_yes_other_rejects_invalid_workflow(tmp_path: Path):
    dest = tmp_path / "bad"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "bad",
            "--output",
            str(dest),
            "--domain",
            "other",
            "--workflow",
            "My Flow",
            "--framework",
            "none",
            "--yes",
        ],
    )
    assert result.exit_code != 0
    assert "lowercase slug" in result.output


def test_from_choices_app_yaml(tmp_path: Path):
    src_yaml = tmp_path / "app.yaml"
    src_yaml.write_text(
        "project:\n  domain: bfs\n  workflow: afi\n  plan: accepted\n"
        "cache:\n  backend: memory\n"
        "vector:\n  backend: memory\n",
        encoding="utf-8",
    )
    dest = tmp_path / "replay"
    result = runner.invoke(
        app,
        [
            "init",
            "--from-choices",
            str(src_yaml),
            "--name",
            "replay",
            "--output",
            str(dest),
            "--dry-run",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "bfs" in result.output
    assert "afi" in result.output


def test_copy_skips_site_packages_neighbors(tmp_path: Path):
    from cli.copier import copy_template

    src = tmp_path / "site-packages"
    src.mkdir()
    (src / "app").mkdir()
    (src / "app" / "main.py").write_text("# app\n", encoding="utf-8")
    (src / "factories").mkdir()
    (src / "factories" / "ok.py").write_text("# factories\n", encoding="utf-8")
    (src / "pyproject.toml").write_text(
        '[project]\nname = "multi-agent-factory"\n',
        encoding="utf-8",
    )
    (src / "aiohttp").mkdir()
    (src / "aiohttp" / "__init__.py").write_text("# leak\n", encoding="utf-8")
    (src / "aiohttp-3.14.3.dist-info").mkdir()
    (src / "aiohttp-3.14.3.dist-info" / "METADATA").write_text("Name: aiohttp\n", encoding="utf-8")
    (src / "_cffi_backend.cpython-312-darwin.so").write_bytes(b"\x00")

    dest = tmp_path / "out"
    written = copy_template(src, dest)
    assert "app/main.py" in written
    assert "factories/ok.py" in written
    assert "pyproject.toml" in written
    assert not (dest / "aiohttp").exists()
    assert not (dest / "aiohttp-3.14.3.dist-info").exists()
    assert not (dest / "_cffi_backend.cpython-312-darwin.so").exists()


def test_init_yes_gsse_defaults_assets_adk(tmp_path: Path):
    dest = tmp_path / "district-dine"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "district-dine",
            "--output",
            str(dest),
            "--domain",
            "retail",
            "--workflow",
            "gsse",
            "--framework",
            "none",
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    env = (dest / ".env").read_text(encoding="utf-8")
    assert "ASSETS_ENABLED=true" in env
    assert "ASSETS_PACK=district_dine" in env
    assert "ADK_ENABLED=true" in env
    assert "GEMINI_ENTERPRISE_ENABLED" not in env
    assert "AGENT_CLI_ENABLED=false" in env
    graph = (dest / "domains" / "retail" / "workflows" / "gsse" / "graph.yaml").read_text(
        encoding="utf-8"
    )
    assert "confirm" in graph
    assert "requires_hitl: true" in graph
    readme = (dest / "domains" / "retail" / "workflows" / "gsse" / "README.md").read_text(
        encoding="utf-8"
    )
    assert "Geospatial Site Suitability Engine" in readme
    assert "Asset pack: `district_dine`" in readme
    assert "gsse_ingest" in readme
    assert not (dest / "domains" / "retail" / "workflows" / "gsse" / "gemini_enterprise").exists()


def test_init_yes_gsse_no_assets(tmp_path: Path):
    dest = tmp_path / "gsse-off"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "gsse-off",
            "--output",
            str(dest),
            "--domain",
            "retail",
            "--workflow",
            "gsse",
            "--no-assets",
            "--framework",
            "none",
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    env = (dest / ".env").read_text(encoding="utf-8")
    assert "ASSETS_ENABLED" not in env
    assert "ASSETS_PACK" not in env
    assert "ASSETS_SQL_DB_URL" not in env
    assert "ASSETS_CENSUS_STATE_FIPS" not in env


def test_init_yes_gsse_gemini_enterprise(tmp_path: Path):
    dest = tmp_path / "gsse-ge"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "gsse-ge",
            "--output",
            str(dest),
            "--domain",
            "retail",
            "--workflow",
            "Geospatial Site Suitability Engine",
            "--gemini-enterprise",
            "--framework",
            "none",
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    env = (dest / ".env").read_text(encoding="utf-8")
    assert "GEMINI_ENTERPRISE_ENABLED=true" in env
    assert "ASSETS_ENABLED=true" in env
    assert "ADK_ENABLED=true" in env
    ge = dest / "domains" / "retail" / "workflows" / "gsse" / "gemini_enterprise"
    assert (ge / "agent.yaml").exists()
    assert (ge / "actions" / "confirm_site.json").exists()
    assert (ge / "README.md").exists()
    assert "gemini-enterprise" in result.output


def test_init_yes_dispute_handler_writes_opa_and_hitl(tmp_path: Path):
    dest = tmp_path / "dispute-demo"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "dispute-demo",
            "--output",
            str(dest),
            "--domain",
            "retail",
            "--workflow",
            "returns",
            "--framework",
            "none",
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    wf = dest / "domains" / "retail" / "workflows" / "dispute_handler"
    graph = (wf / "graph.yaml").read_text(encoding="utf-8")
    assert "dispute_triage" in graph
    assert "requires_hitl: true" in graph
    assert (wf / "policies" / "opa" / "settle.rego").exists()
    data = (wf / "policies" / "opa" / "data.json").read_text(encoding="utf-8")
    assert "max_auto_settle_usd" in data
    readme = (wf / "README.md").read_text(encoding="utf-8")
    assert "Autonomous Dispute Processor" in readme
    assert "OPA" in readme
    assert (wf / "agents" / "dispute_settle.yaml").exists()


def test_init_yes_dispute_handler_assets_core_pack(tmp_path: Path):
    dest = tmp_path / "dispute-assets"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "dispute-assets",
            "--output",
            str(dest),
            "--domain",
            "retail",
            "--workflow",
            "dispute_handler",
            "--assets",
            "--framework",
            "none",
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    env = (dest / ".env").read_text(encoding="utf-8")
    assert "ASSETS_ENABLED=true" in env
    assert "ASSETS_PACK=core" in env


def test_init_yes_gsse_asset_pack_all(tmp_path: Path):
    dest = tmp_path / "gsse-all"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "gsse-all",
            "--output",
            str(dest),
            "--domain",
            "retail",
            "--workflow",
            "gsse",
            "--asset-pack",
            "all",
            "--framework",
            "none",
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    env = (dest / ".env").read_text(encoding="utf-8")
    assert "ASSETS_ENABLED=true" in env
    assert "ASSETS_PACK=all" in env


def _fake_agents_cli_create(monkeypatch):
    calls: list[list[str]] = []

    def fake_which(name: str) -> str | None:
        if name == "agents-cli":
            return "/usr/bin/agents-cli"
        return None

    def fake_run(args, check=False):
        calls.append(list(args))
        parent = Path(args[args.index("-o") + 1])
        kebab = args[2]
        app_dir = parent / kebab / "app"
        app_dir.mkdir(parents=True, exist_ok=True)
        (app_dir / "agent.py").write_text(
            "from google.adk.agents import Agent\n"
            'instruction="x"\n'
            "tools=[]\n"
            "root_agent = Agent(name='root', instruction=instruction, tools=tools)\n",
            encoding="utf-8",
        )

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr("cli.agent_cli.shutil.which", fake_which)
    monkeypatch.setattr("cli.agent_cli.subprocess.run", fake_run)
    return calls


def test_init_agent_cli_missing_binary(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("cli.agent_cli.shutil.which", lambda *_a, **_k: None)
    dest = tmp_path / "gsse-app"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "gsse-app",
            "--output",
            str(dest),
            "--domain",
            "retail",
            "--workflow",
            "gsse",
            "--yes",
        ],
    )
    assert result.exit_code != 0
    assert "uv tool install google-agents-cli" in result.output
    assert not dest.exists()


def test_init_agent_cli_gsse_overlays_sdk_classes(tmp_path: Path, monkeypatch):
    calls = _fake_agents_cli_create(monkeypatch)
    dest = tmp_path / "gsse-app"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "gsse-app",
            "--output",
            str(dest),
            "--domain",
            "retail",
            "--workflow",
            "gsse",
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    assert calls
    assert "--yes" in calls[0]
    env = (dest / ".env").read_text(encoding="utf-8")
    assert "AGENT_CLI_ENABLED=true" in env
    assert "ADK_ENABLED=true" in env
    agent_py = (dest / "agents_cli" / "gsse-app" / "app" / "agent.py").read_text(
        encoding="utf-8"
    )
    assert "# --- factory overlay start ---" in agent_py
    assert "IngestCensusAcsDag" in agent_py
    assert "from enterprise_agent_sdk.assets import" in agent_py
    assert "FACTORY_INSTRUCTION" in agent_py
    assert (dest / "agents_cli" / "gsse-app" / "assets_config.yaml").exists()
    assert (dest / "agents_cli" / "gsse-app" / "README.md").exists()
    assert "Wrote agents_cli/gsse-app/" in result.output
    assert not (dest / "factories").exists()
    assert not (dest / "app").exists()
    assert not (dest / "pyproject.toml").exists()
    assert not (dest / "config" / "app.yaml").exists()
    assert "ASSETS_CENSUS_STATE_FIPS" not in env
    assert "LOOKER_ENABLED" not in env
    assert (dest / "domains" / "retail" / "workflows" / "gsse" / "graph.yaml").exists()
    readme = (dest / "README.md").read_text(encoding="utf-8")
    assert "agents_cli/gsse-app/" in readme
    assert "make dev" not in readme


def test_init_agent_cli_dispute_handler_no_sdk_classes(tmp_path: Path, monkeypatch):
    _fake_agents_cli_create(monkeypatch)
    dest = tmp_path / "dispute-cli"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "dispute-cli",
            "--output",
            str(dest),
            "--domain",
            "retail",
            "--workflow",
            "dispute_handler",
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    env = (dest / ".env").read_text(encoding="utf-8")
    assert "AGENT_CLI_ENABLED=true" in env
    assert "ADK_ENABLED=true" in env
    agent_py = (dest / "agents_cli" / "dispute-cli" / "app" / "agent.py").read_text(
        encoding="utf-8"
    )
    assert "# --- factory overlay start ---" in agent_py
    assert "CrmCustomerLookup" not in agent_py
    assert "AnySQLSafeExecutor" not in agent_py
    assert "enterprise_agent_sdk" not in agent_py
    assert not (dest / "factories").exists()
    assert not (dest / "config" / "app.yaml").exists()
    assert "CACHE_BACKEND" not in env
    assert "ASSETS_CENSUS" not in env


def test_init_dry_run_agent_cli_no_subprocess(tmp_path: Path, monkeypatch):
    def boom(*_a, **_k):
        raise AssertionError("subprocess.run must not run on --dry-run")

    monkeypatch.setattr("cli.agent_cli.subprocess.run", boom)
    dest = tmp_path / "gsse-dry"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "gsse-dry",
            "--output",
            str(dest),
            "--domain",
            "retail",
            "--workflow",
            "gsse",
            "--yes",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "agents_cli_args" in result.output
    assert "IngestCensusAcsDag" in result.output
    assert "factories/" not in result.output
    assert "config/app.yaml" not in result.output
    assert not dest.exists()


def test_init_unknown_framework(tmp_path: Path):
    dest = tmp_path / "bad-fw"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "bad-fw",
            "--output",
            str(dest),
            "--domain",
            "retail",
            "--workflow",
            "gsse",
            "--framework",
            "langchain",
            "--yes",
        ],
    )
    assert result.exit_code != 0
    clean_output = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", result.output)
    assert "Unknown --framework" in clean_output

