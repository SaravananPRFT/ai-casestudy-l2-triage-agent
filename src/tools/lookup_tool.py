"""
Policy lookup tool — exposed as a callable LangChain tool so the agent can
query the escalation policy by category. A new category added to the policy
table is automatically available here without graph changes.
"""
from langchain_core.tools import tool
from src.agent.policy_engine import BASE_PRIORITY, VALID_CATEGORIES, PRIORITY_LADDER


@tool
def lookup_policy(category: str) -> str:
    """
    Look up the triage policy for a given issue category.
    Returns base priority, premium bump result, and routing rule.
    """
    cat = category.lower().strip()
    if cat not in VALID_CATEGORIES:
        valid = ", ".join(sorted(VALID_CATEGORIES))
        return f"Unknown category '{cat}'. Valid categories: {valid}"

    base = BASE_PRIORITY[cat]
    idx = PRIORITY_LADDER.index(base)
    premium_result = PRIORITY_LADDER[min(idx + 1, len(PRIORITY_LADDER) - 1)]

    if cat in ("fraud_alert", "payment_issue"):
        route_rule = "always escalate to Priya (money-movement/fraud)"
    elif premium_result in ("HIGH", "URGENT"):
        route_rule = (
            f"standard/plus → Marcus; "
            f"premium → Priya (premium bump gives {premium_result})"
        )
    else:
        route_rule = "Marcus (draft reply) for all tiers"

    return (
        f"Category: {cat}\n"
        f"Base priority: {base}\n"
        f"Premium bump result: {premium_result}\n"
        f"Routing: {route_rule}"
    )
