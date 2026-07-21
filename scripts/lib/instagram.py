"""Instagram Graph API publishing (image feed posts only).

Docs: https://developers.facebook.com/docs/instagram-platform/

Flow for a single-image post:
  1. POST /{ig-user-id}/media          (image_url, caption)   -> creation_id
  2. GET  /{creation_id}?fields=status_code                    -> poll until FINISHED
  3. POST /{ig-user-id}/media_publish  (creation_id)           -> media_id
"""
import os
import time

import requests

GRAPH_API_VERSION = os.environ.get("IG_GRAPH_API_VERSION", "v21.0")
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


class InstagramAPIError(RuntimeError):
    pass


def _raise_for_graph_error(response):
    if response.ok:
        return
    try:
        err = response.json().get("error", {})
    except ValueError:
        err = {}
    message = err.get("message", response.text)
    code = err.get("code")
    subcode = err.get("error_subcode")
    trace = err.get("fbtrace_id")
    raise InstagramAPIError(
        f"Graph API error (code={code}, subcode={subcode}, trace={trace}): {message}"
    )


def create_media_container(ig_user_id, access_token, image_url, caption):
    resp = requests.post(
        f"{GRAPH_API_BASE}/{ig_user_id}/media",
        data={"image_url": image_url, "caption": caption, "access_token": access_token},
        timeout=30,
    )
    _raise_for_graph_error(resp)
    return resp.json()["id"]


def get_container_status(creation_id, access_token):
    resp = requests.get(
        f"{GRAPH_API_BASE}/{creation_id}",
        params={"fields": "status_code,status", "access_token": access_token},
        timeout=30,
    )
    _raise_for_graph_error(resp)
    return resp.json()


def wait_until_finished(creation_id, access_token, timeout=90, interval=3):
    deadline = time.time() + timeout
    last_status = None
    while time.time() < deadline:
        info = get_container_status(creation_id, access_token)
        last_status = info.get("status_code")
        if last_status == "FINISHED":
            return info
        if last_status in ("ERROR", "EXPIRED"):
            raise InstagramAPIError(f"Media container failed: {info}")
        time.sleep(interval)
    raise InstagramAPIError(
        f"Timed out waiting for media container to finish (last status: {last_status})"
    )


def publish_media(ig_user_id, access_token, creation_id):
    resp = requests.post(
        f"{GRAPH_API_BASE}/{ig_user_id}/media_publish",
        data={"creation_id": creation_id, "access_token": access_token},
        timeout=30,
    )
    _raise_for_graph_error(resp)
    return resp.json()["id"]


def post_image(ig_user_id, access_token, image_url, caption):
    """End-to-end: create container, wait for it to finish processing, publish.

    Returns the published media id.
    """
    creation_id = create_media_container(ig_user_id, access_token, image_url, caption)
    wait_until_finished(creation_id, access_token)
    return publish_media(ig_user_id, access_token, creation_id)
