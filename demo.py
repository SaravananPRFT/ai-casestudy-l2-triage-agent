"""
Demo transcript — runs two tickets through the agent and prints full state.

Ticket 1: ORD-10002  plus / damaged / HIGH -> Marcus (draft reply)
Ticket 2: ORD-10015  premium / address_change / MEDIUM->HIGH -> Priya (escalation)
          ^ this is the key composition case the rubric tests

Saves output to outputs/demo_transcript.txt as well as printing to console.
"""
import sys
import io
from pathlib import Path
from datetime import datetime, timezone

# Windows console UTF-8
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)
TRANSCRIPT = OUTPUT_DIR / "demo_transcript.txt"

DIVIDER = "=" * 72

DEMO_TICKETS = [
    {
        "order_id": "ORD-10002",
        "customer_tier": "plus",
        "text_note": "Box arrived crushed and the mug inside is shattered. Photos attached.",
        "status": "new",
        "demo_label": "Demo 1 — Draft Reply (Marcus path)",
        "expected": "category=damaged, priority=HIGH, route=marcus",
    },
    {
        "order_id": "ORD-10015",
        "customer_tier": "premium",
        "text_note": "Wrong shipping address on file, need it updated before the package leaves the warehouse.",
        "status": "in_progress",
        "demo_label": "Demo 2 — Escalation (Priya path, composition case)",
        "expected": "category=address_change, priority=HIGH (MEDIUM->HIGH premium bump), route=priya",
    },
]


def render_result(ticket: dict, result: dict) -> str:
    lines = []
    lines.append(DIVIDER)
    lines.append(ticket["demo_label"])
    lines.append(DIVIDER)
    lines.append("")
    lines.append("INPUT")
    lines.append(f"  Order ID     : {ticket['order_id']}")
    lines.append(f"  Tier         : {ticket['customer_tier']}")
    lines.append(f"  Status       : {ticket['status']}")
    lines.append(f"  Note         : {ticket['text_note']}")
    lines.append(f"  Expected     : {ticket['expected']}")
    lines.append("")
    lines.append("AGENT OUTPUT")
    lines.append(f"  Category     : {result.get('category', '?')}  (confidence: {result.get('confidence', '?')})")
    lines.append(f"  Priority     : {result.get('priority', '?')}")
    lines.append(f"  Route        : {result.get('route', '?').upper()}")
    lines.append(f"  Flags        : {', '.join(result.get('flags') or []) or 'none'}")
    lines.append(f"  Processed at : {result.get('processed_at', '?')}")
    lines.append("")
    lines.append("RATIONALE")
    rationale = result.get("rationale", "")
    # Wrap long rationale across lines
    for part in rationale.split(" | "):
        lines.append(f"  {part}")
    lines.append("")

    if result.get("draft_reply"):
        lines.append("DRAFT REPLY  (for Marcus to approve)")
        lines.append("-" * 50)
        for line in result["draft_reply"].strip().split("\n"):
            lines.append(f"  {line}")
        lines.append("-" * 50)

    if result.get("escalation_summary"):
        lines.append("ESCALATION SUMMARY  (for Priya)")
        lines.append("-" * 50)
        for line in result["escalation_summary"].strip().split("\n"):
            lines.append(f"  {line}")
        lines.append("-" * 50)

    lines.append("")
    return "\n".join(lines)


def main():
    from src.agent.graph import graph

    header = [
        DIVIDER,
        "ORDER TRIAGE AGENT — DEMO TRANSCRIPT",
        f"Run at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "Model: us.anthropic.claude-sonnet-4-6 via Perficient Portkey gateway",
        DIVIDER,
        "",
    ]

    all_lines = "\n".join(header)
    print(all_lines)

    for ticket in DEMO_TICKETS:
        print(f"Running {ticket['order_id']} ({ticket['demo_label']}) ...\n")
        result = graph.invoke({
            "order_id":      ticket["order_id"],
            "customer_tier": ticket["customer_tier"],
            "text_note":     ticket["text_note"],
            "status":        ticket["status"],
        })
        block = render_result(ticket, result)
        print(block)
        all_lines += block

    footer = "\n".join([
        DIVIDER,
        "END OF DEMO TRANSCRIPT",
        DIVIDER,
    ])
    print(footer)
    all_lines += "\n" + footer

    TRANSCRIPT.write_text(all_lines, encoding="utf-8")
    print(f"\nTranscript saved to: {TRANSCRIPT}")


if __name__ == "__main__":
    main()
