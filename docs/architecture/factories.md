# Factories

All vendor backends stay under `factories/`. Init choices come from the merged catalog (`catalogs/domains/*.yaml` + `catalogs/factories.yaml`).

```python
from factories.registry import get_factory_registry

reg = get_factory_registry()
cache = reg.cache()
gateway = reg.ai_gateway()
eval_client = reg.eval()
```

## Add a backend

1. Add a row under `factories.capabilities` in `catalogs/factories.yaml` (`implemented` | `planned`).
2. Add `factories/<capability>/<backend>/client.py` (and `connector.yaml`).
3. Branch in `factories/<capability>/factory.py`.
4. `66harness list-factories` and the init wizard pick it up automatically.

DeepEval: `uv sync --group eval` then `EVAL_BACKEND=deepeval`.
Qdrant: `uv sync --extra qdrant`. Memcached: `uv sync --extra cache-memcached`.
Looker: `uv sync --extra looker`. BQML: `uv sync --extra bqml`.
Asset Factory: `uv sync --extra asset-factory` (GitHub `66degrees/agentic-asset-factory` @ `ra-gradient-tools`). Includes District Dine dry-run scaffolds; live Looker/BQML stay on `--looker` / `--bqml`.

Wire agents through `app.platform.Platform`, not by constructing SDKs in `agents/`.
