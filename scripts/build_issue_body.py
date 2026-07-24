#!/usr/bin/env python3
"""Builds the Markdown body for a review-queue GitHub Issue from a generated
post's meta sidecar. Printed to stdout so the workflow can pipe it to a file
for `gh issue create --body-file`.

Usage:
    python3 scripts/build_issue_body.py --meta content/generated/2026-07-21-ch_1a.json \
        --image-url https://raw.githubusercontent.com/OWNER/REPO/main/content/generated/2026-07-21-ch_1a.png
"""
import argparse
import json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--meta", required=True)
    parser.add_argument("--image-url", required=True)
    args = parser.parse_args()

    with open(args.meta, encoding="utf-8") as f:
        meta = json.load(f)

    print(f"![preview]({args.image_url})")
    print()
    print(f"**Pillar:** {meta['pillar']} · **Card type:** {meta['card_type']}")
    print()
    print("**Caption:**")
    print()
    print("```")
    print(meta["caption"])
    print("```")
    print()
    print("---")
    print("Add the `approved` label to publish this now, or `declined` to skip it "
          "(the next candidate will generate on the regular schedule once this issue is closed).")


if __name__ == "__main__":
    main()
