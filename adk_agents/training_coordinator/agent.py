"""ADK Dev UI entry: `uv run adk web adk_agents` then pick training_coordinator."""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

def _repo_root() -> Path:
    here = Path(__file__).resolve()
    candidates = [Path("/app"), Path.cwd(), *here.parents]
    for candidate in candidates:
        if (candidate / "factories" / "adk" / "tca_graph.py").exists():
            return candidate
    return Path.cwd()


ROOT = _repo_root()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

from factories.adk.tca_graph import build_root_agent  # noqa: E402

root_agent = build_root_agent()
