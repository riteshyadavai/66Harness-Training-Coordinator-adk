# OPA Governance & Contribution Rules

This document outlines the **Open Policy Agent (OPA)** governance framework enforced in this repository. It details what policies exist, which paths are governed, the standards contributions must satisfy, and best practices for developers.

---

## Overview

The multi-agent factory repository serves as a foundational blueprint: code, catalog specifications, and infrastructure configurations here are copied into every application generated via `factory init`. Consequently, defects, security oversights, or interface changes propagate to all downstream downstream projects.

To enforce high quality and prevent architectural drift, contributions are validated against **Policy-as-Code** written in [Rego](https://www.openpolicyagent.org/docs/latest/policy-language/) and evaluated by [Open Policy Agent (OPA)](https://www.openpolicyagent.org/).

### How OPA Governance Operates

1. **Base-Branch Evaluation**: In CI, policies and ownership configurations are always evaluated from the repository's **base branch** (e.g., `main`), never from the pull request branch. A contributor cannot weaken or delete a rule to pass their own PR.
2. **Deterministic Change-Set Inputs**: A dedicated builder (`governance/input/build_input.py`) extracts the branch diff, file additions, deletions, modified lines, and pull request metadata into a structured JSON document conforming to `governance/schema/input.json`.
3. **Structured Decisions**: Rather than a binary pass/fail, OPA produces an actionable decision object containing `violations`, `required_approvals`, and `warnings`, including clear remediation steps.
4. **Automated Reviewer Requests**: CI reads OPA's decision and automatically requests reviews from the specific team members mapped to the modified files (`governance/input/request_reviewers.py`).

---

## Path Governance Tiers

Repository paths are categorized into three tiers declared in `governance/data/paths.yaml`:

```
       ┌────────────────────────┐
       │     Repository Diff    │
       └───────────┬────────────┘
                   │
         ┌─────────┼─────────┐
         ▼         ▼         ▼
     [Frozen]   [Owned]   [Open]
```

### 1. Frozen Tier (Denied by Default)

Frozen paths represent foundational contracts or governance controls. Unauthorized modifications are denied outright.

| Paths | Rationale | Override Label | Override Team |
|---|---|---|---|
| `factories/*/protocol.py`<br>`factories/registry.py`<br>`agents/contracts.py` | Core interfaces that every scaffolded application depends upon. Changes break downstream compatibility silently. | `policy:contract-change` | `maintainers` |
| `governance/**`<br>`.tool-versions` | Governance engine, policy rules, and pinned tool versions. | `policy:governance-change` | `maintainers` |

!!! note "Exemption for New Capability Contracts"
    Adding a **new** capability protocol (e.g., creating a new `factories/new_capability/protocol.py`) is permitted without an override because downstream projects cannot yet depend on an interface that did not previously exist (`exempt_new_files: true`). Editing or deleting an existing protocol remains strictly frozen.

#### Override Procedure
If changes to a frozen file are genuinely necessary:
1. Discuss the change and downstream impact with the `maintainers` team.
2. Have a maintainer apply the appropriate override label (`policy:contract-change` or `policy:governance-change`) to the pull request.
3. Obtain at least 1 approval from a member of the `maintainers` team.

---

### 2. Owned Tier (Requires Team Approval)

Owned files are open to contribution but require explicit sign-off from the governing team defined in `governance/data/owners.yaml`.

| Rule ID | Governed Patterns | Owning Team | Scope & Rationale |
|---|---|---|---|
| `security-runtime` | `agents/security/**`<br>`agents/mcp/registry.py`<br>`shared/schemas.py`<br>`shared/middleware.py`<br>`docs/security/**` | `security` | Authentication, authorization, tool permissions, input sanitization, trust boundaries, and tenant isolation. |
| `runtime-payload` | `app/**`<br>`agents/**`<br>`factories/**`<br>`config/**`<br>`shared/**` | `platform` | The runtime template copied verbatim into generated projects. *(Excludes security files carved out above).* |
| `test-suite` | `tests/**`<br>`evals/**` | `platform` | Test suites, test fixtures, and evaluation gates. |
| `supply-chain` | `.github/**`<br>`Dockerfile`<br>`pyproject.toml`<br>`uv.lock`<br>`deployment/**`<br>`deploy/**` | `platform` | Dependencies, container builds, CI workflows, and deployment configurations. |
| `generator` | `cli/**` | `platform` | The `factory` CLI and project scaffolding logic. |
| `catalog` | `catalogs/**` | `platform` | Domain and workflow catalog definitions. |

#### Approval Rules
- **Fresh Approvals**: Approvals are bound to the specific commit evaluated. Pushing new commits invalidates prior approvals.
- **No Self-Approvals**: Pull request authors cannot approve their own changes.
- **Carve-Outs**: Narrow rules take precedence over broad rules (e.g., `agents/security/**` requires only `security`, not both `security` and `platform`).

---

### 3. Open Tier

Any file not matched by frozen or owned rules:
- `docs/**` (outside `docs/security/**`)
- `examples/**`
- `notebooks/**`
- `README.md`
- `.env.example`

Open paths require no specialized team approvals, but must still satisfy all linting, credential, and environment variable standards.

---

## Contribution Standards Enforced by OPA

Beyond team ownership, OPA enforces structural completeness, schema consistency, and security hygiene (defined in `governance/data/standards.yaml`).

### Rule 1: Factory Backend Completeness (`structure/factory-backend-*`)

When contributing a new vendor backend under `factories/<capability>/<vendor>/`, the PR must be structurally complete:
1. **Registration**: Must register the new backend in `factories/<capability>/factory.py`.
2. **Unit Test**: Must include a unit test under `tests/unit/**`.
3. **Documentation**: Must describe the backend in `docs/architecture/factories.md`.

*Incomplete backends that land without tests or registration are blocked.*

---

### Rule 2: Catalog Structure & Semantic Consistency (`catalog/*`, `structure/*`)

When adding or modifying domains or workflows in `catalogs/domains/*.yaml`:

#### Domain Completeness
New domains must declare:
- `name`
- `aliases`
- `description`
- `workflows`

#### Workflow Completeness
New workflows must declare:
- `name`, `summary`, `recommended_stack`, `skills`, `tools`
- `evals`: At least 1 evaluation definition
- `agents`: At least 1 agent definition
- `graph`: Must define `entry` and `nodes`

#### Agent Completeness
Every agent defined under a workflow must have:
- `name`
- `description`
- `prompt_stub`

#### Semantic Integrity Checks
- **Graph Entry**: `graph.entry` must reference a valid node ID in `graph.nodes`.
- **Graph Edges**: Every target in `node.next` must reference an existing node ID.
- **Node Agents**: If a node specifies `agent_name`, that agent must be declared in the workflow's `agents` list.
- **Tool Allowlist**: Any tool listed in an agent's `allowed_tools` must either be declared in the workflow's `tools` list or be a runtime builtin (`vector_search`).
- **Alias Uniqueness**:
  - Workflow aliases must be unique within their domain.
  - Domain aliases must be globally unique across the entire catalog.

---

### Rule 3: Secret Hygiene (`secrets/*`)

OPA scans all newly added lines in the diff:
- **No Hardcoded Secrets**: Scans for patterns including Google API keys (`AIza...`), OpenAI API keys (`sk-...`), AWS access keys (`AKIA...`), GitHub personal access tokens (`ghp_...`), Slack tokens (`xox...`), and private key blocks (`-----BEGIN ... PRIVATE KEY-----`).
- **Forbidden Files**: Committing any of the following files is blocked:
  - `.env`, `.env.local`, `.env.*.local`
  - `*.pem`, `*.p12`, `*.pfx`
  - `*service-account*.json`
- **Permitted Placeholders**: If documenting credential formats, use recognized placeholders like `your-api-key`, `${SOME_ENV}`, or dummy strings.

---

### Rule 4: Undocumented Environment Variables (`secrets/undocumented-env-var`)

Any environment variable referenced in code (e.g., via `os.getenv("VAR")`, `os.environ["VAR"]`, or `os.environ.get("VAR")`) must be documented in `.env.example`.

- Can be commented or uncommented in `.env.example`.
- Standard runtime/system variables (e.g., `PATH`, `CI`, `HOME`, `PORT`) are exempted.
- Code under `tests/`, `evals/`, `notebooks/`, `docs/`, and `governance/` is exempted.

---

## Local Developer Workflow

You can run the exact governance checks locally before pushing code.

### 1. Install Tooling

Install the pinned versions of `opa` and `regal` specified in `.tool-versions`:

```bash
make policy-install
```

Binaries are placed in `.tools/`.

### 2. Run Policy Check

Evaluate your working tree (including unstaged and uncommitted changes):

```bash
make policy-check
```

This runs `governance/input/build_input.py --local`, evaluates the policy via OPA, and outputs a formatted report:

```text
wrote .tools/input.json (5 changed paths)
REVIEW Generated application payload
      needs 1 approval(s) from `platform`
      app/main.py
OK: All structural rules passed.
```

### 3. Run Policy Unit Tests and Linters

If you modify or add governance policies:

```bash
# Run Rego unit tests
make policy-test

# Lint Rego code with opa fmt and Regal
make policy-lint

# Run all policy checks (lint + test + local check)
make policy
```

### 4. Enable Pre-Commit Hooks

To automatically verify policy on push:

```bash
uv run pre-commit install --install-hooks
```

Fast formatting/linting runs on commit; the full OPA policy check executes on `git push`.

### 5. Update Catalog Snapshot Fixture

The test suite checks that the existing catalog satisfies all standards via `governance/fixtures/catalog_snapshot.json`. If you update `catalogs/domains/` or `catalogs/factories.yaml`, regenerate the fixture:

```bash
make policy-fixtures
```

---

## Best Practices

### For Contributors

1. **Check Before Pushing**: Always execute `make policy-check` prior to pushing your branch. Fixing violations locally is much faster than waiting for CI feedback.
2. **Never Commit Secrets**: Do not commit test API keys or `.env` files even temporarily. Use local `.env` files that are ignored by `.gitignore`.
3. **Keep Backends Complete**: When introducing a new capability backend, ensure the factory registration, tests, and documentation are committed together in the same PR.
4. **Document New Config**: Whenever adding `os.getenv("MY_NEW_VAR")`, immediately add `MY_NEW_VAR=` to `.env.example`.
5. **Keep PRs Focused**: Avoid touching files across disparate domains or tiers unless necessary. Touching both `security` and `platform` paths requires reviews from both teams.

### For Maintainers & Policy Authors

1. **Prefer YAML Data Over Rego Logic**:
   - To add a team or modify membership: update `governance/data/owners.yaml`.
   - To protect a new path or change tiers: update `governance/data/paths.yaml`.
   - To adjust allowed tools or keys: update `governance/data/standards.yaml`.
   - Modifying data files avoids introducing regressions in Rego policy code.
2. **Test Every Policy Rule**:
   - Every Rego denial or requirement must have corresponding unit tests in `governance/policy/*_test.rego`.
   - Maintain 100% test coverage for governance policies.
3. **Ensure Deterministic Reports**:
   - Sort all arrays and iteration outputs in Rego (`sort(...)`) so reports and PR comments remain stable and reproducible.
4. **Calibrate Rules Against Historical Commits**:
   - When introducing a new policy rule, test it against past commits to detect false positives before rolling it out:
     ```bash
     python3 governance/input/build_input.py --range "<sha>~1..<sha>" -o /tmp/input.json
     .tools/opa eval --format=json --ignore '*_test.rego' \
       -d governance/policy -d governance/data -s governance/schema/input.json \
       -i /tmp/input.json 'data.governance.contribution.decision'
     ```
