"""
Entry point: load orders_queue.csv, run every ticket through the graph,
print a triage table, and write full results to outputs/triage_results.json.

Usage:
    python run_triage.py                  # process full queue
    python run_triage.py --limit 5        # first N tickets (for testing)
    python run_triage.py --order ORD-10015  # single ticket
"""
import argparse
import csv
import json
import sys
from pathlib import Path

# Windows console UTF-8 fix
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# Clear audit log at start of a full run so it doesn't accumulate across runs
AUDIT_LOG = OUTPUT_DIR / "audit_log.jsonl"


def load_queue(queue_path: Path) -> list[dict]:
    with open(queue_path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def run_all(tickets: list[dict]) -> list[dict]:
    from src.agent.graph import graph

    results = []
    for i, ticket in enumerate(tickets, 1):
        print(f"  [{i:02d}/{len(tickets)}] {ticket['order_id']} ...", end=" ", flush=True)
        try:
            final_state = graph.invoke({
                "order_id": ticket["order_id"],
                "customer_tier": ticket["customer_tier"],
                "text_note": ticket["text_note"],
                "status": ticket.get("status", ""),
            })
            results.append(final_state)
            route_label = "-> PRIYA (escalate)" if final_state.get("route") == "priya" else "-> Marcus (draft)"
            print(f"{final_state.get('category', '?'):20} {final_state.get('priority', '?'):6} {route_label}")
        except Exception as exc:
            print(f"ERROR: {exc}")
            results.append({
                "order_id": ticket["order_id"],
                "customer_tier": ticket["customer_tier"],
                "text_note": ticket["text_note"],
                "error": str(exc),
            })

    return results


def print_summary_table(results: list[dict]) -> None:
    print("\n" + "=" * 90)
    print(f"{'ORDER_ID':<12} {'TIER':<10} {'CATEGORY':<20} {'PRI':<8} {'ROUTE':<8} RATIONALE")
    print("=" * 90)
    for r in results:
        if "error" in r:
            print(f"{r['order_id']:<12} ERROR: {r['error']}")
            continue
        rationale_short = (r.get("rationale") or "")[:45]
        print(
            f"{r.get('order_id',''):<12} "
            f"{r.get('customer_tier',''):<10} "
            f"{r.get('category',''):<20} "
            f"{r.get('priority',''):<8} "
            f"{r.get('route',''):<8} "
            f"{rationale_short}"
        )
    print("=" * 90)

    priya = sum(1 for r in results if r.get("route") == "priya")
    marcus = sum(1 for r in results if r.get("route") == "marcus")
    errors = sum(1 for r in results if "error" in r)
    print(f"\nTotal: {len(results)} | Escalated->Priya: {priya} | Draft->Marcus: {marcus} | Errors: {errors}")


def main():
    parser = argparse.ArgumentParser(description="Run Order Triage Agent on queue")
    parser.add_argument("--limit", type=int, default=None, help="Process only first N tickets")
    parser.add_argument("--order", type=str, default=None, help="Process single order ID")
    parser.add_argument("--no-clear-log", action="store_true", help="Append to existing audit log")
    args = parser.parse_args()

    # Clear audit log unless appending
    if not args.no_clear_log and AUDIT_LOG.exists():
        AUDIT_LOG.unlink()

    tickets = load_queue(DATA_DIR / "orders_queue.csv")

    if args.order:
        tickets = [t for t in tickets if t["order_id"] == args.order]
        if not tickets:
            print(f"Order {args.order} not found in queue.")
            sys.exit(1)
    elif args.limit:
        tickets = tickets[: args.limit]

    print(f"\nProcessing {len(tickets)} tickets...\n")
    results = run_all(tickets)

    print_summary_table(results)

    out_path = OUTPUT_DIR / "triage_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nFull results saved to: {out_path}")
    print(f"Audit log:             {AUDIT_LOG}")


if __name__ == "__main__":
    main()
