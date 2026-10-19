"""Named AssetBundle tools for GSSE / ADK."""

from __future__ import annotations

from typing import Any

from config.settings import Settings, get_settings
from factories.assets.factory import make_asset_bundle
from factories.assets.packs import ALL_TOOL_NAMES, tool_names_for_pack
from factories.assets.protocol import AssetsConfigError

ASSET_TOOL_NAMES = ALL_TOOL_NAMES


def run_asset_tool(
    name: str,
    settings: Settings | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    settings = settings or get_settings()
    allowed = tool_names_for_pack(settings.assets.pack)
    if name not in ALL_TOOL_NAMES:
        known = ", ".join(ALL_TOOL_NAMES)
        raise AssetsConfigError(f"Unknown asset tool '{name}'. Known: {known}")
    if name not in allowed:
        raise AssetsConfigError(
            f"{name} is not in ASSETS_PACK={settings.assets.pack}."
        )
    bundle = make_asset_bundle(settings)
    tool = getattr(bundle, name)()
    result = tool.safe_run(**kwargs)
    if hasattr(result, "to_dict"):
        return result.to_dict()
    return {"status": getattr(result, "status", "unknown"), "data": getattr(result, "data", result)}


def adk_function_tools(settings: Settings | None = None) -> list[Any]:
    settings = settings or get_settings()
    if not settings.assets.enabled:
        return []
    try:
        from google.adk.tools import FunctionTool
    except ImportError:
        return []

    def _wrap(tool_name: str):
        def _call(**kwargs: Any) -> dict[str, Any]:
            return run_asset_tool(tool_name, settings=settings, **kwargs)

        _call.__name__ = tool_name
        _call.__doc__ = (
            f"Asset Factory tool `{tool_name}` "
            "(dry-run scaffolds unless live factories are on)."
        )
        return FunctionTool(_call)

    return [_wrap(name) for name in tool_names_for_pack(settings.assets.pack)]
