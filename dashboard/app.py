#!/usr/bin/env python3
"""Local dashboard: review pending posts, approve/decline them for real,
preview what's coming up next in the rotation, and edit the content bank.

Run with:
    pip install -r dashboard/requirements.txt
    cp dashboard/.env.example dashboard/.env   # fill in GITHUB_TOKEN
    python3 dashboard/app.py

Then open http://localhost:5000. Approve/Decline call the GitHub API
directly (adding the "approved"/"declined" label to the pending review
issue), which is what the "Instagram Publish on Approval" GitHub Actions
workflow watches for — this app never talks to Instagram itself.
"""
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_from_directory

DASHBOARD_DIR = Path(__file__).resolve().parent
ROOT = DASHBOARD_DIR.parent
CACHE_DIR = DASHBOARD_DIR / ".cache"

sys.path.insert(0, str(ROOT / "scripts"))
from lib import cards, captions, copy, state  # noqa: E402

load_dotenv(DASHBOARD_DIR / ".env")

GITHUB_REPO = os.environ.get("GITHUB_REPO", "dennisscheffel-ux/pfa-book")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    print(
        "GITHUB_TOKEN is not set. Copy dashboard/.env.example to dashboard/.env "
        "and fill it in (see SETUP.md for how to generate one).",
        file=sys.stderr,
    )
    sys.exit(1)

API_BASE = "https://api.github.com"
RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main"
COPY_BANK_PATH = ROOT / "content" / "copy_bank.json"

app = Flask(__name__)


def gh_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def fetch_pending():
    resp = requests.get(
        f"{API_BASE}/repos/{GITHUB_REPO}/issues",
        headers=gh_headers(),
        params={"labels": "pending-review", "state": "open"},
        timeout=15,
    )
    resp.raise_for_status()
    issues = resp.json()
    if not issues:
        return None
    issue = issues[0]
    slug = issue["title"].removeprefix("Review: ")
    return {
        "number": issue["number"],
        "slug": slug,
        "html_url": issue["html_url"],
        "image_url": f"{RAW_BASE}/content/generated/{slug}.png",
        "body": issue["body"],
    }


def fetch_history():
    resp = requests.get(f"{RAW_BASE}/state/history.json", timeout=15)
    resp.raise_for_status()
    history = resp.json()
    resolved = [r for r in history if r.get("status") in ("published", "declined", "failed")]
    resolved.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    return resolved[:8]


@app.route("/")
def index():
    return render_template("index.html", repo=GITHUB_REPO)


@app.route("/api/state")
def api_state():
    try:
        pending = fetch_pending()
        recent = fetch_history()
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 502
    return jsonify({"pending": pending, "recent": recent})


@app.route("/api/resolve", methods=["POST"])
def api_resolve():
    data = request.get_json(force=True)
    issue_number = data.get("issue_number")
    decision = data.get("decision")
    if decision not in ("approved", "declined"):
        return jsonify({"error": "decision must be 'approved' or 'declined'"}), 400
    if not issue_number:
        return jsonify({"error": "issue_number is required"}), 400

    resp = requests.post(
        f"{API_BASE}/repos/{GITHUB_REPO}/issues/{issue_number}/labels",
        headers=gh_headers(),
        json={"labels": [decision]},
        timeout=15,
    )
    if not resp.ok:
        return jsonify({"error": resp.text}), resp.status_code
    return jsonify({"ok": True})


@app.route("/api/queue")
def api_queue():
    count = min(int(request.args.get("count", 6)), 12)
    bank = copy.load_bank()
    items = copy.build_items(bank)
    grouped = copy.items_by_pillar(items)
    brand = bank["brand"]

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    upcoming = state.peek_upcoming(grouped, count)

    preview = []
    for item_id, cycle in upcoming:
        item = items[item_id]
        image_path = CACHE_DIR / f"{item_id}.png"
        if not image_path.exists():
            html_str = cards.build_card_html(item, brand)
            cards.render_png(html_str, image_path)
        preview.append({
            "item_id": item_id,
            "pillar": item["pillar"],
            "card_type": item["card_type"],
            "caption": captions.render_caption(item, brand, cycle),
            "image_url": f"/api/queue-image/{item_id}.png",
        })
    return jsonify({"upcoming": preview})


@app.route("/api/queue-image/<path:filename>")
def api_queue_image(filename):
    return send_from_directory(CACHE_DIR, filename)


@app.route("/api/content", methods=["GET"])
def api_content_get():
    with open(COPY_BANK_PATH, encoding="utf-8") as f:
        return jsonify(json.load(f))


@app.route("/api/content", methods=["POST"])
def api_content_post():
    data = request.get_json(force=True)
    required_top_level = {"brand", "credibility", "pain_points", "insights", "chapters",
                           "testimonials", "offer_items", "for_who"}
    missing = required_top_level - set(data.keys())
    if missing:
        return jsonify({"error": f"Missing top-level keys: {sorted(missing)}"}), 400

    with open(COPY_BANK_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Any cached queue previews may now be stale.
    for cached_file in CACHE_DIR.glob("*.png"):
        cached_file.unlink()

    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
