.PHONY: install dev lint typecheck test contract integration eval openapi run docs docker-build clean \
	policy-install policy-input policy-check policy-test policy-lint policy

# Pinned in .tool-versions so CI and a laptop evaluate the same policy.
TOOLS_DIR := .tools
OPA_VERSION := $(shell awk '/^opa /{print $$2}' .tool-versions)
REGAL_VERSION := $(shell awk '/^regal /{print $$2}' .tool-versions)
OPA := $(TOOLS_DIR)/opa
REGAL := $(TOOLS_DIR)/regal
UNAME_S := $(shell uname -s)
UNAME_M := $(shell uname -m)

install:
	uv sync --all-groups

dev: install
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

adk-web: install
	uv run adk web adk_agents --port 8080

adk-deploy: install
	uv run adk deploy cloud_run \
		--project ai-ml-team-sandbox \
		--region us-central1 \
		--service_name tca-adk-demo \
		--with_ui \
		--otel_to_cloud \
		--trace_to_cloud \
		--app_name training_coordinator \
		--extra_packages factories \
		--extra_packages config \
		--extra_packages domains \
		--extra_packages shared \
		--env ADK_ENABLED=true \
		--env ADK_DEFAULT_MODEL=openrouter/openai/gpt-oss-120b \
		adk_agents/training_coordinator \
		-- \
		--allow-unauthenticated \
		--cpu=2 \
		--memory=2Gi \
		--timeout=600 \
		--min-instances=1 \
		--no-cpu-throttling \
		--set-secrets=OPENROUTER_API_KEY=tca-openrouter-api-key:latest

lint:
	uv run ruff check app agents shared factories config tests examples cli governance

typecheck:
	uv run mypy app agents shared factories config --ignore-missing-imports

test:
	uv run pytest tests -m "not integration"

contract:
	uv run pytest tests/contract tests/mcp -v

integration:
	uv run pytest tests/integration -v

eval:
	uv run pytest tests/evaluation -v

openapi:
	uv run python -c "from app.main import export_openapi; export_openapi()"

run:
	uv run factory serve

docs:
	uv sync --group docs
	uv run mkdocs serve -a 127.0.0.1:8001

docs-build:
	uv sync --group docs
	uv run mkdocs build
	rm -rf deploy/docs/site
	cp -R site deploy/docs/site

docs-deploy: docs-build
	gcloud run deploy adf-factory-docs \
		--project=ai-ml-team-sandbox \
		--region=us-central1 \
		--source deploy/docs \
		--allow-unauthenticated \
		--port=8080

docker-build:
	docker build -t multi-agent-factory:latest .

# ---- Contribution policy -------------------------------------------------
# See CONTRIBUTING.md. `make policy-check` answers "would CI let this through?"

policy-install: $(OPA) $(REGAL)

$(OPA):
	@mkdir -p $(TOOLS_DIR)
	@echo "downloading opa $(OPA_VERSION)"
	@curl -sSL -o $(OPA) \
		"https://github.com/open-policy-agent/opa/releases/download/v$(OPA_VERSION)/opa_$(shell echo $(UNAME_S) | tr A-Z a-z)_$(if $(filter arm64 aarch64,$(UNAME_M)),arm64,amd64)"
	@chmod +x $(OPA)

$(REGAL):
	@mkdir -p $(TOOLS_DIR)
	@echo "downloading regal $(REGAL_VERSION)"
	@curl -sSL -o $(REGAL) \
		"https://github.com/open-policy-agent/regal/releases/download/v$(REGAL_VERSION)/regal_$(UNAME_S)_$(if $(filter arm64 aarch64,$(UNAME_M)),arm64,x86_64)"
	@chmod +x $(REGAL)

# Snapshot the shipping catalog so the policy tests can prove that every
# workflow already in the repo satisfies the standards imposed on new ones.
policy-fixtures:
	@python3 -c "import json; \
		from cli.catalog_load import merge_shards; \
		json.dump({'governance': {'fixtures': {'catalog_snapshot': merge_shards()}}}, \
		open('governance/fixtures/catalog_snapshot.json','w'), indent=2, sort_keys=True); \
		open('governance/fixtures/catalog_snapshot.json','a').write('\n')"

policy-input: policy-install
	@python3 governance/input/build_input.py --local -o $(TOOLS_DIR)/input.json

policy-check: policy-input
	@$(OPA) eval --format=json --fail \
		--ignore '*_test.rego' \
		-d governance/policy -d governance/data \
		-s governance/schema/input.json \
		-i $(TOOLS_DIR)/input.json \
		'data.governance.contribution.decision' > $(TOOLS_DIR)/decision.json
	@python3 governance/report.py $(TOOLS_DIR)/decision.json

policy-test: policy-install
	@$(OPA) test governance/policy governance/data governance/fixtures --fail-on-empty -v

policy-lint: policy-install
	@$(OPA) fmt --list --fail governance/policy
	@$(OPA) check --strict governance/policy governance/data
	@$(REGAL) lint governance/policy

policy: policy-lint policy-test policy-check

clean:
	rm -rf dist data .pytest_cache .mypy_cache .ruff_cache $(TOOLS_DIR)
