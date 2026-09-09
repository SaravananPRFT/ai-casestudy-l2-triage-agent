"""
LangGraph StateGraph wiring.

Graph shape:
  classify → route → [conditional] → draft  → audit → END
                                   ↘ escalate → audit → END

Adding a new category or route target only requires:
  1. Updating policy_engine.py tables.
  2. Adding a new node + edge here if a new action type is needed.
  The classify/route/audit nodes do not change.
"""
from langgraph.graph import StateGraph, END

from src.agent.state import TriageState
from src.agent.nodes import classify_node, route_node, draft_node, escalate_node, audit_node


def _route_selector(state: TriageState) -> str:
    """Conditional edge: branch on the route field set by route_node."""
    return state.get("route", "marcus")


def build_graph() -> StateGraph:
    workflow = StateGraph(TriageState)

    workflow.add_node("classify", classify_node)
    workflow.add_node("route", route_node)
    workflow.add_node("draft", draft_node)
    workflow.add_node("escalate", escalate_node)
    workflow.add_node("audit", audit_node)

    workflow.set_entry_point("classify")

    workflow.add_edge("classify", "route")

    workflow.add_conditional_edges(
        "route",
        _route_selector,
        {"marcus": "draft", "priya": "escalate"},
    )

    workflow.add_edge("draft", "audit")
    workflow.add_edge("escalate", "audit")
    workflow.add_edge("audit", END)

    return workflow.compile()


# Module-level compiled graph — import this for use in run_triage.py and tests
graph = build_graph()
