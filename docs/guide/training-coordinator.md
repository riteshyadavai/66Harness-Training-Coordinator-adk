# Training Coordinator Agent

Organization workflow `training-coordinator-agent` (aliases: `training-coordinator`,
`hr-onboarding-agent`, `hr-onboarding`, `whats-due`).

```bash
66harness init \
  --name training-coordinator \
  --domain org \
  --workflow training-coordinator-agent \
  --ingest-source sharepoint \
  --framework none \
  --yes
```

Use `--ingest-source workday` to grant the ingest agent
`workday_new_hire_lookup` instead. SharePoint is the default. Both
provider-neutral contracts remain in `tools/toolspec.json`, but the ingest
agent receives only the selected tool.

Optional Camping World MCP (not copied into the template — install the SDK extra):

```bash
66harness list-mcp
66harness init --name training-coordinator --domain org \
  --workflow training-coordinator-agent --ingest-source sharepoint \
  --mcp outlook,sharepoint --framework none --yes
```

## Graph

`ingest → eligibility → reconcile → draft → review (HITL) → recommend`

- Ingest reads either a Workday API or a Workday Excel export on SharePoint.
- Eligibility and status calculations run in deterministic Python, never in the LLM.
- Live M365 calendar events are committed intent; `trainings.md` is the baseline.
- Outlook and Teams tools create drafts with `requireConfirmation: true`.
- The scaffold has no send/execute tools.
- SharePoint tracking workbooks are read-only; the workflow recommends exact edits.

## Generated workflow artifacts

| Path | Purpose |
|---|---|
| `tools/toolspec.json` | Provider-neutral Workday, SharePoint, Outlook, and Teams tool contracts |
| `logic_tools.py` | Deterministic eligibility starter implementation |
| `governance.md` | Approved rule placeholders and exception authority |
| `trainings.md` | Tentative curriculum and facilitator baseline |
| `policies/opa/data.json` | Tenure windows, drafts-only, HITL defaults |
| `policies/opa/eligibility.rego` | Auto-enroll vs ineligible vs HITL |
| `policies/opa/actions.rego` | No send; drafts need confirmation; no tracker write |

Catalog evals (`capability`, ingest, eligibility, OPA HITL, reconcile, drafts,
review, tracker, `whats_due_scan`) land in
`evals/training-coordinator-agent/app.evalset.json` and `config/app.yaml`.
This starter set is not exhaustive. Add or drop cases in the catalog `evals:`
list (or the generated evalset) as HR, OPA, or connector requirements change.

Live provider connectors, recurring scheduling, Model Armor, Gemini Enterprise
registration, and custom MCP exposure are post-scaffold design work.
