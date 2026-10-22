"""Locate the repo root without importing config.settings (Cloud Run ADK image)."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in (Path("/app"), Path.cwd(), *here.parents):
        if (candidate / "domains" / "org" / "workflows" / "training-coordinator-agent").is_dir():
            return candidate
    return Path.cwd()
