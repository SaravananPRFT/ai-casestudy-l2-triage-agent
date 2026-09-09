"""
Reply drafting tool — exposed as a callable LangChain tool so the draft step
is independently testable and reusable outside the graph.
"""
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate


DRAFT_SYSTEM = """\
You are a support reply writer for NorthPeak Commerce, a mid-market online retailer.
Write a short, warm, professional reply on behalf of the support team.

Rules (strictly enforced):
- Acknowledge the customer's issue clearly.
- State the concrete next step NorthPeak will take (or ask for information needed).
- NEVER promise a refund, replacement, or credit unless the issue type explicitly
  authorises it (wrong_item and damaged authorise replacement/refund; refund_request
  authorises processing a refund review; all others: do not promise money back).
- Do not use hollow phrases like "I apologize for the inconvenience".
- Keep it under 80 words.
- Do not mention internal systems, priorities, or routing.
"""

DRAFT_HUMAN = """\
Order ID: {order_id}
Issue category: {category}
Customer note: {text_note}

Write the reply now.
"""


@tool
def draft_reply(order_id: str, category: str, text_note: str, llm=None) -> str:
    """
    Draft a short, on-brand customer reply for Marcus to approve.
    The LLM is injected so the tool is testable with a mock.
    """
    from src.llm.client import get_llm
    model = llm or get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", DRAFT_SYSTEM),
        ("human", DRAFT_HUMAN),
    ])
    chain = prompt | model
    result = chain.invoke({
        "order_id": order_id,
        "category": category,
        "text_note": text_note,
    })
    return result.content.strip()
