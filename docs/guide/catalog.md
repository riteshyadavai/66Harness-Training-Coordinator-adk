# Catalog layout

Repo: [66degrees/66harness](https://github.com/66degrees/66harness).

The CLI menu is **not** a single `catalog.yaml`. Files under `catalogs/` are merged at load time into `{version, domains, factories}`. `66harness` list commands, the wizard, and `init` all use that merge. Generated apps still do **not** receive `catalogs/`.

OPA policy tests load the merged snapshot at `governance/fixtures/catalog_snapshot.json` (`make policy-fixtures`). Do not pass `catalogs/catalog.yaml` to `opa test`.

```text
catalogs/
  version.yaml              # package/catalog version string
  factories.yaml            # factories.capabilities (LLM, cache, vector, …)
  domains/
    bfs.yaml                # stem = domain id
    hcls.yaml
    retail.yaml
    org.yaml
    other.yaml
```

Each `domains/<id>.yaml` is the domain body only (`name`, `aliases`, `workflows`, …). Do not wrap it in a `domains:` key.

SDK tools are not copied into this catalog. Point at them with `sdk.query` (and optional `sdk.kind`). `66harness init` fetches `forge66/catalog.yaml` from GitHub and fills `tools` at generate time.

## What to edit

| Change | File |
|--------|------|
| New or updated workflow / agents / evals / graph | `catalogs/domains/<domain>.yaml` |
| New factory backend or capability | `catalogs/factories.yaml` |
| Version string shipped with the menu | `catalogs/version.yaml` (keep in sync with the package) |

After catalog edits:

```bash
make policy-fixtures
```

Commit the updated `governance/fixtures/catalog_snapshot.json`.

## Commands (unchanged)

```bash
66harness list-domains
66harness list-workflows --domain org
66harness list-factories
66harness init --name demo --domain org --workflow training-coordinator-agent --yes --framework none
```
