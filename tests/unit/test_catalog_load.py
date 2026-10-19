"""Merged catalog shards match the former monolith shape."""

from pathlib import Path

import pytest
import yaml

from cli.catalog import load_raw_catalog
from cli.catalog_load import merge_catalog_from_texts, merge_shards


def test_merge_shards_has_expected_domains_and_factories():
    merged = merge_shards()
    assert set(merged["domains"]) == {"bfs", "hcls", "retail", "org", "other"}
    assert merged["factories"]["capabilities"]
    raw = load_raw_catalog()
    assert raw["domains"].keys() == merged["domains"].keys()
    assert raw["factories"] == merged["factories"]


def test_merge_shards_equals_monolith_if_present():
    monolith = Path("catalogs/catalog.yaml")
    if not monolith.is_file():
        pytest.skip("monolith removed; shards are the source of truth")
    expected = yaml.safe_load(monolith.read_text(encoding="utf-8"))
    assert merge_shards() == expected


def test_merge_rejects_duplicate_domain_stem(tmp_path: Path):
    catalogs = tmp_path / "catalogs"
    (catalogs / "domains").mkdir(parents=True)
    (catalogs / "version.yaml").write_text('version: "0.2.21"\n')
    (catalogs / "factories.yaml").write_text("factories:\n  capabilities: []\n")
    body = "name: X\nworkflows: {}\n"
    (catalogs / "domains" / "bfs.yaml").write_text(body)
    (catalogs / "domains" / "bfs.yml").write_text(body)
    with pytest.raises(ValueError, match="duplicate"):
        merge_shards(tmp_path)


def test_merge_rejects_missing_version():
    with pytest.raises(ValueError, match="version.yaml"):
        merge_catalog_from_texts(
            version_text=None,
            factories_text="factories:\n  capabilities: []\n",
            domain_texts={"bfs": "name: X\nworkflows: {}\n"},
        )
