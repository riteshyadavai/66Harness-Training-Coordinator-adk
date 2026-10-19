"""Named Asset Factory packs (core vs District Dine)."""

from __future__ import annotations

from factories.assets.protocol import AssetsConfigError

CORE_TOOL_NAMES: tuple[str, ...] = (
    "sql",
    "openapi",
    "hitl",
    "pii",
    "crawler",
    "vector_sync",
)

DISTRICT_DINE_TOOL_NAMES: tuple[str, ...] = (
    "census",
    "osm",
    "transit",
    "gold_features",
    "sites_catalog",
    "suitability_model",
    "sites_explore",
    "bqml_train",
    "bqml_infer",
    "nav",
    "grounded_analytics",
    "reasoning",
)

ALL_TOOL_NAMES: tuple[str, ...] = CORE_TOOL_NAMES + DISTRICT_DINE_TOOL_NAMES

PACK_NAMES = ("core", "district_dine", "all")

_PACK_TOOLS: dict[str, frozenset[str]] = {
    "core": frozenset(CORE_TOOL_NAMES),
    "district_dine": frozenset(DISTRICT_DINE_TOOL_NAMES),
    "all": frozenset(ALL_TOOL_NAMES),
}


def normalize_pack(name: str | None) -> str:
    key = (name or "core").strip().lower().replace("-", "_")
    if key not in _PACK_TOOLS:
        raise AssetsConfigError(
            f"Unknown ASSETS_PACK '{name}'. Use: {', '.join(PACK_NAMES)}."
        )
    return key


def resolve_pack(name: str | None) -> frozenset[str]:
    return _PACK_TOOLS[normalize_pack(name)]


def pack_needs_core(name: str | None) -> bool:
    return bool(resolve_pack(name) & frozenset(CORE_TOOL_NAMES))


def pack_needs_district_dine(name: str | None) -> bool:
    return bool(resolve_pack(name) & frozenset(DISTRICT_DINE_TOOL_NAMES))


def tool_names_for_pack(name: str | None) -> tuple[str, ...]:
    allowed = resolve_pack(name)
    return tuple(tool for tool in ALL_TOOL_NAMES if tool in allowed)


def init_asset_pack(
    *,
    flag: str | None,
    recommended: str | None,
    assets_enabled: bool,
) -> str:
    if flag:
        return normalize_pack(flag)
    if not assets_enabled:
        return "core"
    return normalize_pack(recommended or "core")
