"""Unit tests for the CI reviewer-request adapter."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "request_reviewers",
    ROOT / "governance" / "input" / "request_reviewers.py",
)
assert SPEC and SPEC.loader
reviewers = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reviewers)

OWNERS = {
    "governance": {
        "owners": {
            "teams": {
                "platform": {"members": ["pat", "alex"]},
                "security": {"members": ["sam", "alex"]},
                "maintainers": {"members": ["pat"]},
            }
        }
    }
}

PATH_RULES = [
    {
        "id": "capability-contracts",
        "tier": "frozen",
        "override": {"team": "maintainers", "label": "policy:contract-change"},
    },
    {"id": "runtime-payload", "tier": "owned", "teams": ["platform"]},
]


def test_unsatisfied_owned_teams_are_collected() -> None:
    decision = {
        "required_approvals": [
            {"team": "platform", "satisfied": False},
            {"team": "security", "satisfied": True},
        ],
        "violations": [],
    }

    assert reviewers.teams_needed(decision, PATH_RULES) == ["platform"]


def test_frozen_violations_add_the_override_team() -> None:
    decision = {
        "required_approvals": [],
        "violations": [{"rule": "frozen/capability-contracts", "path": "agents/contracts.py"}],
    }

    assert reviewers.teams_needed(decision, PATH_RULES) == ["maintainers"]


def test_author_and_duplicates_are_dropped() -> None:
    logins = reviewers.reviewer_logins(
        ["platform", "security"],
        OWNERS,
        author="Alex",
    )

    assert logins == ["pat", "sam"]


def test_unknown_team_contributes_nobody() -> None:
    assert reviewers.reviewer_logins(["ghost"], OWNERS, author="pat") == []
