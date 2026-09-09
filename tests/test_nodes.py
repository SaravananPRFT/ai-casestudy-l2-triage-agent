"""
Node-level tests with LLM mocked out.
Tests that each node correctly reads/writes state fields.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.state import TriageState
from src.agent.nodes import route_node, audit_node


# ---------------------------------------------------------------------------
# route_node — pure Python, no mock needed
# ---------------------------------------------------------------------------

def make_state(**kwargs) -> TriageState:
    defaults: TriageState = {
        "order_id": "ORD-TEST",
        "customer_tier": "standard",
        "text_note": "Test note",
        "status": "new",
        "category": "delivery_delay",
        "confidence": "high",
        "flags": [],
    }
    defaults.update(kwargs)
    return defaults


def test_route_node_sets_priority_and_route():
    state = make_state(category="wrong_item", customer_tier="standard")
    result = route_node(state)
    assert result["priority"] == "HIGH"
    assert result["route"] == "marcus"


def test_route_node_premium_escalation():
    state = make_state(category="wrong_item", customer_tier="premium")
    result = route_node(state)
    assert result["priority"] == "URGENT"
    assert result["route"] == "priya"


def test_route_node_fraud_always_priya():
    state = make_state(category="fraud_alert", customer_tier="standard")
    result = route_node(state)
    assert result["route"] == "priya"
    assert result["priority"] == "URGENT"


def test_route_node_premium_address_change_composition():
    """address_change: base MEDIUM + premium bump = HIGH → priya (composition order matters)"""
    state = make_state(category="address_change", customer_tier="premium")
    result = route_node(state)
    assert result["priority"] == "HIGH"
    assert result["route"] == "priya"


def test_route_node_rationale_not_empty():
    state = make_state(category="refund_request", customer_tier="standard")
    result = route_node(state)
    assert result.get("rationale"), "rationale must not be empty"


def test_route_node_includes_flags_in_rationale():
    state = make_state(
        category="damaged",
        customer_tier="plus",
        flags=["multi_issue", "customer_directed"],
    )
    result = route_node(state)
    assert "multi_issue" in result["rationale"]
    assert "customer_directed" in result["rationale"]


# ---------------------------------------------------------------------------
# audit_node — writes to log, stamps processed_at
# ---------------------------------------------------------------------------

def test_audit_node_stamps_timestamp(tmp_path):
    state = make_state(
        category="refund_request",
        priority="MEDIUM",
        route="marcus",
        rationale="test rationale",
        draft_reply="Hi, we'll process your refund.",
    )
    with patch("src.agent.nodes.AUDIT_LOG", tmp_path / "test_audit.jsonl"):
        result = audit_node(state)
    assert "processed_at" in result
    assert result["processed_at"]


def test_audit_node_writes_jsonl(tmp_path):
    import json
    state = make_state(
        category="fraud_alert",
        priority="URGENT",
        route="priya",
        rationale="fraud always priya",
        escalation_summary="Fraud escalation for ORD-TEST",
    )
    log_path = tmp_path / "test_audit.jsonl"
    with patch("src.agent.nodes.AUDIT_LOG", log_path):
        audit_node(state)

    lines = log_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["order_id"] == "ORD-TEST"
    assert record["route"] == "priya"
    assert record["has_escalation"] is True
    assert record["has_draft"] is False


# ---------------------------------------------------------------------------
# classify_node — mock LLM structured output
# ---------------------------------------------------------------------------

def test_classify_node_happy_path():
    from src.agent.nodes import classify_node

    mock_output = MagicMock()
    mock_output.category = "wrong_item"
    mock_output.confidence = "high"
    mock_output.flags = []
    mock_output.rationale = "Customer received wrong color."

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_llm
    mock_llm.__or__ = lambda self, other: MagicMock(invoke=lambda x: mock_output)

    with patch("src.agent.nodes.get_llm", return_value=mock_llm):
        # Build a minimal chain mock
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = mock_output

        with patch("src.agent.nodes.ChatPromptTemplate") as mock_prompt_cls:
            mock_prompt = MagicMock()
            mock_prompt.__or__ = lambda self, other: mock_chain
            mock_prompt_cls.from_messages.return_value = mock_prompt

            state = make_state(text_note="I got the wrong item")
            result = classify_node(state)

    assert result["category"] == "wrong_item"
    assert result["confidence"] == "high"


def test_classify_node_invalid_category_fallback():
    """If LLM returns an unknown category, node falls back to product_question."""
    from src.agent.nodes import classify_node

    mock_output = MagicMock()
    mock_output.category = "completely_invalid_category"
    mock_output.confidence = "high"
    mock_output.flags = []
    mock_output.rationale = "Some rationale."

    mock_chain = MagicMock()
    mock_chain.invoke.return_value = mock_output

    mock_llm = MagicMock()
    with patch("src.agent.nodes.get_llm", return_value=mock_llm):
        with patch("src.agent.nodes.ChatPromptTemplate") as mock_prompt_cls:
            mock_prompt = MagicMock()
            mock_prompt.__or__ = lambda self, other: mock_chain
            mock_prompt_cls.from_messages.return_value = mock_prompt

            state = make_state(text_note="gibberish")
            result = classify_node(state)

    assert result["category"] == "product_question"
    assert "invalid_category_fallback" in result["flags"]
