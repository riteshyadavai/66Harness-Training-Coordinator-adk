# training-coordinator

Organization and Human Resources / **Training Coordinator Agent** (`org/training-coordinator-agent`).

Coordinate new-hire training from Workday or SharePoint ingest through deterministic eligibility, calendar reconciliation, draft communications, human approval, and read-only tracker recommendations.


## Run

```bash
uv sync
make dev
```

API docs: http://localhost:8000/api/v1/docs

## ADK mock demo (Dev UI)

Fixture-backed tools only — no live Workday, SharePoint, or mailbox.

1. Copy `.env.example` to `.env` and set `OPENROUTER_API_KEY` plus `ADK_ENABLED=true`. Gemini (`GOOGLE_API_KEY`) stays commented.
2. From the repo root:

```bash
uv sync
uv run adk web adk_agents
```

3. Open the URL printed in the terminal (usually http://127.0.0.1:8000).
4. Select **training_coordinator**.
5. Use the queries in **Testing** below.
6. Confirm ingest → eligibility → reconcile → drafts → review.
7. Reply `approve` or `reject`. Tracker runs only after approve.

## Testing (ADK)

Restart `uv run adk web adk_agents --port 8080`, pick **training_coordinator**.

| # | What you are testing | Query |
|---|---|---|
| 1 | Full weekly packet | What's due for GM and OEM Parts the week of 2026-09-21? Use mock tools only. Do not invent employees. Follow governance.md. |
| 2 | Ingest, no enroll | Read new GM and OEM Parts hires from /HR/WorkdayExports. Use sharepoint_workday_export_reader only. Flag each as awaiting inclusion. Do not enroll. |
| 3 | OEM mid-cycle hold | OEM Parts participant E-088 started 2026-07-01 and asked to join mid-cycle as of 2026-09-17. Use compute_eligibility with cohort_open false. Expect hold_next_cycle. Escalate to P1. Do not enroll. |
| 4 | OEM over 6 months | Evaluate OEM hire E-001 started 2025-01-01 as of 2026-09-17. Use compute_eligibility. Expect ineligible above_maximum_tenure. |
| 5 | Calendar wins | trainings.md lists P20 Jesse Jensen for GM-5 (DMS & Financial Management). Reconcile with the live invite. Calendar wins. Do not invent availability. |
| 6 | No invented FOD class | Is there a FOD session the week of 2026-09-21? If trainings.md has none, say so. Do not invent a session. |
| 7 | Drafts only | Draft the OEM-5 Parts Financials reminder and invite for 2026-09-22 2:30 PM CST. Use approved-template tone. Do not send. |
| 8 | Inclusion HITL | New GM E-204 appeared on the hire export. Event-based trigger. Hold for P14 Karen Lorden. Write an ESCALATION NOTICE. Do not add them to the tracker. |
| 9 | Tracker recommend | E-100 completed OEM session 2. Recommend the exact tracker cell. Do not write SharePoint. |
| 10 | Approve path | After query 1, when review stops, reply: approve |

Expect: Spencer Toomey on the GM-5 calendar (not P20); no FOD class that week; drafts `pending_confirmation`; nothing sent.

## Stack

LLM litellm  ·  cache memory  ·  vector memory

Runtime knobs: `config/app.yaml` (env vars override). Plan: `accepted`.

Skills: org-training-coordinator

Tools: sharepoint_workday_export_reader, workday_new_hire_lookup, lookup_governance_rules, sharepoint_roster_reader, compute_eligibility, compute_status, lookup_trainings_plan, find_session_invite, resolve_session_stakeholders, check_facilitator_availability, whats_due_all, draft_session_invite, reschedule_session_invite, cancel_session_invite, reassign_facilitator, draft_email, draft_teams_message, poll_facilitator_availability, recommend_tracker_edit

## Environment

Set these in `.env`:

- `OPENROUTER_API_KEY` (Gemini `GOOGLE_API_KEY` is optional / commented)

## Evals

```bash
uv run pytest evals/
```

Cases for this workflow live in `evals/training-coordinator-agent/` and `evals:` in `config/app.yaml`.
