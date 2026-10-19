"""ADK Dev UI entry: `uv run adk web adk_agents` then pick training_coordinator."""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

from factories.adk.tca_graph import build_root_agent  # noqa: E402

root_agent = build_root_agent()
