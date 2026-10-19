"""GSSE dry-run walk: ingest → gold → BQML → analyze → explain → confirm.

Requires: ASSETS_ENABLED=true, ASSETS_PACK=district_dine, and `uv sync --extra asset-factory`.
"""

from __future__ import annotations

from config.settings import AssetsSettings, Settings
from factories.assets.tools import run_asset_tool


def _require_dry_run(payload: dict, label: str) -> None:
    meta = payload.get("meta") or {}
    print(label, payload.get("status"), "dry_run=", meta.get("dry_run"))
    if payload.get("status") not in {"success", "SUCCESS"} and str(
        payload.get("status")
    ) != "AssetStatus.SUCCESS":
        status = payload.get("status")
        if getattr(status, "value", status) != "success":
            raise SystemExit(f"{label} failed: {payload}")
    if not meta.get("dry_run"):
        raise SystemExit(f"{label} expected meta.dry_run")


def main() -> None:
    settings = Settings(assets=AssetsSettings(enabled=True, pack="district_dine"))
    if not settings.assets.enabled:
        raise SystemExit("ASSETS_ENABLED=true is required")

    layers = [
        ("ingest/census", "census", {"run_id": "smoke-census"}),
        ("ingest/osm", "osm", {"run_id": "smoke-osm"}),
        ("ingest/transit", "transit", {"run_id": "smoke-transit"}),
        ("gold", "gold_features", {"location_id": "loc-chi-south-loop-001"}),
        ("score/bqml", "bqml_infer", {"candidate_lat": 41.8781, "candidate_lon": -87.6298}),
        ("analyze/nav", "nav", {"query": "high income areas near transit"}),
        ("explain", "reasoning", {"site_id": "site-001"}),
        ("confirm/sites_catalog", "sites_catalog", {"site_id": "site-001"}),
    ]
    for label, name, kwargs in layers:
        payload = run_asset_tool(name, settings=settings, **kwargs)
        _require_dry_run(payload, label)


if __name__ == "__main__":
    main()
