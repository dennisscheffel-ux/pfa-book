"""Posting rotation + history, persisted as JSON so state survives across
GitHub Actions runs (the workflow commits these files back to the repo).
"""
import json
import random
from datetime import datetime, timezone
from itertools import zip_longest
from pathlib import Path

from .copy import PILLAR_ORDER

ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = ROOT / "state"
ROTATION_PATH = STATE_DIR / "rotation_state.json"
HISTORY_PATH = STATE_DIR / "history.json"


def _build_sequence(cycle, grouped_items):
    """Round-robins across pillars so the same angle never posts twice in a
    row. Each pillar's items are shuffled with a cycle-seeded RNG, so the
    order changes every time the rotation wraps but stays reproducible.
    """
    shuffled = {}
    for pillar in PILLAR_ORDER:
        ids = list(grouped_items.get(pillar, []))
        rng = random.Random(f"{cycle}:{pillar}")
        rng.shuffle(ids)
        shuffled[pillar] = ids

    sequence = []
    for row in zip_longest(*(shuffled[p] for p in PILLAR_ORDER)):
        sequence.extend(item_id for item_id in row if item_id is not None)
    return sequence


def load_rotation_state():
    if ROTATION_PATH.exists():
        with open(ROTATION_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"cycle": 0, "sequence": [], "pointer": 0}


def save_rotation_state(state):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(ROTATION_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def next_item_id(grouped_items):
    """Advances the rotation and returns (item_id, cycle_used_for_this_pick)."""
    state = load_rotation_state()

    if state["pointer"] >= len(state["sequence"]):
        state["cycle"] += 1
        state["sequence"] = _build_sequence(state["cycle"], grouped_items)
        state["pointer"] = 0

    item_id = state["sequence"][state["pointer"]]
    cycle_used = state["cycle"]
    state["pointer"] += 1
    save_rotation_state(state)
    return item_id, cycle_used


def peek_upcoming(grouped_items, count):
    """Non-mutating preview of the next `count` (item_id, cycle) picks in the
    rotation — same logic as next_item_id, but never advances or saves state.
    Used by the local dashboard's queue preview.
    """
    state = load_rotation_state()
    cycle = state["cycle"]
    sequence = list(state["sequence"])
    pointer = state["pointer"]

    upcoming = []
    while len(upcoming) < count:
        if pointer >= len(sequence):
            cycle += 1
            sequence = _build_sequence(cycle, grouped_items)
            pointer = 0
            if not sequence:
                break
        upcoming.append((sequence[pointer], cycle))
        pointer += 1
    return upcoming


def load_history():
    if HISTORY_PATH.exists():
        with open(HISTORY_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_history(history):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)
        f.write("\n")


def append_history(record):
    history = load_history()
    record.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    history.append(record)
    save_history(history)
    return history


def update_history_by_slug(slug, **fields):
    """Updates the history entry matching slug (date + item_id). Used by the
    publish step, which now runs in a separate, later workflow run (after
    human review) rather than immediately after generation, so "last entry"
    is no longer a safe way to find the right record.
    """
    history = load_history()
    for record in history:
        if record.get("slug") == slug:
            record.update(fields)
            save_history(history)
            return record
    raise RuntimeError(f"No history entry found for slug {slug!r}")
