"""Mock TCA tools and ADK graph construction."""

from __future__ import annotations

from factories.adk.tca_graph import AGENT_TOOLS, PIPELINE, _decision, build_root_agent
from factories.adk.tca_tools import load_mock_runtime


def test_compute_eligibility_below_tenure():
    runtime = load_mock_runtime()
    runtime.reset_demo_state()
    result = runtime.compute_eligibility(
        employee_id="E-204",
        job_profile="GM",
        start_date="2026-09-10",
        as_of_date="2026-09-17",
        program="GM",
    )
    assert result["status"] == "ineligible"
    assert result["tenure_days"] == 7
    assert result["reason"] == "below_minimum_tenure"


def test_compute_eligibility_in_window():
    runtime = load_mock_runtime()
    result = runtime.compute_eligibility(
        employee_id="E-100",
        job_profile="OEM Parts",
        start_date="2026-08-10",
        as_of_date="2026-09-17",
        program="OEM_Parts",
        cohort_open=True,
    )
    assert result["status"] == "eligible"
    assert result["tenure_days"] == 38


def test_compute_eligibility_hold_when_cohort_closed():
    runtime = load_mock_runtime()
    result = runtime.compute_eligibility(
        employee_id="E-088",
        job_profile="OEM Parts",
        start_date="2026-07-01",
        as_of_date="2026-09-17",
        program="OEM_Parts",
        cohort_open=False,
    )
    assert result["status"] == "hold_next_cycle"
    assert result["reason"] == "cohort_closed"


def test_drafts_are_pending_confirmation_never_sent():
    runtime = load_mock_runtime()
    runtime.reset_demo_state()
    draft = runtime.draft_email(
        to=["oem-parts@example.com"],
        subject="OEM-2 reminder",
        body="Please complete the pre-read.",
        purpose="reminder",
    )
    assert draft["status"] == "pending_confirmation"
    assert draft["sent"] is False
    assert draft["executed"] is False
    assert runtime.list_drafts()[0]["draft_id"] == draft["draft_id"]


def test_recommend_tracker_edit_does_not_write():
    runtime = load_mock_runtime()
    runtime.reset_demo_state()
    rec = runtime.recommend_tracker_edit(
        file_path="/HR/Trackers/training_roster.xlsx",
        tab="OEM_Parts",
        row=5,
        column="D",
        value=2,
        reason="E-100 completed session 2",
        employee_id="E-100",
    )
    assert rec["applied"] is False
    assert rec["wrote_sharepoint"] is False
    roster = runtime.sharepoint_roster_reader(
        file_path="/HR/Trackers/training_roster.xlsx",
        program="OEM_Parts",
        employee_id="E-100",
    )
    assert roster["wrote"] is False
    assert roster["rows"][0]["sessions_completed"] == 2


def test_calendar_facilitator_wins_over_baseline():
    runtime = load_mock_runtime()
    stakeholders = runtime.resolve_session_stakeholders("GM-3", program="GM")
    assert stakeholders["calendar_facilitators"] == ["jordan@example.com"]
    assert stakeholders["baseline_facilitator_alias"] == "Alex"
    assert stakeholders["calendar_wins"] is True


def test_adk_root_has_six_sub_agents_and_allowed_tools():
    root = build_root_agent()
    names = [child.name for child in root.sub_agents]
    assert names == [*PIPELINE, "tca_tracker"]
    by_name = {child.name: child for child in root.sub_agents}
    for name, allowed in AGENT_TOOLS.items():
        tool_names = [tool.name for tool in getattr(by_name[name], "tools", [])]
        assert tool_names == allowed


def test_hitl_decision_words():
    assert _decision("Please approve the packet") == "approve"
    assert _decision("reject these drafts") == "reject"
    assert _decision("What's due this week?") is None
