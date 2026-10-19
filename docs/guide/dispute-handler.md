# Autonomous Dispute Processor

Retail workflow `dispute_handler` (aliases: `disputes`, `returns`, `chargeback`, `accr`, `concierge`). Replaces the old `accr` id. Same FastAPI template as every other domain.

```bash
cd ~
rm -rf ~/Desktop/dispute-demo
66harness init \
  --name dispute-demo \
  --output ~/Desktop/dispute-demo \
  --domain retail \
  --workflow dispute_handler \
  --yes
```

## Graph

`triage → audit → review (HITL) → settle`

| Node | Agent | Tools |
|------|--------|--------|
| triage | `dispute_triage` | `CrmCustomerLookup`, `OrderFulfillmentLookup` |
| audit | `dispute_audit` | `CarrierTrackingLookup`, `OrderFulfillmentLookup` |
| review | `dispute_review` | `RiskPolicyEvaluator` |
| settle | `dispute_settle` | `SettlementExecutor` |

Map those tool names to the client's CRM, OMS, carrier, risk, and payments APIs (or mocks).

## OPA bundle

`init` writes:

```text
domains/retail/workflows/dispute_handler/policies/opa/
  settle.rego
  data.json
```

Default data:

- `max_auto_settle_usd`: 100
- `max_returns_per_month`: 3
- `fraud_score_threshold`: 0.7
- `hitl_required_default`: true

The review node has `requires_hitl: true` in `graph.yaml`. Toggle HITL in the wizard (Edit HITL / tools) or edit the graph after generate. Align `hitl_required_default` in `data.json` with that choice.

This package **does not** run OPA at request time. Wire an OPA-compatible evaluator if you want `allow_auto_settle` enforced in the graph.

## After generate

```bash
cd ~/Desktop/dispute-demo
cat domains/retail/workflows/dispute_handler/README.md
cat domains/retail/workflows/dispute_handler/policies/opa/data.json
# set GOOGLE_API_KEY in .env
uv sync
make dev
```
