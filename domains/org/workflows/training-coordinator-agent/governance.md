# Training governance

Approved HR policy for the local mock demo. `logic_tools.py` and
`compute_eligibility` must receive these values as configuration;
the model must never infer them.

| Program | Minimum tenure days | Maximum tenure days | Mid-cycle enrollment |
|---|---:|---:|---|
| GM | 30 | 365 | HITL + director approval |
| FOD | 14 | 180 | HITL + director approval |
| OEM Parts | 30 | 90 | Hold for next cycle; HITL + director for exceptions |

HR Leadership or Director approval is required for opt-in, opt-out,
and mid-cycle enrollment exceptions.

Rule IDs:

- `GM-TENURE` — GM 30–365 days
- `FOD-TENURE` — FOD 14–180 days
- `OEM-TENURE` — OEM Parts 30–90 days
- `OEM-HOLD` — hold missed or mid-cycle OEM Parts when the cohort is closed
- `HITL-EXCEPTION` — director approval for opt-in, opt-out, mid-cycle
