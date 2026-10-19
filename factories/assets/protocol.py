"""Enterprise Asset Factory bundle — wraps enterprise_agent_sdk assets."""

from __future__ import annotations

from typing import Any, Protocol


class AssetsDisabledError(RuntimeError):
    pass


class AssetsConfigError(RuntimeError):
    pass


class HydratedAsset(Protocol):
    def safe_run(self, **kwargs: Any) -> Any: ...


class AssetBundle:
    """Lazy accessors for hydrated SDK assets. Missing config raises; no fake results."""

    def __init__(
        self,
        *,
        enabled: bool,
        pack: str = "core",
        sql: Any | None = None,
        openapi: Any | None = None,
        hitl: Any | None = None,
        pii: Any | None = None,
        crawler: Any | None = None,
        vector_sync: Any | None = None,
        census: Any | None = None,
        osm: Any | None = None,
        transit: Any | None = None,
        gold_features: Any | None = None,
        sites_catalog: Any | None = None,
        suitability_model: Any | None = None,
        sites_explore: Any | None = None,
        bqml_train: Any | None = None,
        bqml_infer: Any | None = None,
        nav: Any | None = None,
        grounded_analytics: Any | None = None,
        reasoning: Any | None = None,
    ) -> None:
        self.enabled = enabled
        self.pack = pack
        self._sql = sql
        self._openapi = openapi
        self._hitl = hitl
        self._pii = pii
        self._crawler = crawler
        self._vector_sync = vector_sync
        self._census = census
        self._osm = osm
        self._transit = transit
        self._gold_features = gold_features
        self._sites_catalog = sites_catalog
        self._suitability_model = suitability_model
        self._sites_explore = sites_explore
        self._bqml_train = bqml_train
        self._bqml_infer = bqml_infer
        self._nav = nav
        self._grounded_analytics = grounded_analytics
        self._reasoning = reasoning

    def _require_enabled(self) -> None:
        if not self.enabled:
            raise AssetsDisabledError(
                "Asset Factory is disabled. Set ASSETS_ENABLED=true and "
                "uv sync --extra asset-factory."
            )

    def _require(self, name: str, tool: Any | None, env_hint: str) -> Any:
        self._require_enabled()
        if tool is None:
            from factories.assets.packs import resolve_pack

            if name not in resolve_pack(self.pack):
                raise AssetsConfigError(f"{name} is not in ASSETS_PACK={self.pack}.")
            raise AssetsConfigError(env_hint)
        return tool

    def sql(self) -> Any:
        return self._require(
            "sql",
            self._sql,
            "ASSETS_SQL_DB_URL is required to hydrate AnySQLSafeExecutor.",
        )

    def openapi(self) -> Any:
        return self._require(
            "openapi",
            self._openapi,
            "ASSETS_OPENAPI_BASE_URL and ASSETS_OPENAPI_SPEC_URL are required.",
        )

    def hitl(self) -> Any:
        return self._require("hitl", self._hitl, "ASSETS_HITL_WEBHOOK_URL is required.")

    def pii(self) -> Any:
        return self._require("pii", self._pii, "PII shield failed to hydrate.")

    def crawler(self) -> Any:
        return self._require(
            "crawler",
            self._crawler,
            "ASSETS_CRAWLER_ALLOWED_FOLDERS is required "
            "(source_type=local, or s3 with credentials).",
        )

    def vector_sync(self) -> Any:
        return self._require(
            "vector_sync",
            self._vector_sync,
            "Vector sync failed to hydrate (memory provider only).",
        )

    def census(self) -> Any:
        return self._require("census", self._census, "IngestCensusAcsDag failed to hydrate.")

    def osm(self) -> Any:
        return self._require("osm", self._osm, "IngestOsmOvertureDag failed to hydrate.")

    def transit(self) -> Any:
        return self._require(
            "transit", self._transit, "IngestTransitTrafficDag failed to hydrate."
        )

    def gold_features(self) -> Any:
        return self._require(
            "gold_features", self._gold_features, "GoldFeatureStoreView failed to hydrate."
        )

    def sites_catalog(self) -> Any:
        return self._require(
            "sites_catalog",
            self._sites_catalog,
            "SitesCatalogTableSchema failed to hydrate.",
        )

    def suitability_model(self) -> Any:
        return self._require(
            "suitability_model",
            self._suitability_model,
            "SiteSuitabilityModel failed to hydrate.",
        )

    def sites_explore(self) -> Any:
        return self._require(
            "sites_explore", self._sites_explore, "SitesCatalogExplore failed to hydrate."
        )

    def bqml_train(self) -> Any:
        return self._require(
            "bqml_train",
            self._bqml_train,
            "BqmlSiteScoringPipeline failed to hydrate.",
        )

    def bqml_infer(self) -> Any:
        return self._require(
            "bqml_infer",
            self._bqml_infer,
            "BqmlRealtimeInferenceRoutine failed to hydrate.",
        )

    def nav(self) -> Any:
        return self._require("nav", self._nav, "NaturalLanguageNavTool failed to hydrate.")

    def grounded_analytics(self) -> Any:
        return self._require(
            "grounded_analytics",
            self._grounded_analytics,
            "GroundedAnalyticsTool failed to hydrate.",
        )

    def reasoning(self) -> Any:
        return self._require(
            "reasoning",
            self._reasoning,
            "ExplainableReasoningEngine failed to hydrate.",
        )
