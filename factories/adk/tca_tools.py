"""Wrap TCA mock handlers as Google ADK FunctionTools."""

from __future__ import annotations

import importlib.util
from typing import Any

from factories.adk.paths import repo_root

MOCK_PATH = (
    repo_root()
    / "domains"
    / "org"
    / "workflows"
    / "training-coordinator-agent"
    / "tools"
    / "mock_runtime.py"
)


def load_mock_runtime():
    spec = importlib.util.spec_from_file_location("tca_mock_runtime", MOCK_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {MOCK_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def function_tools_for(names: list[str]) -> list[Any]:
    from google.adk.tools import FunctionTool

    runtime = load_mock_runtime()
    tools: list[Any] = []
    for name in names:
        handler = runtime.HANDLERS[name]
        tools.append(FunctionTool(handler))
    return tools
