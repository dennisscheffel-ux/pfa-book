"""GitHub API client shared by the local dashboard (dashboard/app.py) and the
hosted Vercel entrypoint (dashboard/api/index.py). No Playwright/local-disk
assumptions here — everything goes through the GitHub API, which works the
same whether the caller has a persistent filesystem or not.
"""
import base64
import json
import os
from datetime import datetime, timezone

import requests

GITHUB_REPO = os.environ.get("GITHUB_REPO", "dennisscheffel-ux/pfa-book")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

API_BASE = "https://api.github.com"
RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main"
COPY_BANK_PATH = "content/copy_bank.json"
TOPIC_STATE_PATH = "state/topic_suggestions.json"


class GitHubClientError(RuntimeError):
    pass


def _require_token():
    if not GITHUB_TOKEN:
        raise GitHubClientError(
            "GITHUB_TOKEN is not set. See SETUP.md for how to generate one and where to set it."
        )


def _headers():
    _require_token()
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def fetch_pending():
    resp = requests.get(
        f"{API_BASE}/repos/{GITHUB_REPO}/issues",
        headers=_headers(),
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


def resolve_issue(issue_number, decision):
    resp = requests.post(
        f"{API_BASE}/repos/{GITHUB_REPO}/issues/{issue_number}/labels",
        headers=_headers(),
        json={"labels": [decision]},
        timeout=15,
    )
    resp.raise_for_status()


def fetch_content():
    resp = requests.get(f"{RAW_BASE}/{COPY_BANK_PATH}", timeout=15)
    resp.raise_for_status()
    return resp.json()


def fetch_pending_topics():
    resp = requests.get(f"{RAW_BASE}/{TOPIC_STATE_PATH}", timeout=15)
    resp.raise_for_status()
    topics = resp.json()
    return [t for t in topics if t.get("status") == "pending"]


def resolve_topic(topic_id, decision):
    """Accept/decline a suggested topic by committing the status change
    straight to main via the Contents API (mirrors save_content_via_github).
    Requires the token to have Contents: Read and write.
    """
    get_resp = requests.get(
        f"{API_BASE}/repos/{GITHUB_REPO}/contents/{TOPIC_STATE_PATH}",
        headers=_headers(),
        timeout=15,
    )
    get_resp.raise_for_status()
    payload = get_resp.json()
    sha = payload["sha"]
    topics = json.loads(base64.b64decode(payload["content"]).decode("utf-8"))

    found = None
    for t in topics:
        if t["id"] == topic_id:
            t["status"] = decision
            t["resolved_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            found = t
            break
    if not found:
        raise GitHubClientError(f"Topic {topic_id!r} not found")

    content_str = json.dumps(topics, indent=2, ensure_ascii=False) + "\n"
    encoded = base64.b64encode(content_str.encode("utf-8")).decode("ascii")

    put_resp = requests.put(
        f"{API_BASE}/repos/{GITHUB_REPO}/contents/{TOPIC_STATE_PATH}",
        headers=_headers(),
        json={
            "message": f"chore(topics): {decision} {topic_id}",
            "content": encoded,
            "sha": sha,
            "branch": "main",
        },
        timeout=15,
    )
    put_resp.raise_for_status()
    return found


def save_content_via_github(data):
    """Commits an updated copy_bank.json straight to main via the Contents
    API. Used by the hosted (Vercel) dashboard, which has no persistent
    local disk to write to. Requires the token to also have Contents:
    Read and write, in addition to Issues.
    """
    get_resp = requests.get(
        f"{API_BASE}/repos/{GITHUB_REPO}/contents/{COPY_BANK_PATH}",
        headers=_headers(),
        timeout=15,
    )
    get_resp.raise_for_status()
    sha = get_resp.json()["sha"]

    content_str = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    encoded = base64.b64encode(content_str.encode("utf-8")).decode("ascii")

    put_resp = requests.put(
        f"{API_BASE}/repos/{GITHUB_REPO}/contents/{COPY_BANK_PATH}",
        headers=_headers(),
        json={
            "message": "chore(content): edit copy bank via hosted dashboard",
            "content": encoded,
            "sha": sha,
            "branch": "main",
        },
        timeout=15,
    )
    put_resp.raise_for_status()
