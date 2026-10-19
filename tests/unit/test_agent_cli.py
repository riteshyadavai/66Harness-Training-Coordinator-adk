"""Overlay mapping for Google agents-cli (no live binary)."""

from pathlib import Path

from cli.agent_cli import overlay_class_names, overlay_instruction, patch_agent_py
from cli.catalog import get_workflow


def test_overlay_class_names_gsse_district_dine():
    names = overlay_class_names(assets_enabled=True, asset_pack="district_dine")
    assert "IngestCensusAcsDag" in names
    assert "AnySQLSafeExecutor" not in names


def test_overlay_class_names_core_pack():
    names = overlay_class_names(assets_enabled=True, asset_pack="core")
    assert names[:6] == [
        "AnySQLSafeExecutor",
        "DynamicOpenAPIClient",
        "HITLApprovalGateway",
        "PIIToxicContentShield",
        "OmniChannelDocumentCrawler",
        "ZeroCodeVectorSyncNode",
    ]


def test_overlay_class_names_assets_off():
    assert overlay_class_names(assets_enabled=False, asset_pack="district_dine") == []


def test_overlay_instruction_uses_catalog():
    gsse = get_workflow("retail", "gsse")
    text = overlay_instruction(gsse)
    assert "gsse" in text.lower()
    dispute = get_workflow("retail", "dispute_handler")
    assert "dispute" in overlay_instruction(dispute).lower()


def test_patch_agent_py_markers(tmp_path: Path):
    path = tmp_path / "agent.py"
    path.write_text(
        "from google.adk.agents import Agent\n"
        'instruction="x"\n'
        "tools=[]\n",
        encoding="utf-8",
    )
    patch_agent_py(path, ["AnySQLSafeExecutor"], "hello")
    text = path.read_text(encoding="utf-8")
    assert "# --- factory overlay start ---" in text
    assert "AnySQLSafeExecutor" in text
    assert "instruction=FACTORY_INSTRUCTION" in text
    assert "tools=[AnySQLSafeExecutor]" in text
