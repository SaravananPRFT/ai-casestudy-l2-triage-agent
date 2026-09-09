"""
Unit tests for policy_engine.py — pure Python, no LLM calls, no network.
These are the authoritative tests for the routing rules.
"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.policy_engine import (
    compute_priority,
    compute_route,
    triage,
    bump_priority,
    resolve_multi_issue,
    PRIORITY_LADDER,
    VALID_CATEGORIES,
)


# ---------------------------------------------------------------------------
# bump_priority
# ---------------------------------------------------------------------------

def test_bump_low():
    assert bump_priority("LOW") == "MEDIUM"

def test_bump_medium():
    assert bump_priority("MEDIUM") == "HIGH"

def test_bump_high():
    assert bump_priority("HIGH") == "URGENT"

def test_bump_urgent_stays_urgent():
    assert bump_priority("URGENT") == "URGENT"


# ---------------------------------------------------------------------------
# compute_priority — base priorities for standard/plus tier
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("category,expected", [
    ("fraud_alert",      "URGENT"),
    ("payment_issue",    "URGENT"),
    ("damaged",          "HIGH"),
    ("wrong_item",       "HIGH"),
    ("delivery_delay",   "MEDIUM"),
    ("refund_request",   "MEDIUM"),
    ("address_change",   "MEDIUM"),
    ("cancel_request",   "MEDIUM"),
    ("product_question", "LOW"),
    ("subscription",     "LOW"),
])
def test_base_priority_standard(category, expected):
    priority, _ = compute_priority(category, "standard")
    assert priority == expected

def test_base_priority_plus_same_as_standard():
    for cat in VALID_CATEGORIES:
        p_std, _ = compute_priority(cat, "standard")
        p_plus, _ = compute_priority(cat, "plus")
        assert p_std == p_plus, f"{cat}: plus should equal standard"


# ---------------------------------------------------------------------------
# compute_priority — premium tier bump
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("category,expected_after_bump", [
    ("product_question", "MEDIUM"),  # LOW → MEDIUM
    ("subscription",     "MEDIUM"),  # LOW → MEDIUM
    ("delivery_delay",   "HIGH"),    # MEDIUM → HIGH
    ("refund_request",   "HIGH"),    # MEDIUM → HIGH
    ("address_change",   "HIGH"),    # MEDIUM → HIGH
    ("cancel_request",   "HIGH"),    # MEDIUM → HIGH
    ("damaged",          "URGENT"),  # HIGH → URGENT
    ("wrong_item",       "URGENT"),  # HIGH → URGENT
    ("fraud_alert",      "URGENT"),  # already URGENT — bump is no-op
    ("payment_issue",    "URGENT"),  # already URGENT — bump is no-op
])
def test_premium_bump(category, expected_after_bump):
    priority, _ = compute_priority(category, "premium")
    assert priority == expected_after_bump, f"{category}: expected {expected_after_bump}"


# ---------------------------------------------------------------------------
# compute_route — rule 1: fraud & payment always go to Priya
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("tier", ["standard", "plus", "premium"])
def test_fraud_always_priya(tier):
    route, _ = compute_route("fraud_alert", "URGENT", tier)
    assert route == "priya"

@pytest.mark.parametrize("tier", ["standard", "plus", "premium"])
def test_payment_always_priya(tier):
    route, _ = compute_route("payment_issue", "URGENT", tier)
    assert route == "priya"


# ---------------------------------------------------------------------------
# compute_route — rule 2: premium + HIGH/URGENT → Priya
# ---------------------------------------------------------------------------

def test_premium_high_goes_priya():
    route, _ = compute_route("damaged", "HIGH", "premium")
    assert route == "priya"

def test_premium_urgent_goes_priya():
    route, _ = compute_route("wrong_item", "URGENT", "premium")
    assert route == "priya"

def test_premium_medium_goes_marcus():
    route, _ = compute_route("delivery_delay", "MEDIUM", "premium")
    assert route == "marcus"

def test_premium_low_goes_marcus():
    route, _ = compute_route("product_question", "LOW", "premium")
    assert route == "marcus"


# ---------------------------------------------------------------------------
# triage — full composition tests (the key correctness cases)
# ---------------------------------------------------------------------------

def test_triage_standard_wrong_item():
    """standard + wrong_item → HIGH, marcus (HIGH doesn't trigger rule 2 without premium)"""
    priority, route, _ = triage("wrong_item", "standard")
    assert priority == "HIGH"
    assert route == "marcus"

def test_triage_premium_wrong_item():
    """premium + wrong_item → HIGH→URGENT, priya (premium bump + rule 2)"""
    priority, route, _ = triage("wrong_item", "premium")
    assert priority == "URGENT"
    assert route == "priya"

def test_triage_premium_address_change():
    """KEY COMPOSITION CASE: premium + address_change → MEDIUM→HIGH, priya.
    If bump is applied after routing check, route would be wrong (marcus).
    Order: base=MEDIUM, bump to HIGH, then route HIGH+premium → priya."""
    priority, route, _ = triage("address_change", "premium")
    assert priority == "HIGH"
    assert route == "priya"

def test_triage_premium_product_question():
    """premium + product_question → LOW→MEDIUM, marcus (MEDIUM is below HIGH threshold)"""
    priority, route, _ = triage("product_question", "premium")
    assert priority == "MEDIUM"
    assert route == "marcus"

def test_triage_plus_damaged():
    """plus + damaged → HIGH, marcus (plus gets no bump, rule 2 is premium-only)"""
    priority, route, _ = triage("damaged", "plus")
    assert priority == "HIGH"
    assert route == "marcus"

def test_triage_fraud_premium():
    """fraud_alert is already URGENT — premium bump is no-op, still priya via rule 1"""
    priority, route, _ = triage("fraud_alert", "premium")
    assert priority == "URGENT"
    assert route == "priya"

def test_triage_standard_subscription():
    priority, route, _ = triage("subscription", "standard")
    assert priority == "LOW"
    assert route == "marcus"


# ---------------------------------------------------------------------------
# resolve_multi_issue — design rule for multi-issue tickets
# ---------------------------------------------------------------------------

def test_multi_issue_picks_highest():
    cat, pri = resolve_multi_issue(["subscription", "damaged"], "standard")
    assert cat == "damaged"
    assert pri == "HIGH"

def test_multi_issue_tie_picks_first():
    """On a priority tie, first-listed category wins."""
    cat, _ = resolve_multi_issue(["delivery_delay", "refund_request"], "standard")
    assert cat == "delivery_delay"

def test_multi_issue_premium_considers_bumped_priority():
    """premium: cancel_request(MEDIUM→HIGH) vs product_question(LOW→MEDIUM) → cancel_request wins"""
    cat, pri = resolve_multi_issue(["product_question", "cancel_request"], "premium")
    assert cat == "cancel_request"
    assert pri == "HIGH"
