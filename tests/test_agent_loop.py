"""
Full agent loop tests using pytest-asyncio.
Nodes are mocked at the graph level so tests run without API keys.
Tests verify: graph wiring, conditional routing, and failure propagation.
"""
import pytest
import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent))

pytestmark = pytest.mark.asyncio


def _run_graph(ticket: dict, mock_classify_out: dict, mock_action_out: dict) -> dict:
    """
    Build a fresh graph and invoke it with mocked nodes.
    mock_classify_out: dict returned by classify_node
    mock_action_out: dict returned by draft_node or escalate_node
    """
    from src.agent.graph import build_graph

    def mock_classify(state):
        return mock_classify_out

    def mock_draft(state):
        return mock_action_out

    def mock_escalate(state):
        return mock_action_out

    def mock_audit(state):
        return {"processed_at": "2026-01-01T00:00:00+00:00"}

    with patch("src.agent.graph.classify_node", side_effect=mock_classify), \
         patch("src.agent.graph.draft_node",    side_effect=mock_draft), \
         patch("src.agent.graph.escalate_node", side_effect=mock_escalate), \
         patch("src.agent.graph.audit_node",    side_effect=mock_audit):
        g = build_graph()
        return g.invoke(ticket)


# ---------------------------------------------------------------------------
# Test: standard + damaged → draft path (marcus)
# ---------------------------------------------------------------------------

async def test_graph_routes_to_marcus():
    ticket = {
        "order_id": "ORD-TEST-01",
        "customer_tier": "standard",
        "text_note": "My order arrived damaged.",
        "status": "new",
    }
    result = _run_graph(
        ticket,
        mock_classify_out={"category": "damaged", "confidence": "high", "flags": []},
        mock_action_out={"draft_reply": "We'll send a replacement.", "escalation_summary": None},
    )
    assert result["category"] == "damaged"
    assert result["priority"] == "HIGH"
    assert result["route"] == "marcus"
    assert result.get("draft_reply") == "We'll send a replacement."


# ---------------------------------------------------------------------------
# Test: premium + wrong_item → escalation path (priya)
# ---------------------------------------------------------------------------

async def test_graph_routes_premium_wrong_item_to_priya():
    ticket = {
        "order_id": "ORD-TEST-02",
        "customer_tier": "premium",
        "text_note": "Wrong item received.",
        "status": "new",
    }
    result = _run_graph(
        ticket,
        mock_classify_out={"category": "wrong_item", "confidence": "high", "flags": []},
        mock_action_out={"escalation_summary": "Premium wrong_item escalation.", "draft_reply": None},
    )
    assert result["priority"] == "URGENT"   # HIGH bumped to URGENT for premium
    assert result["route"] == "priya"
    assert result.get("escalation_summary") == "Premium wrong_item escalation."
    assert result.get("draft_reply") is None


# ---------------------------------------------------------------------------
# Test: fraud_alert always goes to priya, regardless of tier
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("tier", ["standard", "plus", "premium"])
async def test_fraud_always_routes_to_priya(tier):
    ticket = {
        "order_id": f"ORD-FRAUD-{tier}",
        "customer_tier": tier,
        "text_note": "Unauthorised charge on my account.",
        "status": "new",
    }
    result = _run_graph(
        ticket,
        mock_classify_out={"category": "fraud_alert", "confidence": "high", "flags": []},
        mock_action_out={"escalation_summary": "Fraud escalation.", "draft_reply": None},
    )
    assert result["route"] == "priya", f"fraud_alert tier={tier} must go to priya"
    assert result["priority"] == "URGENT"


# ---------------------------------------------------------------------------
# Test: premium + address_change (key composition case) → priya
# ---------------------------------------------------------------------------

async def test_premium_address_change_escalates():
    """address_change: base MEDIUM + premium bump = HIGH → priya (not marcus)."""
    ticket = {
        "order_id": "ORD-TEST-COMP",
        "customer_tier": "premium",
        "text_note": "Please update my shipping address.",
        "status": "new",
    }
    result = _run_graph(
        ticket,
        mock_classify_out={"category": "address_change", "confidence": "high", "flags": []},
        mock_action_out={"escalation_summary": "Premium high priority escalation.", "draft_reply": None},
    )
    assert result["priority"] == "HIGH"
    assert result["route"] == "priya"


# ---------------------------------------------------------------------------
# Test: premium + product_question → marcus (LOW→MEDIUM, below HIGH threshold)
# ---------------------------------------------------------------------------

async def test_premium_product_question_goes_to_marcus():
    ticket = {
        "order_id": "ORD-TEST-PQ",
        "customer_tier": "premium",
        "text_note": "Does this jacket run true to size?",
        "status": "new",
    }
    result = _run_graph(
        ticket,
        mock_classify_out={"category": "product_question", "confidence": "high", "flags": []},
        mock_action_out={"draft_reply": "Yes, it runs true to size.", "escalation_summary": None},
    )
    assert result["priority"] == "MEDIUM"  # LOW → MEDIUM (premium bump)
    assert result["route"] == "marcus"


# ---------------------------------------------------------------------------
# Test: audit node receives processed_at
# ---------------------------------------------------------------------------

async def test_audit_node_is_called_and_stamps_timestamp():
    ticket = {
        "order_id": "ORD-AUDIT",
        "customer_tier": "standard",
        "text_note": "Cancel my order.",
        "status": "new",
    }
    result = _run_graph(
        ticket,
        mock_classify_out={"category": "cancel_request", "confidence": "high", "flags": []},
        mock_action_out={"draft_reply": "Cancellation processed.", "escalation_summary": None},
    )
    assert "processed_at" in result
    assert result["processed_at"]


# ---------------------------------------------------------------------------
# Test: failure in classify_node propagates out of graph cleanly
# ---------------------------------------------------------------------------

async def test_classify_failure_propagates():
    ticket = {
        "order_id": "ORD-FAIL",
        "customer_tier": "standard",
        "text_note": "Test.",
        "status": "new",
    }

    def failing_classify(state):
        raise RuntimeError("LLM API timeout")

    def mock_audit(state):
        return {"processed_at": "2026-01-01T00:00:00+00:00"}

    from src.agent.graph import build_graph
    with patch("src.agent.graph.classify_node", side_effect=failing_classify), \
         patch("src.agent.graph.audit_node", side_effect=mock_audit):
        g = build_graph()
        with pytest.raises(Exception, match="LLM API timeout"):
            g.invoke(ticket)
