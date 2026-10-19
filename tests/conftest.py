from pathlib import Path

import pytest

from cli import copier, main, sdk_inventory, wizard
from cli import sdk_remote as sdk_remote_mod

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sdk_catalog.yaml"
_orig_fetch = sdk_remote_mod.fetch_sdk_catalog


@pytest.fixture(autouse=True)
def _mock_live_sdk_catalog(monkeypatch: pytest.MonkeyPatch) -> None:
    def _load(ref: str = "ra-camptools", *, text: str | None = None):
        body = text if text is not None else _FIXTURE.read_text(encoding="utf-8")
        return _orig_fetch(ref=ref, text=body)

    monkeypatch.setattr(sdk_remote_mod, "fetch_sdk_catalog", _load)
    monkeypatch.setattr(sdk_inventory, "fetch_sdk_catalog", _load)
    monkeypatch.setattr(main, "fetch_sdk_catalog", _load)
    monkeypatch.setattr(copier, "fetch_sdk_catalog", _load)
    monkeypatch.setattr(wizard, "fetch_sdk_catalog", _load)
