# Geospatial Site Suitability Engine

Retail workflow `gsse`. Same FastAPI template as every other domain. Gemini Enterprise is the **target** front door, not something this CLI deploys.

```bash
66harness init --name district-dine --domain retail --workflow gsse --yes
cd ~/Desktop/district-dine
uv sync --extra asset-factory
uv run python examples/gsse_smoke.py
```

`--yes` turns **assets** and **ADK** on and sets `ASSETS_PACK=district_dine` (the twelve District Dine tools only — not the generic SQL / OpenAPI / HITL / PII / crawler / vector_sync pack). Pass `--no-assets` / `--no-adk` to keep them off. Override with `--asset-pack all` if you need both packs.

Opt-in workspace pack:

```bash
66harness init --name district-dine --domain retail --workflow gsse --gemini-enterprise --yes
```

That writes `domains/retail/workflows/gsse/gemini_enterprise/` (`agent.yaml`, `actions/confirm_site.json`, README). Register the spec yourself. FastAPI stays for local use.

## What this CLI generates vs GCP

| This repo | Still yours on GCP |
|---|---|
| Catalog graph ingest → gold → score → analyze → explain → confirm (HITL) | Daily Census / OSM / transit jobs |
| Asset Factory dry-run tools | Live Looker connection (`--looker`) |
| Local ADK tools when ADK is on | Agent Gallery publish |
| Confirm Site HITL + `sites_catalog` scaffold | Real Gold MERGE / Gemini forms |
| Workflow `README.md` + optional gemini-enterprise folder | Workspace IdP / RBAC |

## Asset taxonomy

| Category | Tools |
|---|---|
| Data pipelines | `census`, `osm`, `transit` |
| Data storage | `gold_features`, `sites_catalog` |
| Semantic layer | `suitability_model` |
| Machine learning | `bqml_train`, `bqml_infer` |
| Agent / ADK | `nav`, `grounded_analytics`, `reasoning` |

## Agents

| Node | Agent | Tools |
|------|--------|--------|
| ingest | `gsse_ingest` | `vector_search`, `census`, `osm`, `transit` |
| gold | `gsse_gold` | `gold_features` |
| score | `gsse_scorer` | `bqml_train`, `bqml_infer`, `suitability_model` |
| analyze | `gsse_analyst` | `grounded_analytics`, `nav` |
| explain | `gsse_explainer` | `reasoning` |
| confirm | `gsse_confirm` (HITL) | `sites_catalog` |

Call tools from Python with `factories.assets.tools.run_asset_tool("census", run_id="…")` when `ASSETS_ENABLED=true` and `ASSETS_PACK=district_dine`.

## Wizard

Interactive `init` lists `gsse — Geospatial Site Suitability Engine`. After you accept the plan it asks **Enable Enterprise Asset Factory (District Dine pack)** (default yes), **Enable Google ADK** (default yes), **Enable gemini-enterprise** (default no), then Looker / BQML.

## Target topology (Gemini Enterprise)

External public data → Bronze/Gold BigQuery → BQML and LookML → ADK tools (`nav`, `grounded_analytics`, `reasoning`) → Gemini Enterprise workspace → Confirm Site → `sites_catalog`.

This CLI does not replace FastAPI with that workspace and does not register the agent in the Gallery.
