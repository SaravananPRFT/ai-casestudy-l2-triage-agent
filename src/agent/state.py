from typing import TypedDict, Optional


class TriageState(TypedDict, total=False):
    # Input fields (from CSV)
    order_id: str
    customer_tier: str          # standard | plus | premium
    text_note: str
    status: str

    # Agent outputs
    category: str               # one of 10 valid issue types
    confidence: str             # high | medium | low
    priority: str               # LOW | MEDIUM | HIGH | URGENT
    route: str                  # marcus | priya
    draft_reply: Optional[str]  # set when route == marcus
    escalation_summary: Optional[str]  # set when route == priya
    rationale: str              # one-line audit trail entry
    flags: list                 # ["multi_issue", "customer_directed", "low_confidence"]

    # Metadata
    processed_at: str           # ISO timestamp
