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

1. Copy `.env.example` to `.env` and set `GOOGLE_API_KEY` plus `ADK_ENABLED=true`.
2. From the repo root:

```bash
uv sync
uv run adk web adk_agents
```

3. Open the URL printed in the terminal (usually http://127.0.0.1:8000).
4. Select **training_coordinator**.
5. Send: `What's due for OEM Parts and GM the week of 2026-09-21? Use the mock tools. Do not invent employees.`
6. Confirm tool calls through ingest → eligibility → reconcile → drafts → review.
7. When review asks for approval, reply `approve` (or `reject`). Tracker recommendations appear only after approve.

Other prompts to try: eval cases in `config/app.yaml` (`ingest_sharepoint`, `deterministic_eligibility`, `reconcile_calendar_wins`, `draft_only`, `tracker_read_only`).

## Stack

LLM litellm  ·  cache memory  ·  vector memory

Runtime knobs: `config/app.yaml` (env vars override). Plan: `accepted`.

Skills: org-training-coordinator

Tools: sharepoint_workday_export_reader, workday_new_hire_lookup, lookup_governance_rules, sharepoint_roster_reader, compute_eligibility, compute_status, lookup_trainings_plan, find_session_invite, resolve_session_stakeholders, check_facilitator_availability, whats_due_all, draft_session_invite, reschedule_session_invite, cancel_session_invite, reassign_facilitator, draft_email, draft_teams_message, poll_facilitator_availability, recommend_tracker_edit

## Environment

Set these in `.env`:

- `GOOGLE_API_KEY`

## Evals

```bash
uv run pytest evals/
```

Cases for this workflow live in `evals/training-coordinator-agent/` and `evals:` in `config/app.yaml`.
