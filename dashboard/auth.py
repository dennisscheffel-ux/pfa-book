"""Optional shared-password gate. Enforced only when DASHBOARD_PASSWORD is
set — the local app can be left password-free, but the hosted (Vercel)
deployment should always set one, since a public URL with working
Approve/Decline buttons can trigger a real Instagram post.
"""
import os
from functools import wraps

from flask import redirect, request, session, url_for

DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD")


def register_auth(app):
    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = None
        if request.method == "POST":
            if request.form.get("password") == DASHBOARD_PASSWORD:
                session["authed"] = True
                return redirect(request.args.get("next") or url_for("index"))
            error = "Wrong password."
        return _login_page(error)

    @app.before_request
    def require_login():
        if not DASHBOARD_PASSWORD:
            return None
        if request.endpoint in ("login", "static"):
            return None
        if not session.get("authed"):
            return redirect(url_for("login", next=request.path))
        return None


def _login_page(error):
    from flask import render_template
    return render_template("login.html", error=error)
