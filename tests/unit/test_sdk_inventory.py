"""SDK category inventory and init --mcp/--sdk-tools (mocked extras + catalog)."""

from pathlib import Path

from typer.testing import CliRunner

from cli.main import app
from cli.sdk_inventory import (
    mcp_yaml_payload,
    parse_mcp_flag,
    parse_sdk_tools_flag,
    sdk_categories,
)
from cli.sdk_remote import fetch_sdk_catalog

runner = CliRunner()
FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "sdk_catalog.yaml"


def _catalog():
    return fetch_sdk_catalog(ref="fixture", text=FIXTURE.read_text(encoding="utf-8"))


def test_parse_sdk_tools_packs():
    catalog = _catalog()
    pack, tools = parse_sdk_tools_flag("district_dine", catalog)
    assert pack == "district_dine"
    assert "census" in tools
    pack, tools = parse_sdk_tools_flag("census,osm", catalog)
    assert pack == "district_dine"
    assert tools == ["census", "osm"]


def test_parse_mcp_flag():
    catalog = _catalog()
    assert parse_mcp_flag("outlook,sharepoint", catalog) == ["outlook", "sharepoint"]
    payload = mcp_yaml_payload(["outlook"], catalog)
    assert payload["stdio"]["command"] == "camping-outlook-mcp"
    assert "npx" not in str(mcp_yaml_payload(["outlook", "sharepoint"], catalog))


def test_categories_always_include_district_dine_and_camping(monkeypatch):
    monkeypatch.setattr(
        "cli.sdk_inventory.fetch_sdk_catalog",
        lambda ref="ra-camptools": _catalog(),
    )
    ids = {cat.id for cat in sdk_categories()}
    assert {"core", "district_dine", "camping_world"} <= ids
    camping = next(c for c in sdk_categories() if c.id == "camping_world")
    assert {item.id for item in camping.items} == {"outlook", "sharepoint"}


def test_list_sdk_tools_json(monkeypatch):
    monkeypatch.setattr(
        "cli.sdk_inventory.fetch_sdk_catalog",
        lambda ref="ra-camptools": _catalog(),
    )
    result = runner.invoke(app, ["list-sdk-tools", "--json"])
    assert result.exit_code == 0, result.output
    assert "district_dine" in result.output
    assert "census" in result.output


def test_list_mcp_shows_camping_world(monkeypatch):
    monkeypatch.setattr(
        "cli.sdk_inventory.fetch_sdk_catalog",
        lambda ref="ra-camptools": _catalog(),
    )
    result = runner.invoke(app, ["list-mcp"])
    assert result.exit_code == 0, result.output
    assert "Camping World" in result.output
    assert "outlook" in result.output


def test_init_yes_mcp_missing_extra(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("cli.main.fetch_sdk_catalog", lambda ref="ra-camptools": _catalog())
    monkeypatch.setattr("cli.sdk_inventory.fetch_sdk_catalog", lambda ref="ra-camptools": _catalog())
    monkeypatch.setattr("cli.sdk_inventory._camping_mcp_installed", lambda: False)
    dest = tmp_path / "tca"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "tca",
            "--output",
            str(dest),
            "--domain",
            "org",
            "--workflow",
            "training-coordinator-agent",
            "--framework",
            "none",
            "--mcp",
            "outlook",
            "--yes",
        ],
    )
    assert result.exit_code != 0
    out = result.output.lower()
    assert "mcp" in out and ("not installed" in out or "mcp-connectors" in out or "camping" in out)
    assert not dest.exists()


def test_init_yes_sdk_tools_missing_extra(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("cli.main.fetch_sdk_catalog", lambda ref="ra-camptools": _catalog())
    monkeypatch.setattr("cli.sdk_inventory.fetch_sdk_catalog", lambda ref="ra-camptools": _catalog())
    monkeypatch.setattr("cli.sdk_inventory._assets_installed", lambda: False)
    dest = tmp_path / "gsse"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "gsse",
            "--output",
            str(dest),
            "--domain",
            "retail",
            "--workflow",
            "gsse",
            "--framework",
            "none",
            "--sdk-tools",
            "district_dine",
            "--yes",
        ],
    )
    assert result.exit_code != 0
    assert "asset-factory" in result.output
    assert not dest.exists()


def test_init_mcp_writes_camping_yaml(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("cli.main.fetch_sdk_catalog", lambda ref="ra-camptools": _catalog())
    monkeypatch.setattr("cli.sdk_inventory.fetch_sdk_catalog", lambda ref="ra-camptools": _catalog())
    monkeypatch.setattr("cli.copier.fetch_sdk_catalog", lambda ref="ra-camptools": _catalog())
    monkeypatch.setattr("cli.sdk_inventory._camping_mcp_installed", lambda: True)
    dest = tmp_path / "tca-mcp"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "tca-mcp",
            "--output",
            str(dest),
            "--domain",
            "org",
            "--workflow",
            "training-coordinator-agent",
            "--framework",
            "none",
            "--mcp",
            "outlook,sharepoint",
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    mcp = (
        dest
        / "domains"
        / "org"
        / "workflows"
        / "training-coordinator-agent"
        / "mcp.yaml"
    ).read_text(encoding="utf-8")
    assert "camping-outlook-mcp" in mcp
    assert "127.0.0.1:8080/mcp" in mcp
    assert "npx" not in mcp
    assert "camping_mcp" not in list((dest / "domains").rglob("*.py"))
