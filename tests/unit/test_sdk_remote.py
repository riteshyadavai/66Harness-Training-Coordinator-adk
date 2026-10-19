from pathlib import Path

import pytest

from cli.sdk_remote import class_name_from_ref, fetch_sdk_catalog, search_tools

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "sdk_catalog.yaml"


def test_parse_and_search_fixture():
    text = FIXTURE.read_text(encoding="utf-8")
    catalog = fetch_sdk_catalog(ref="fixture", text=text)
    assert catalog.version == "test-1"
    found = search_tools(catalog, "district")
    assert {tool.id for tool in found} >= {"census", "osm"}
    assert class_name_from_ref("enterprise_agent_sdk.assets:CensusAsset") == "CensusAsset"


def test_parse_rejects_non_mapping():
    from cli.sdk_remote import SdkCatalogError

    with pytest.raises(SdkCatalogError):
        fetch_sdk_catalog(text="[]")


def test_download_uses_github_api_when_token_set(monkeypatch):
    from cli import sdk_remote

    monkeypatch.setattr(sdk_remote, "github_token", lambda: "test-token")

    def fake_read(url: str, headers: dict[str, str]) -> str:
        assert "api.github.com" in url
        assert headers.get("Authorization") == "Bearer test-token"
        return FIXTURE.read_text(encoding="utf-8")

    monkeypatch.setattr(sdk_remote, "_read_url", fake_read)
    body = sdk_remote._download_catalog("ra-camptools")
    catalog = fetch_sdk_catalog(ref="ra-camptools", text=body)
    assert "census" in catalog.tool_by_id()


def test_download_explains_private_repo(monkeypatch):
    from cli import sdk_remote
    from cli.sdk_remote import SdkCatalogError

    monkeypatch.delenv("SDK_CATALOG_FILE", raising=False)
    monkeypatch.setattr(sdk_remote, "github_token", lambda: None)
    monkeypatch.setattr(
        sdk_remote,
        "_download_via_gh_cli",
        lambda ref: (_ for _ in ()).throw(SdkCatalogError("not logged in")),
    )
    with pytest.raises(SdkCatalogError, match="private"):
        sdk_remote._download_catalog("ra-camptools")


def test_download_reads_sdk_catalog_file(monkeypatch):
    from cli import sdk_remote

    monkeypatch.setenv("SDK_CATALOG_FILE", str(FIXTURE))
    body = sdk_remote._download_catalog("ignored")
    assert "census" in body
