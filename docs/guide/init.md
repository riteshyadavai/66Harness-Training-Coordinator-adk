# Init a project

One output directory = **one domain + one workflow**. `bfs/afi` and `bfs/clu` are two `init` runs. The wizard reads the [merged catalog](catalog.md) (`catalogs/domains/*.yaml` + `factories.yaml`).

Interactive `init` shows a **predefined plan** (agents + graph). Accept it, or customize agents/HITL and then configure backends. Choose **other** to name your own domain and workflow slugs, then pick the same stack.

!!! note "Write set"
    `.env` (secrets), `config/app.yaml` (runtime knobs), `factory-choices.json`, `pyproject.toml` name, `domains/<domain>/workflows/<workflow>/`.

!!! danger "Destructive `--force`"
    `--force` **deletes** a non-empty destination, then recopies. `--dry-run` writes nothing.

## Interactive

From an **empty folder** you already created, init writes **here** (project name = folder name):

```bash
mkdir ~/Desktop/demo-afi && cd ~/Desktop/demo-afi
66harness init
```

From this factory repo, init refuses `.` and defaults to `~/Desktop/<name>`:

```bash
uv run 66harness init
```

Or pass `--output` explicitly. Do **not** use this template repo as the destination.

Each workflow has a catalog **platform stack** (LLM / cache / vector). Accept the plan to keep it, or choose **Change stack**. After Accept or Customize, the wizard still asks optional factories: Enterprise Asset Factory, Google ADK, **Enable gemini-enterprise**, Looker, BQML. The plan card lists recommended extras and notes that gemini-enterprise is opt-in.

Retail **gsse** (Geospatial Site Suitability Engine) is a six-node graph. `--yes` defaults assets + ADK on. See [GSSE](gsse.md).

Retail **dispute_handler** (Autonomous Dispute Processor) is triage → audit → review (HITL) → settle. `init` writes `policies/opa/`. See [Dispute handler](dispute-handler.md).

Org **training-coordinator-agent** (Training Coordinator Agent) selects SharePoint
Workday-export ingest by default. Pass `--ingest-source workday` for the
provider-neutral Workday API contract. It generates deterministic rule,
governance, curriculum, and tool-spec artifacts. See
[Training coordinator](training-coordinator.md).

## What gets written

Runtime app snapshot (`app/`, `agents/`, `factories/`, `tests/`, `docs/`). **Not copied:** `catalogs/`, `cli/`.

| Path | Purpose |
|------|---------|
| `.env` | Secrets (`CHANGE_ME`) |
| `config/app.yaml` | Chosen workflow snapshot (agents, prompts, MCP, evals) plus backends |
| `factory-choices.json` | Replay (`--from-choices`) |
| `domains/<domain>/workflows/<workflow>/` | Manifests, prompts, `graph.yaml`, **README.md**, optional `policies/opa/` |
| `…/gemini_enterprise/` | Only with `--gemini-enterprise` (gsse): `agent.yaml`, `actions/confirm_site.json` |
| `agents_cli/<slug>/` | Default `--framework agent-cli`: Google `agents-cli create` output plus catalog overlay. Omit with `--framework none` |

`--yes` accepts the catalog plan and `recommended_stack` unless you pass factory flags. Looker and BQML stay off unless you pass `--looker` / `--bqml`. Retail `gsse` turns assets and ADK on unless you pass `--no-assets` / `--no-adk`. `--gemini-enterprise` is opt-in. `--framework` defaults to `agent-cli` (requires `agents-cli` on PATH; forces ADK).

Every workflow gets `domains/<domain>/workflows/<workflow>/README.md`.

Asset Factory does **not** copy GitHub into the project. After assets are on, run `uv sync --extra asset-factory` (needs access to `66degrees/agentic-asset-factory` branch `ra-gradient-tools` for District Dine). Then set the `ASSETS_*` keys you use. `--assets` on a generic workflow hydrates the **core** pack (SQL, OpenAPI, HITL, PII, crawler, vector_sync). `gsse --yes` sets `ASSETS_PACK=district_dine` (the twelve dry-run scaffolds only). Override with `--asset-pack all`. Live Looker/BQML still need `--looker` / `--bqml`. Smoke: `uv run python examples/assets_smoke.py` (core) or `examples/gsse_smoke.py` (District Dine).

`Platform` loads that workflow when `config/app.yaml` has `project.domain` and `project.workflow`. This checkout without a project block uses the default `respond` graph.

## After generate

```bash
cd ~/Desktop/demo-afi && uv sync && make dev
```
