"""
Pure-Python triage policy engine.  No LLM calls — deterministic, fully unit-testable.
Adding a new category or tier rule only requires editing the tables/rules here;
the graph does not need to change.
"""

VALID_CATEGORIES: frozenset[str] = frozenset([
    "delivery_delay",
    "wrong_item",
    "damaged",
    "refund_request",
    "payment_issue",
    "address_change",
    "cancel_request",
    "product_question",
    "subscription",
    "fraud_alert",
])

# Base priority per issue category (from personas.md, Table 1)
BASE_PRIORITY: dict[str, str] = {
    "fraud_alert":      "URGENT",
    "payment_issue":    "URGENT",
    "damaged":          "HIGH",
    "wrong_item":       "HIGH",
    "delivery_delay":   "MEDIUM",
    "refund_request":   "MEDIUM",
    "address_change":   "MEDIUM",
    "cancel_request":   "MEDIUM",
    "product_question": "LOW",
    "subscription":     "LOW",
}

PRIORITY_LADDER: list[str] = ["LOW", "MEDIUM", "HIGH", "URGENT"]


def bump_priority(priority: str) -> str:
    """Move priority one rung up the ladder, capped at URGENT."""
    idx = PRIORITY_LADDER.index(priority)
    return PRIORITY_LADDER[min(idx + 1, len(PRIORITY_LADDER) - 1)]


def compute_priority(category: str, customer_tier: str) -> tuple[str, str]:
    """
    Returns (final_priority, rationale_fragment).

    Compose order (must be applied in this exact sequence):
      1. Look up base priority from category table.
      2. If tier == 'premium', bump once (capped at URGENT).
      Standard and plus tiers keep the base priority unchanged.
    """
    base = BASE_PRIORITY[category]

    if customer_tier == "premium":
        bumped = bump_priority(base)
        if bumped != base:
            note = f"premium-tier bump: {base}→{bumped}"
        else:
            note = f"premium bump no-op (already {base})"
        return bumped, note

    return base, f"base priority for {category} ({customer_tier} tier, no bump)"


def compute_route(category: str, priority: str, customer_tier: str) -> tuple[str, str]:
    """
    Returns (route, rationale_fragment).

    Routing rules applied in documented order — ORDER IS CRITICAL:
      Rule 1: fraud_alert or payment_issue → always priya (money-movement/fraud).
      Rule 2: premium tier AND priority is HIGH or URGENT → priya.
      Rule 3: everything else → marcus (draft reply).

    Rule 1 is evaluated BEFORE Rule 2.  Changing this order would not affect
    fraud/payment (already URGENT), but Rule 1 being first makes the logic
    explicit and prevents any accidental interaction with Rule 2.
    """
    if category in ("fraud_alert", "payment_issue"):
        return "priya", f"{category} → always escalate to Priya (money-movement/fraud rule)"

    if customer_tier == "premium" and priority in ("HIGH", "URGENT"):
        return "priya", f"premium customer with {priority} priority → escalate to Priya"

    return "marcus", "routed to Marcus for draft reply"


def triage(category: str, customer_tier: str) -> tuple[str, str, str]:
    """
    One-call convenience: returns (priority, route, full_rationale).
    Used by route_node and directly in unit tests.
    """
    priority, p_note = compute_priority(category, customer_tier)
    route, r_note = compute_route(category, priority, customer_tier)
    rationale = f"[classify] {category} | [priority] {p_note} | [route] {r_note}"
    return priority, route, rationale


def resolve_multi_issue(categories: list[str], customer_tier: str) -> tuple[str, str]:
    """
    Design rule for tickets describing more than one problem (policy is silent on this):
    Select the category with the highest resulting priority after the premium bump.
    On a tie, prefer the category that appears first in the note (list order).
    Documents the rule consistently; applied to every multi-issue ticket.
    """
    best_cat = categories[0]
    best_priority, _ = compute_priority(best_cat, customer_tier)

    for cat in categories[1:]:
        p, _ = compute_priority(cat, customer_tier)
        if PRIORITY_LADDER.index(p) > PRIORITY_LADDER.index(best_priority):
            best_cat = cat
            best_priority = p

    return best_cat, best_priority
