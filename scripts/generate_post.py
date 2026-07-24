#!/usr/bin/env python3
"""Selects the next post in the rotation, renders its graphic, and writes a
caption/meta sidecar. Does NOT post to Instagram — the workflow opens a
GitHub Issue for human review instead, and publish_post.py only runs later,
once that issue is labeled "approved".

Usage:
    python3 scripts/generate_post.py
    python3 scripts/generate_post.py --retention-days 14
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import cards, captions, copy, state  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIR = ROOT / "content" / "generated"


def prune_old(retention_days):
    if retention_days <= 0:
        return
    cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).strftime("%Y-%m-%d")
    if not GENERATED_DIR.exists():
        return
    for path in GENERATED_DIR.iterdir():
        if not path.is_file():
            continue
        # filenames are "<YYYY-MM-DD>-<item_id>.(png|json)"
        date_part = path.name[:10]
        if len(date_part) == 10 and date_part < cutoff:
            path.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--retention-days", type=int, default=14,
        help="Delete generated images/meta older than this many days (Instagram only needs "
             "the public URL to exist long enough to fetch it once during publish).",
    )
    args = parser.parse_args()

    bank = copy.load_bank()
    items = copy.build_items(bank)
    grouped = copy.items_by_pillar(items)
    brand = bank["brand"]

    item_id, cycle = state.next_item_id(grouped)
    item = items[item_id]
    caption = captions.render_caption(item, brand, cycle)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = f"{today}-{item_id}"
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    image_path = GENERATED_DIR / f"{slug}.png"
    meta_path = GENERATED_DIR / f"{slug}.json"

    html_str = cards.build_card_html(item, brand)
    cards.render_png(html_str, image_path)

    meta = {
        "slug": slug,
        "item_id": item_id,
        "pillar": item["pillar"],
        "card_type": item["card_type"],
        "cycle": cycle,
        "date": today,
        "caption": caption,
        "image_file": str(image_path.relative_to(ROOT)),
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
        f.write("\n")

    state.append_history({
        "slug": slug,
        "date": today,
        "item_id": item_id,
        "pillar": item["pillar"],
        "card_type": item["card_type"],
        "cycle": cycle,
        "image_file": meta["image_file"],
        "caption_excerpt": caption[:100],
        "status": "pending_review",
    })

    prune_old(args.retention_days)

    print(f"Generated: {slug}")
    print(f"  image: {image_path.relative_to(ROOT)}")
    print(f"  meta:  {meta_path.relative_to(ROOT)}")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"slug={slug}\n")
            f.write(f"image_file={meta['image_file']}\n")
            f.write(f"meta_file={meta_path.relative_to(ROOT)}\n")


if __name__ == "__main__":
    main()
