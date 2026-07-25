"""Weekly topic suggestions: static seed ideas (content/topic_bank.json)
surfaced for accept/decline review in the dashboard, tracked in
state/topic_suggestions.json. Accepted topics jump ahead of the normal
pillar rotation in generate_post.py.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOPIC_BANK_PATH = ROOT / "content" / "topic_bank.json"
SUGGESTIONS_PATH = ROOT / "state" / "topic_suggestions.json"


def load_bank():
    with open(TOPIC_BANK_PATH, encoding="utf-8") as f:
        return {t["id"]: t for t in json.load(f)["topics"]}


def load_suggestions():
    if SUGGESTIONS_PATH.exists():
        with open(SUGGESTIONS_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_suggestions(suggestions):
    SUGGESTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SUGGESTIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(suggestions, f, indent=2, ensure_ascii=False)
        f.write("\n")


def today():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def next_accepted():
    """Oldest accepted-but-not-yet-posted suggestion, or None."""
    accepted = [s for s in load_suggestions() if s["status"] == "accepted"]
    if not accepted:
        return None
    accepted.sort(key=lambda s: s.get("resolved_date") or s["suggested_date"])
    return accepted[0]


def mark_posted(topic_id, slug):
    suggestions = load_suggestions()
    for s in suggestions:
        if s["id"] == topic_id:
            s["status"] = "posted"
            s["posted_slug"] = slug
            save_suggestions(suggestions)
            return s
    raise RuntimeError(f"No topic suggestion found for id {topic_id!r}")


def resolve(topic_id, decision):
    if decision not in ("accepted", "declined"):
        raise ValueError("decision must be 'accepted' or 'declined'")
    suggestions = load_suggestions()
    for s in suggestions:
        if s["id"] == topic_id:
            s["status"] = decision
            s["resolved_date"] = today()
            save_suggestions(suggestions)
            return s
    raise RuntimeError(f"No topic suggestion found for id {topic_id!r}")
