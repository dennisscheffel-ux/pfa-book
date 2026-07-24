#!/usr/bin/env python3
"""Publishes an already-generated, human-approved post to Instagram.

Expects generate_post.py to have already run (and its output image to already
be pushed to a public URL, since the Instagram Graph API fetches images by
URL — it will not accept a local file). Runs once a GitHub Issue for the post
has been labeled "approved" — see .github/workflows/instagram-publish-on-approval.yml.

Usage:
    python3 scripts/publish_post.py --meta content/generated/2026-07-21-ch_1a.json \
        --image-url https://raw.githubusercontent.com/OWNER/REPO/main/content/generated/2026-07-21-ch_1a.png

    python3 scripts/publish_post.py --meta ... --image-url ... --dry-run
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import instagram, state  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--meta", required=True, help="Path to the *.json sidecar written by generate_post.py")
    parser.add_argument("--image-url", required=True, help="Public HTTPS URL where the rendered PNG now lives")
    parser.add_argument("--dry-run", action="store_true", help="Skip the actual Instagram API call")
    args = parser.parse_args()

    with open(args.meta, encoding="utf-8") as f:
        meta = json.load(f)

    caption = meta["caption"]
    slug = meta["slug"]

    if args.dry_run:
        print(f"[dry-run] Would publish {args.image_url}\n---\n{caption}\n---")
        return

    access_token = os.environ.get("IG_ACCESS_TOKEN")
    ig_user_id = os.environ.get("IG_USER_ID")
    if not access_token or not ig_user_id:
        print(
            "IG_ACCESS_TOKEN and IG_USER_ID must be set as environment variables "
            "(configured as GitHub Actions secrets). See SETUP.md.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        media_id = instagram.post_image(ig_user_id, access_token, args.image_url, caption)
    except instagram.InstagramAPIError as e:
        state.update_history_by_slug(slug, status="failed", error=str(e))
        print(f"Failed to publish: {e}", file=sys.stderr)
        sys.exit(1)

    state.update_history_by_slug(slug, status="published", ig_media_id=media_id, image_url=args.image_url)
    print(f"Published. Instagram media id: {media_id}")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"media_id={media_id}\n")


if __name__ == "__main__":
    main()
