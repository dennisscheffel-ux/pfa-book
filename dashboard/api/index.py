"""Vercel entrypoint for the hosted dashboard: Review + Content tabs only.

No Playwright/Chromium here (not viable in a standard Python serverless
function) — the Queue preview tab lives only in the local app
(dashboard/app.py). Content edits commit straight to main via the GitHub
Contents API instead of writing to local disk, since serverless functions
have no persistent filesystem across requests.

Required environment variables (set in the Vercel project settings, not a
.env file): GITHUB_TOKEN, GITHUB_REPO, SECRET_KEY, DASHBOARD_PASSWORD.
See SETUP.md for how to generate the token and what scope it needs.
"""
import os
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, request

DASHBOARD_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DASHBOARD_DIR))
import gh_client  # noqa: E402
from auth import register_auth  # noqa: E402

app = Flask(
    __name__,
    template_folder=str(DASHBOARD_DIR / "templates"),
    static_folder=str(DASHBOARD_DIR / "static"),
)
app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("SECRET_KEY must be set (Vercel project settings -> Environment Variables).")

register_auth(app)


@app.route("/")
def index():
    return render_template(
        "index.html",
        show_queue=False,
        content_save_note="Edit the source material the system draws posts from. "
                           "Save commits directly to main on GitHub — no local disk here.",
        topics_note="Accept/decline commits directly to main on GitHub. "
                     "Accepted topics jump ahead of the normal rotation.",
    )


@app.route("/api/state")
def api_state():
    try:
        pending = gh_client.fetch_pending()
        recent = gh_client.fetch_history()
    except Exception as e:
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
    try:
        gh_client.resolve_issue(issue_number, decision)
    except Exception as e:
        return jsonify({"error": str(e)}), 502
    return jsonify({"ok": True})


@app.route("/api/topics")
def api_topics():
    try:
        return jsonify({"pending": gh_client.fetch_pending_topics()})
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@app.route("/api/topics/resolve", methods=["POST"])
def api_topics_resolve():
    data = request.get_json(force=True)
    topic_id = data.get("topic_id")
    decision = data.get("decision")
    if decision not in ("accepted", "declined"):
        return jsonify({"error": "decision must be 'accepted' or 'declined'"}), 400
    if not topic_id:
        return jsonify({"error": "topic_id is required"}), 400
    try:
        gh_client.resolve_topic(topic_id, decision)
    except Exception as e:
        return jsonify({"error": str(e)}), 502
    return jsonify({"ok": True})


@app.route("/api/content", methods=["GET"])
def api_content_get():
    try:
        return jsonify(gh_client.fetch_content())
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@app.route("/api/content", methods=["POST"])
def api_content_post():
    data = request.get_json(force=True)
    required_top_level = {"brand", "credibility", "pain_points", "insights", "chapters",
                           "testimonials", "offer_items", "for_who"}
    missing = required_top_level - set(data.keys())
    if missing:
        return jsonify({"error": f"Missing top-level keys: {sorted(missing)}"}), 400
    try:
        gh_client.save_content_via_github(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 502
    return jsonify({"ok": True})
