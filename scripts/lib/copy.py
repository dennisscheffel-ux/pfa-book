"""Loads content/copy_bank.json into a flat registry of postable content items.

Each item belongs to a "pillar" (the marketing angle) and carries a "card_type"
(which HTML card layout to render it with, see lib/cards.py).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COPY_BANK_PATH = ROOT / "content" / "copy_bank.json"

# Fixed pillar order: used to build the round-robin posting sequence so the
# same angle never repeats back-to-back.
PILLAR_ORDER = [
    "pain_point",
    "insight",
    "chapter",
    "testimonial",
    "stat",
    "offer",
    "qualifier",
]


def load_bank():
    with open(COPY_BANK_PATH, encoding="utf-8") as f:
        return json.load(f)


def build_items(bank=None):
    """Returns {item_id: item_dict} for every postable piece of content.

    item_dict always has: id, pillar, card_type, plus pillar-specific fields
    used by both the caption templates and the card renderer.
    """
    bank = bank or load_bank()
    items = {}

    for p in bank["pain_points"]:
        card_type = "quote" if p["id"] == "pain_truth" else "problem"
        items[p["id"]] = {**p, "pillar": "pain_point", "card_type": card_type}

    for i in bank["insights"]:
        items[i["id"]] = {**i, "pillar": "insight", "card_type": "insight"}

    for c in bank["chapters"]:
        items[c["id"]] = {**c, "pillar": "chapter", "card_type": "chapter"}

    for t in bank["testimonials"]:
        items[t["id"]] = {**t, "pillar": "testimonial", "card_type": "testimonial"}

    for s in bank["credibility"]["stats"]:
        items[s["id"]] = {**s, "pillar": "stat", "card_type": "stat"}

    for o in bank["offer_items"]:
        items[o["id"]] = {**o, "pillar": "offer", "card_type": "offer"}

    items["qualifier_yes"] = {
        "id": "qualifier_yes",
        "pillar": "qualifier",
        "card_type": "qualifier",
        "heading": "This is for you if...",
        "tone": "yes",
        "lines": bank["for_who"]["yes"],
    }
    items["qualifier_no"] = {
        "id": "qualifier_no",
        "pillar": "qualifier",
        "card_type": "qualifier",
        "heading": "This isn't for you if...",
        "tone": "no",
        "lines": bank["for_who"]["no"],
    }

    return items


def items_by_pillar(items=None):
    items = items or build_items()
    grouped = {p: [] for p in PILLAR_ORDER}
    for item_id, item in items.items():
        grouped[item["pillar"]].append(item_id)
    for ids in grouped.values():
        ids.sort()  # stable base order; state.py shuffles per-cycle
    return grouped
