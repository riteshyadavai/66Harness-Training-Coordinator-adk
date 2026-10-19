"""Deterministic training eligibility helpers.

Supply approved rule values from governed configuration. Do not ask an
LLM to calculate dates, tenure, eligibility, or completion windows.
"""

from __future__ import annotations

from datetime import date
from typing import Literal, TypedDict


EligibilityStatus = Literal["eligible", "ineligible", "hold_next_cycle"]


class EligibilityResult(TypedDict):
    status: EligibilityStatus
    tenure_days: int
    reason: str


def compute_eligibility(
    *,
    start_date: date,
    as_of_date: date,
    minimum_tenure_days: int,
    maximum_tenure_days: int,
    cohort_open: bool,
    hold_when_cohort_closed: bool,
) -> EligibilityResult:
    """Apply approved numeric rules without model arithmetic."""
    tenure_days = (as_of_date - start_date).days
    if tenure_days < 0:
        return {
            "status": "ineligible",
            "tenure_days": tenure_days,
            "reason": "start_date_is_after_as_of_date",
        }
    if tenure_days < minimum_tenure_days:
        return {
            "status": "ineligible",
            "tenure_days": tenure_days,
            "reason": "below_minimum_tenure",
        }
    if tenure_days > maximum_tenure_days:
        return {
            "status": "ineligible",
            "tenure_days": tenure_days,
            "reason": "above_maximum_tenure",
        }
    if not cohort_open and hold_when_cohort_closed:
        return {
            "status": "hold_next_cycle",
            "tenure_days": tenure_days,
            "reason": "cohort_closed",
        }
    return {
        "status": "eligible",
        "tenure_days": tenure_days,
        "reason": "within_approved_window",
    }
