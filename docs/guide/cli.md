# CLI command reference

Same Typer app, two names. No subcommand → help (`no_args_is_help`). Domain and factory menus are loaded from [catalog shards](catalog.md), not a single `catalog.yaml`.

```bash
66harness --help
factory --help
```

## Command map

<div class="grid cards" markdown>

-   :material-domain: [`list-domains`](#list-domains)

    Catalog domain ids.

-   :material-sitemap: [`list-workflows`](#list-workflows)

    Workflows for one `--domain`.

-   :material-factory: [`list-factories`](#list-factories)

    Capability backends and status.

-   :material-puzzle: [`list-sdk-tools`](#list-sdk-tools--list-mcp) / [`list-mcp`](#list-sdk-tools--list-mcp)

    SDK categories (District Dine vs Camping World MCP).

-   :material-folder-plus: [`init`](#init)

    Generate one domain + one workflow.

-   :material-play: [`serve`](#serve)

    Uvicorn for `app.main:app`.

</div>


## `list-domains`

Print domains from the merged catalog (`catalogs/domains/*.yaml`).

```bash
66harness list-domains
```

| Domain | Workflows |
|--------|-----------|
| `bfs` | `afi`, `clu`, `rca` |
| `hcls` | `epa`, `ctpm`, `addw` |
| `retail` | `dispute_handler`, `dcap`, `avmts`, `gsse` (Geospatial Site Suitability Engine) |
| `other` | starter `custom` — you name domain + workflow slugs |

---

## `list-workflows`

List workflows for **one** domain.

```bash
66harness list-workflows --domain bfs
```

| Flag | Required | Description |
|------|----------|-------------|
| `--domain` | yes | Catalog domain id or alias (`banking` → `bfs`) |

Prints `workflow_id` and display name. Example for `--domain bfs`: `afi`, `clu`, `rca`. For `--domain retail`: `dispute_handler` (aliases `accr`, `disputes`), `dcap`, `avmts`, `gsse`. For `--domain org`: `training-coordinator-agent`.

---

## `list-factories`

Print capabilities and backends from `catalogs/factories.yaml` (`implemented` / `planned`).

```bash
66harness list-factories
66harness list-factories --capability cache
```

| Flag | Required | Description |
|------|----------|-------------|
| `--capability` | no | Filter: `gateway`, `cache`, `vector`, `embeddings`, `parser`, `guardrails`, `eval`, `state`, `secrets`, `observability`, `adk`, `a2a`, `mcp`, `looker`, `bqml`, `assets` |

---

## `list-sdk-tools` / `list-mcp`

Reads `forge66/catalog.yaml` from private `66degrees/agentic-asset-factory` (default ref `ra-camptools`) via the **GitHub API** or `gh api`. It does not use `raw.githubusercontent.com` (that URL times out on a private repo). Auth: `gh auth login`, or `GITHUB_TOKEN` / `GH_TOKEN`, or `SDK_CATALOG_FILE=/path/to/catalog.yaml`.

```bash
66harness list-sdk-tools
66harness list-mcp
66harness list-sdk-tools --json --ref ra-camptools
```

`--sdk-tools`, `--mcp`, `--sdk-query`, and `--sdk-ref` on `init` use the same fetch. Missing pip extras still print an install hint.

---

## `init`

Create a **new directory** (or fill an **empty cwd**) that is a runtime copy of this template plus **one** domain and **one** workflow. Writes `.env` and `config/app.yaml`. Unused factory folders stay on disk. `catalogs/` and `cli/` are not copied.

### Interactive

```bash
mkdir ~/Desktop/demo-afi && cd ~/Desktop/demo-afi
66harness init
```

1. Location — empty folder: confirm this folder; factory repo: refuse `.`; nonempty: subfolder  
2. Domain (`bfs`, `hcls`, `retail`, `org`)
3. Workflow  
4. Plan card: graph, **platform stack**, agents + agent tools (Training Coordinator also asks for its ingest source)
5. Accept (keep catalog stack), **Change stack**, or Customize agents  
6. Optional factories: Asset Factory, ADK, **Enable gemini-enterprise**, **Agent framework** (`agent-cli` default), Looker, BQML  
7. Summary → Create project?

`--yes` always accepts the catalog plan and that workflow’s `recommended_stack`.

`init` refuses the template source tree. If `config/app.yaml` already has a project block, it warns that `init` creates a **new** folder.

### Non-interactive

`--yes` requires `--domain` and `--workflow`. `--name` is required unless the current directory is empty (then the folder name is used).

```bash
66harness init \
  --name demo-afi \
  --output ~/Desktop/demo-afi \
  --domain bfs \
  --workflow afi \
  --yes
```

### Dry run (no files written)

```bash
66harness init \
  --name demo \
  --output ~/Desktop/demo \
  --domain retail \
  --workflow dispute_handler \
  --yes \
  --dry-run
```

### Replay a previous run

```bash
66harness init --from-choices /path/to/factory-choices.json --output /Users/ritesh/Desktop/copy
```

Optional `--name` / `--output` override the JSON.

### All `init` flags

| Flag | Default | Meaning |
|------|---------|---------|
| `--name` | (prompt / `my-agent-project`) | Project name; written to `pyproject.toml` |
| `--output` | `./<name>` | Destination directory |
| `--domain` | (prompt) | Catalog domain id |
| `--workflow` | (prompt) | One workflow id in that domain |
| `--ingest-source` | `sharepoint` | Training Coordinator ingest: `sharepoint` \| `workday` |
| `--gateway` | `litellm` | `litellm` \| `openai` \| `bedrock` \| `ollama` \| `kong` (planned) |
| `--default-model` | `gemini/gemini-2.5-flash` | `GATEWAY_DEFAULT_MODEL` |
| `--cache` | `memory` | `memory` \| `redis` \| `memcached` |
| `--redis-url` | `redis://localhost:6379/0` | `CACHE_REDIS_URL` |
| `--memcached-url` | `memcached://localhost:11211` | `CACHE_MEMCACHED_URL` |
| `--vector` | `memory` | `memory` \| `opensearch` \| `qdrant` \| `pgvector` \| `weaviate` |
| `--opensearch-url` | `http://localhost:9200` | `VECTOR_OPENSEARCH_URL` |
| *(no `--qdrant-url` flag)* | `http://localhost:6333` | Wizard-only; default `VECTOR_QDRANT_URL` in `factory-choices.json` |
| `--embeddings` | `litellm` | `litellm` \| `jina` |
| `--parser` | `docling` | `PDF_BACKEND` |
| `--guardrails` | `passthrough` | `passthrough` \| `bedrock` |
| `--eval` | `local` | `local` \| `deepeval` |
| `--langfuse` / `--no-langfuse` | off | `LANGFUSE_ENABLED` |
| `--logfire` / `--no-logfire` | off | `LOGFIRE_ENABLED` |
| `--adk` / `--no-adk` | off (on for `gsse` `--yes`) | `ADK_ENABLED` |
| `--a2a` / `--no-a2a` | off | `A2A_ENABLED` |
| `--looker` / `--no-looker` | off | `LOOKER_ENABLED` |
| `--bqml` / `--no-bqml` | off | `BQML_ENABLED` |
| `--assets` / `--no-assets` | off (on for `gsse` `--yes`) | `ASSETS_ENABLED` |
| `--asset-pack` | `core` (or `district_dine` for `gsse`) | `ASSETS_PACK` |
| `--gemini-enterprise` / `--no-gemini-enterprise` | off | `GEMINI_ENTERPRISE_ENABLED` (scaffold only) |
| `--framework` | `agent-cli` | `agent-cli` nested Google project + catalog overlay (`AGENT_CLI_ENABLED`, forces ADK). `none` skips it. PATH: `uv tool install google-agents-cli`. `--dry-run` prints overlay JSON, no subprocess |
| `--mcp-examples` / `--no-mcp-examples` | off | generic npx MCP stub if `--mcp` is not set |
| `--sdk-tools` | — | Pack name or tool ids from the live GitHub catalog. Sets assets pack. Requires `uv sync --extra asset-factory` on `--yes` |
| `--sdk-query` | — | Search the live catalog (overrides workflow `sdk.query`) |
| `--sdk-ref` | `ra-camptools` | Git ref of `66degrees/agentic-asset-factory` |
| `--mcp` | — | MCP ids from `list-mcp` → workflow `mcp.yaml`. Requires MCP extra on `--yes` |
| `--secrets-backend` | `env` | `env` \| `vault` \| `aws_secrets_manager` \| `sops` |
| `--environment` | `local` | `local` \| `dev` \| `test` \| `uat` \| `production` |
| `--yes` | off | No prompts; requires name, domain, workflow |
| `--dry-run` | off | Print plan and `.env`; write nothing |
| `--force` | off | Overwrite a non-empty destination |
| `--force-planned` | off | Allow `--yes` with planned backends (Kong, pgvector, …) |
| `--from-choices` | — | Path to `factory-choices.json` or `config/app.yaml` |
| `--custom-domain` | `other` | Folder slug when `--domain other` |

`--yes` **rejects** planned backends unless `--force-planned`.

`--framework` vs `--gemini-enterprise` vs `--adk`: `--framework agent-cli` (the default) **does not copy** the FastAPI template. It writes the catalog workflow under `domains/…/workflows/…/`, a nested `agents_cli/<slug>/` overlay, evals, a short README, and a slim `.env`. `--framework none` copies the FastAPI tree (`app/`, `factories/`, `config/app.yaml`, …) so `make dev` works. `--adk` with agent-cli only adds `ADK_*` to `.env`; it does not pull in FastAPI. `--gemini-enterprise` writes Gallery-style YAML next to the workflow (no publish). None of them pip-installs `factory66-cli`.

`.env` only includes factory blocks that are **on** (Looker, BQML, Assets, A2A, Langfuse, …). Disabled factories stay on their settings.py defaults.

---

## `serve`

Start uvicorn (`app.main:app`). Same as the old `factory` launcher.

```bash
66harness serve
66harness serve --host 127.0.0.1 --port 8000
```

| Flag | Default | Meaning |
|------|---------|---------|
| `--host` | `0.0.0.0` | Bind address |
| `--port` | `8000` | Port |

Reload follows `Settings.debug` (local overlay often sets `debug: true`).

Equivalent without the CLI:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
make dev
```
