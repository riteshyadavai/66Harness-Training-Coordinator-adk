# Security & Guardrails

## Layers

1. **Secrets** — centralized via Vault/AWS Secrets Manager/SOPS; never in prompts
2. **AuthN/AuthZ** — OIDC for humans; scoped tokens for agent-to-MCP
3. **Prompt injection** — MCP results sanitized before LLM context; trust boundary tags
4. **Execution policies** (`agents/security/execution_policies.py`)
5. **Content guardrails** (`factories/guardrails/`)
6. **Audit log** — append-only record of tool calls, model calls, HITL approvals
7. **OPA (policy-as-code)** — workflow blueprints may ship `policies/opa/*.rego` + `data.json` (e.g. retail `dispute_handler` settle thresholds). Bundle is materialized at `init`; wire an OPA-compatible evaluator at runtime to enforce auto-settle vs HITL.

## MCP Tool Allow-Lists

Enforced at `agents/mcp/registry.py`.

## Redaction

PII and secrets redacted at the AI Gateway boundary before logging or observability export.
