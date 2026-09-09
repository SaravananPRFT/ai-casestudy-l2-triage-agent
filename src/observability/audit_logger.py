"""
Audit logger utilities — reads and summarises the JSONL audit log
written by audit_node.  Used by the Streamlit UI and the eval script.
"""
import json
from pathlib import Path
from typing import Iterator

DEFAULT_LOG = Path(__file__).resolve().parents[2] / "outputs" / "audit_log.jsonl"


def iter_records(log_path: Path = DEFAULT_LOG) -> Iterator[dict]:
    """Yield audit records from the JSONL log file."""
    if not log_path.exists():
        return
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def load_all(log_path: Path = DEFAULT_LOG) -> list[dict]:
    return list(iter_records(log_path))


def escalations(log_path: Path = DEFAULT_LOG) -> list[dict]:
    return [r for r in iter_records(log_path) if r.get("route") == "priya"]


def drafts(log_path: Path = DEFAULT_LOG) -> list[dict]:
    return [r for r in iter_records(log_path) if r.get("route") == "marcus"]


def summary_stats(log_path: Path = DEFAULT_LOG) -> dict:
    records = load_all(log_path)
    if not records:
        return {}

    from collections import Counter
    return {
        "total": len(records),
        "by_route": dict(Counter(r.get("route") for r in records)),
        "by_category": dict(Counter(r.get("category") for r in records)),
        "by_priority": dict(Counter(r.get("priority") for r in records)),
        "flagged": sum(1 for r in records if r.get("flags")),
    }
