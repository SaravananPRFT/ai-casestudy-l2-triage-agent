"""
Evaluation script: run the agent on orders_dev_labeled.csv, compare
predicted category/priority/route against ground truth, and report
per-category accuracy.

Usage:
    python eval/evaluate.py
    python eval/evaluate.py --output eval/eval_results.json
"""
import argparse
import csv
import json
import sys
from pathlib import Path
from collections import defaultdict

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def load_labeled(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def run_agent_on(ticket: dict) -> dict:
    from src.agent.graph import graph
    return graph.invoke({
        "order_id": ticket["order_id"],
        "customer_tier": ticket["customer_tier"],
        "text_note": ticket["text_note"],
        "status": ticket.get("status", ""),
    })


def evaluate(labeled: list[dict]) -> dict:
    results = []
    correct_cat = correct_pri = correct_route = 0

    for ticket in labeled:
        print(f"  Evaluating {ticket['order_id']} ...", end=" ", flush=True)
        predicted = run_agent_on(ticket)

        pred_cat   = (predicted.get("category") or "").lower()
        pred_pri   = (predicted.get("priority") or "").lower()
        pred_route = (predicted.get("route") or "").lower()

        true_cat   = ticket["issue_type"].lower()
        true_pri   = ticket["priority"].lower()
        true_route = ticket["route"].lower()

        cat_ok   = pred_cat == true_cat
        pri_ok   = pred_pri == true_pri
        route_ok = pred_route == true_route

        if cat_ok:   correct_cat += 1
        if pri_ok:   correct_pri += 1
        if route_ok: correct_route += 1

        status = "✓" if (cat_ok and pri_ok and route_ok) else "✗"
        print(f"{status}  cat={'OK' if cat_ok else f'FAIL({pred_cat})'} pri={'OK' if pri_ok else f'FAIL({pred_pri})'} route={'OK' if route_ok else f'FAIL({pred_route})'}")

        results.append({
            "order_id":    ticket["order_id"],
            "tier":        ticket["customer_tier"],
            "text_note":   ticket["text_note"],
            "true_category":  true_cat,
            "pred_category":  pred_cat,
            "cat_correct":    cat_ok,
            "true_priority":  true_pri,
            "pred_priority":  pred_pri,
            "pri_correct":    pri_ok,
            "true_route":     true_route,
            "pred_route":     pred_route,
            "route_correct":  route_ok,
            "rationale":      predicted.get("rationale", ""),
            "flags":          predicted.get("flags", []),
        })

    n = len(labeled)
    # Per-category accuracy
    per_cat: dict[str, dict] = defaultdict(lambda: {"total": 0, "correct": 0})
    for r in results:
        per_cat[r["true_category"]]["total"] += 1
        if r["cat_correct"]:
            per_cat[r["true_category"]]["correct"] += 1

    per_cat_acc = {
        cat: f"{v['correct']}/{v['total']} ({100*v['correct']//v['total']}%)"
        for cat, v in sorted(per_cat.items())
    }

    summary = {
        "n": n,
        "category_accuracy":  f"{correct_cat}/{n} ({100*correct_cat//n}%)",
        "priority_accuracy":  f"{correct_pri}/{n} ({100*correct_pri//n}%)",
        "route_accuracy":     f"{correct_route}/{n} ({100*correct_route//n}%)",
        "per_category":       per_cat_acc,
        "details":            results,
    }
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(OUTPUT_DIR / "eval_results.json"))
    args = parser.parse_args()

    labeled = load_labeled(DATA_DIR / "orders_dev_labeled.csv")
    print(f"\nRunning evaluation on {len(labeled)} labeled tickets...\n")

    summary = evaluate(labeled)

    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    print(f"Category accuracy : {summary['category_accuracy']}")
    print(f"Priority accuracy : {summary['priority_accuracy']}")
    print(f"Route accuracy    : {summary['route_accuracy']}")
    print("\nPer-category breakdown:")
    for cat, acc in summary["per_category"].items():
        print(f"  {cat:<20} {acc}")

    # Failures
    failures = [r for r in summary["details"] if not r["cat_correct"]]
    if failures:
        print(f"\nClassification failures ({len(failures)}):")
        for f in failures:
            print(f"  {f['order_id']}: true={f['true_category']}, pred={f['pred_category']}")
            print(f"    note: {f['text_note'][:70]}")

    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    print(f"\nDetailed results: {args.output}")


if __name__ == "__main__":
    main()
