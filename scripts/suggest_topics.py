#!/usr/bin/env python3
"""Tops up the pending topic-suggestion queue from content/topic_bank.json,
run weekly. Never suggested topics come first; once the whole bank has been
shown at least once, the least-recently-suggested topics resurface.

Usage:
    python3 scripts/suggest_topics.py
    python3 scripts/suggest_topics.py --target-pending 8
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import topics  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target-pending", type=int, default=6,
        help="Keep at least this many topic suggestions awaiting a decision.",
    )
    args = parser.parse_args()

    bank = topics.load_bank()
    suggestions = topics.load_suggestions()

    pending_ids = {s["id"] for s in suggestions if s["status"] == "pending"}
    if len(pending_ids) >= args.target_pending:
        print(f"{len(pending_ids)} topic(s) already pending review — skipping.")
        return

    last_suggested = {}
    for s in suggestions:
        last_suggested[s["id"]] = max(last_suggested.get(s["id"], ""), s["suggested_date"])

    candidates = [tid for tid in bank if tid not in pending_ids]
    candidates.sort(key=lambda tid: last_suggested.get(tid, ""))

    need = args.target_pending - len(pending_ids)
    picks = candidates[:need]

    if not picks:
        print("No topics available to suggest.")
        return

    today = topics.today()
    for tid in picks:
        t = bank[tid]
        suggestions.append({
            "id": tid,
            "eyebrow": t.get("eyebrow", "Topic Idea"),
            "headline": t["headline"],
            "body": t["body"],
            "pull": t.get("pull", ""),
            "suggested_date": today,
            "status": "pending",
            "resolved_date": None,
            "posted_slug": None,
        })

    topics.save_suggestions(suggestions)
    print(f"Added {len(picks)} topic suggestion(s): {', '.join(picks)}")


if __name__ == "__main__":
    main()
