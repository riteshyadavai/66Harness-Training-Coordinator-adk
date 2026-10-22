"""Fixture-backed TCA tools for the local ADK demo. Never writes SharePoint."""

from __future__ import annotations

import importlib.util
import json
import uuid
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

WORKFLOW_DIR = Path(__file__).resolve().parents[1]


def _load_logic_tools():
    path = WORKFLOW_DIR / "logic_tools.py"
    spec = importlib.util.spec_from_file_location("tca_logic_tools", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_logic = _load_logic_tools()
_compute_eligibility = _logic.compute_eligibility
FIXTURES = WORKFLOW_DIR / "fixtures"
OPA_DATA = WORKFLOW_DIR / "policies" / "opa" / "data.json"

_DRAFTS: list[dict[str, Any]] = []
_RECOMMENDATIONS: list[dict[str, Any]] = []

_PROGRAM_ALIASES = {
    "OEM Parts": "OEM_Parts",
    "OEM_Parts": "OEM_Parts",
    "oem_parts": "OEM_Parts",
    "oem-parts": "OEM_Parts",
    "OEM-Parts": "OEM_Parts",
    "oem parts": "OEM_Parts",
    "GM": "GM",
    "FOD": "FOD",
}


def reset_demo_state() -> None:
    _DRAFTS.clear()
    _RECOMMENDATIONS.clear()


def _parse_date(value: str) -> date:
    return date.fromisoformat(value[:10])


def _normalize_program(program: str | None) -> str | None:
    if program is None:
        return None
    return _PROGRAM_ALIASES.get(program, program)


@lru_cache(maxsize=1)
def _export() -> dict[str, Any]:
    return json.loads((FIXTURES / "workday_export.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _roster() -> dict[str, Any]:
    return json.loads((FIXTURES / "roster.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _calendar() -> dict[str, Any]:
    return json.loads((FIXTURES / "calendar.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _aliases() -> dict[str, Any]:
    return json.loads((FIXTURES / "aliases.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _opa() -> dict[str, Any]:
    return json.loads(OPA_DATA.read_text(encoding="utf-8"))


def _employees() -> list[dict[str, Any]]:
    return list(_export()["employees"])


def _program_config(program: str) -> dict[str, Any]:
    key = _normalize_program(program) or program
    programs = _opa()["training"]["programs"]
    if key not in programs:
        raise ValueError(f"Unknown program: {program}")
    return programs[key]


def sharepoint_workday_export_reader(
    folder_path: str,
    file_name: str | None = None,
    job_profiles: list[str] | None = None,
    as_of_date: str | None = None,
) -> dict[str, Any]:
    """Read new-hire rows from a Workday Excel export in SharePoint. Read-only mock."""
    profiles = {_normalize_program(p) or p for p in (job_profiles or [])}
    rows = []
    for emp in _employees():
        program = emp["program"]
        if profiles and program not in profiles and emp["job_profile"] not in (job_profiles or []):
            continue
        export_name = file_name or _export()["file_name"]
        rows.append({**emp, "folder_path": folder_path, "file_name": export_name})
    return {
        "source": "sharepoint_workday_export_reader",
        "folder_path": folder_path,
        "file_name": file_name or _export()["file_name"],
        "as_of_date": as_of_date or _export()["as_of_date"],
        "employees": rows,
        "read_only": True,
    }


def workday_new_hire_lookup(
    start_date_from: str,
    start_date_to: str,
    job_profiles: list[str] | None = None,
) -> dict[str, Any]:
    """Query Workday for new workers by start-date window. Read-only mock."""
    start = _parse_date(start_date_from)
    end = _parse_date(start_date_to)
    profiles = {_normalize_program(p) or p for p in (job_profiles or [])}
    rows = []
    for emp in _employees():
        hired = _parse_date(emp["start_date"])
        if hired < start or hired > end:
            continue
        profile_hit = emp["job_profile"] in (job_profiles or [])
        if profiles and emp["program"] not in profiles and not profile_hit:
            continue
        rows.append(emp)
    return {
        "source": "workday_new_hire_lookup",
        "start_date_from": start_date_from,
        "start_date_to": start_date_to,
        "employees": rows,
        "read_only": True,
    }


def sharepoint_roster_reader(
    file_path: str,
    tab: str | None = None,
    program: str | None = None,
    employee_id: str | None = None,
) -> dict[str, Any]:
    """Read participant state from a SharePoint Excel tracker. Never writes."""
    roster = _roster()
    tabs = roster["tabs"]
    wanted_tab = _normalize_program(tab) or _normalize_program(program)
    rows: list[dict[str, Any]] = []
    for tab_name, items in tabs.items():
        if wanted_tab and tab_name != wanted_tab:
            continue
        for item in items:
            if employee_id and item["employee_id"] != employee_id:
                continue
            rows.append({**item, "tab": tab_name, "file_path": file_path or roster["file_path"]})
    # Tab alias miss (e.g. "OEM Parts") — search all tabs by employee_id.
    if not rows and employee_id:
        for tab_name, items in tabs.items():
            for item in items:
                if item["employee_id"] == employee_id:
                    path = file_path or roster["file_path"]
                    rows.append({**item, "tab": tab_name, "file_path": path})
    known_ids = [item["employee_id"] for items in tabs.values() for item in items]
    return {
        "file_path": file_path or roster["file_path"],
        "tab_requested": tab,
        "tab_resolved": wanted_tab,
        "available_tabs": list(tabs.keys()),
        "known_employee_ids": known_ids,
        "columns": roster["columns"],
        "allowed_status_values": [
            "pending_eligibility",
            "active",
            "hold_next_cycle",
            "ineligible",
        ],
        "rows": rows,
        "wrote": False,
    }


def lookup_trainings_plan(
    program: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Read tentative curriculum from trainings.md."""
    text = (WORKFLOW_DIR / "trainings.md").read_text(encoding="utf-8")
    sessions = [
        {
            "program": "GM",
            "session_id": "GM-5",
            "topic": "DMS & Financial Management",
            "dates": "2026-09-22 and 2026-09-24",
            "time": "11:00 AM–12:00 PM CST",
            "facilitator_ids": ["P20"],
            "backup_ids": [],
            "tentative": True,
        },
        {
            "program": "FOD",
            "session_id": "FOD-NONE-2026-09-21",
            "topic": None,
            "dates": "week of 2026-09-21",
            "time": "1:00–2:00 PM CST",
            "facilitator_ids": [],
            "note": "No FOD session published for this week. Do not invent one.",
            "tentative": True,
        },
        {
            "program": "OEM_Parts",
            "session_id": "OEM-5",
            "topic": "OEM Parts Financials",
            "dates": "2026-09-22 and 2026-09-24",
            "time": "2:30–3:30 PM CST",
            "facilitator_ids": ["P8", "P30", "P31"],
            "tentative": True,
        },
    ]
    key = _normalize_program(program)
    filtered = [
        s
        for s in sessions
        if (key is None or s["program"] == key)
        and (session_id is None or s["session_id"] == session_id)
    ]
    return {
        "baseline": "trainings.md",
        "calendar_wins": True,
        "sessions": filtered,
        "people_directory_excerpt": "IDs only; resolve names from trainings.md People Directory",
        "source_text_excerpt": text[:800],
    }


def lookup_governance_rules(
    program: str | None = None,
    rule_id: str | None = None,
) -> dict[str, Any]:
    """Read inclusion, exclusion, hold, and override rules. No tenure math."""
    text = (WORKFLOW_DIR / "governance.md").read_text(encoding="utf-8")
    rules = [
        {
            "rule_id": "EVENT-HITL",
            "program": None,
            "text": "New hire from Workday export is event-based; hold for inclusion POC",
        },
        {
            "rule_id": "GM-INCLUSION",
            "program": "GM",
            "text": "GM inclusion POC is P14 Karen Lorden. Rolling 6-session cycle.",
        },
        {
            "rule_id": "FOD-INCLUSION",
            "program": "FOD",
            "text": "FOD inclusion POC is P7 Russ Hunt. Hired 2025-01-01+.",
        },
        {
            "rule_id": "OEM-HOLD",
            "program": "OEM_Parts",
            "text": "OEM Parts: last 6 months; no mid-cycle join. POC P1.",
        },
        {
            "rule_id": "DRAFTS-ONLY",
            "program": None,
            "text": "Use approved templates. This scaffold drafts only; never send.",
        },
        {
            "rule_id": "ESCALATE",
            "program": None,
            "text": "Escalate unclear inclusion or wrong-recipient risk to P1",
        },
    ]
    key = _normalize_program(program)
    filtered = [
        r
        for r in rules
        if (rule_id is None or r["rule_id"] == rule_id)
        and (key is None or r["program"] in (None, key))
    ]
    return {"rules": filtered, "source_text_excerpt": text[:500], "computed_tenure": False}


def compute_eligibility(
    employee_id: str,
    job_profile: str,
    start_date: str,
    as_of_date: str,
    program: str,
    cohort_open: bool = True,
) -> dict[str, Any]:
    """Deterministically calculate tenure. Do not let the model do date math."""
    cfg = _program_config(program)
    result = _compute_eligibility(
        start_date=_parse_date(start_date),
        as_of_date=_parse_date(as_of_date),
        minimum_tenure_days=int(cfg["min_tenure_days"]),
        maximum_tenure_days=int(cfg["max_tenure_days"]),
        cohort_open=cohort_open,
        hold_when_cohort_closed=bool(cfg["hold_when_cohort_closed"]),
    )
    return {
        "employee_id": employee_id,
        "job_profile": job_profile,
        "program": _normalize_program(program),
        **result,
    }


def compute_status(
    program: str,
    as_of_date: str,
    employee_id: str | None = None,
) -> dict[str, Any]:
    """Flag stalled participants and completion-window age-outs."""
    as_of = _parse_date(as_of_date)
    key = _normalize_program(program) or program
    flags: list[dict[str, Any]] = []
    for item in _roster()["tabs"].get(key, []):
        if employee_id and item["employee_id"] != employee_id:
            continue
        last = _parse_date(item["last_activity"]) if item.get("last_activity") else None
        stalled = last is not None and (as_of - last).days > 21
        flags.append(
            {
                "employee_id": item["employee_id"],
                "stalled": stalled,
                "days_since_activity": (as_of - last).days if last else None,
                "sessions_completed": item["sessions_completed"],
                "status": "stalled" if stalled else item["status"],
            }
        )
    return {"program": key, "as_of_date": as_of_date, "flags": flags}


def whats_due_all(week_start: str, programs: list[str] | None = None) -> dict[str, Any]:
    """Scan rosters for upcoming sessions, communications, and overdue milestones."""
    wanted = {_normalize_program(p) or p for p in (programs or [])}
    due: list[dict[str, Any]] = []
    for invite in _calendar()["invites"]:
        if wanted and invite["program"] not in wanted:
            continue
        due.append(
            {
                "kind": "session",
                "session_id": invite["session_id"],
                "start": invite["start"],
                "program": invite["program"],
                "action": "prepare_reminder_and_confirm_invite",
            }
        )
    for tab, items in _roster()["tabs"].items():
        if wanted and tab not in wanted:
            continue
        for item in items:
            if item.get("notes"):
                due.append(
                    {
                        "kind": "communication",
                        "employee_id": item["employee_id"],
                        "program": tab,
                        "action": item["notes"],
                    }
                )
            if item["status"] == "hold_next_cycle":
                due.append(
                    {
                        "kind": "overdue_or_hold",
                        "employee_id": item["employee_id"],
                        "program": tab,
                        "action": "do_not_enroll; HITL if exception requested",
                    }
                )
    return {"week_start": week_start, "items": due, "sent": False}


def find_session_invite(
    session_id: str | None = None,
    topic: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    organizer: str | None = None,
) -> dict[str, Any]:
    """Find committed M365 calendar events. Read-only mock."""
    matches = []
    for invite in _calendar()["invites"]:
        if session_id and invite["session_id"] != session_id:
            continue
        if topic and topic.lower() not in invite["topic"].lower():
            continue
        if organizer and invite["organizer"] != organizer:
            continue
        start = datetime.fromisoformat(invite["start"])
        if date_from and start < datetime.fromisoformat(date_from):
            continue
        if date_to and start > datetime.fromisoformat(date_to):
            continue
        matches.append(invite)
    return {"invites": matches, "committed_intent": True}


def resolve_session_stakeholders(session_id: str, program: str | None = None) -> dict[str, Any]:
    """Resolve facilitators, co-hosts, and participants from schedules and aliases."""
    aliases = _aliases()
    invite = next((i for i in _calendar()["invites"] if i["session_id"] == session_id), None)
    plan = lookup_trainings_plan(program=program, session_id=session_id)
    baseline = plan["sessions"][0] if plan["sessions"] else {}
    return {
        "session_id": session_id,
        "calendar_facilitators": invite["facilitators"] if invite else [],
        "baseline_facilitator_ids": baseline.get("facilitator_ids"),
        "baseline_facilitator_emails": [
            aliases["aliases"].get(pid) for pid in baseline.get("facilitator_ids") or []
        ],
        "co_hosts": aliases["co_hosts"].get(session_id, []),
        "attendees": invite["attendees"] if invite else [],
        "calendar_wins": True,
        "note": "A live calendar event is committed intent over trainings.md.",
    }


def check_facilitator_availability(
    facilitator_email: str,
    start: str,
    end: str,
) -> dict[str, Any]:
    """Read facilitator calendar free/busy. Does not send a poll."""
    busy = []
    for invite in _calendar()["invites"]:
        if facilitator_email in invite["facilitators"]:
            busy.append(
                {
                    "start": invite["start"],
                    "end": invite["end"],
                    "session_id": invite["session_id"],
                }
            )
    requested = datetime.fromisoformat(start)
    conflict = any(
        datetime.fromisoformat(b["start"]) < datetime.fromisoformat(end)
        and datetime.fromisoformat(b["end"]) > requested
        for b in busy
    )
    return {
        "facilitator_email": facilitator_email,
        "start": start,
        "end": end,
        "busy": busy,
        "free": not conflict,
        "poll_sent": False,
    }


def _draft(kind: str, preview: dict[str, Any]) -> dict[str, Any]:
    packet = {
        "draft_id": f"DFT-{uuid.uuid4().hex[:8]}",
        "kind": kind,
        "status": "pending_confirmation",
        "preview": preview,
        "sent": False,
        "executed": False,
    }
    _DRAFTS.append(packet)
    return packet


def draft_session_invite(
    subject: str,
    start: str,
    end: str,
    attendees: list[str],
    facilitators: list[str] | None = None,
    body: str | None = None,
    pre_read_links: list[str] | None = None,
) -> dict[str, Any]:
    """Prepare an Outlook session invite draft; never sends."""
    return _draft(
        "session_invite",
        {
            "subject": subject,
            "start": start,
            "end": end,
            "attendees": attendees,
            "facilitators": facilitators or [],
            "body": body or "",
            "pre_read_links": pre_read_links or [],
        },
    )


def reschedule_session_invite(
    invite_id: str,
    new_start: str,
    new_end: str,
    reason: str,
) -> dict[str, Any]:
    """Prepare a reschedule draft for an existing invite."""
    return _draft(
        "reschedule",
        {"invite_id": invite_id, "new_start": new_start, "new_end": new_end, "reason": reason},
    )


def cancel_session_invite(invite_id: str, reason: str) -> dict[str, Any]:
    """Prepare a cancellation draft. Does not cancel the live event."""
    return _draft("cancel", {"invite_id": invite_id, "reason": reason})


def reassign_facilitator(
    invite_id: str,
    from_email: str,
    to_email: str,
    topic: str | None = None,
) -> dict[str, Any]:
    """Prepare a facilitator or topic reassignment draft."""
    return _draft(
        "reassign_facilitator",
        {"invite_id": invite_id, "from_email": from_email, "to_email": to_email, "topic": topic},
    )


def draft_email(to: list[str], subject: str, body: str, purpose: str) -> dict[str, Any]:
    """Prepare an Outlook reminder, pre-read, or follow-up email draft."""
    return _draft("email", {"to": to, "subject": subject, "body": body, "purpose": purpose})


def draft_teams_message(channel_or_user: str, body: str) -> dict[str, Any]:
    """Prepare a Microsoft Teams message draft."""
    return _draft("teams", {"channel_or_user": channel_or_user, "body": body})


def poll_facilitator_availability(
    facilitator_emails: list[str],
    candidate_slots: list[str],
) -> dict[str, Any]:
    """Prepare an asynchronous facilitator availability poll draft."""
    return _draft(
        "availability_poll",
        {"facilitator_emails": facilitator_emails, "candidate_slots": candidate_slots},
    )


def recommend_tracker_edit(
    file_path: str,
    tab: str,
    row: int,
    column: str,
    value: Any,
    reason: str,
    employee_id: str | None = None,
) -> dict[str, Any]:
    """Recommend an exact Excel cell change. Never writes SharePoint."""
    rec = {
        "file_path": file_path,
        "tab": tab,
        "row": row,
        "column": column,
        "value": value,
        "employee_id": employee_id,
        "reason": reason,
        "applied": False,
        "wrote_sharepoint": False,
    }
    _RECOMMENDATIONS.append(rec)
    return rec


def list_drafts() -> list[dict[str, Any]]:
    return list(_DRAFTS)


def list_recommendations() -> list[dict[str, Any]]:
    return list(_RECOMMENDATIONS)


HANDLERS: dict[str, Any] = {
    "sharepoint_workday_export_reader": sharepoint_workday_export_reader,
    "workday_new_hire_lookup": workday_new_hire_lookup,
    "sharepoint_roster_reader": sharepoint_roster_reader,
    "lookup_trainings_plan": lookup_trainings_plan,
    "lookup_governance_rules": lookup_governance_rules,
    "compute_eligibility": compute_eligibility,
    "compute_status": compute_status,
    "whats_due_all": whats_due_all,
    "find_session_invite": find_session_invite,
    "resolve_session_stakeholders": resolve_session_stakeholders,
    "check_facilitator_availability": check_facilitator_availability,
    "draft_session_invite": draft_session_invite,
    "reschedule_session_invite": reschedule_session_invite,
    "cancel_session_invite": cancel_session_invite,
    "reassign_facilitator": reassign_facilitator,
    "draft_email": draft_email,
    "draft_teams_message": draft_teams_message,
    "poll_facilitator_availability": poll_facilitator_availability,
    "recommend_tracker_edit": recommend_tracker_edit,
}
