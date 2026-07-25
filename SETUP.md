# Instagram Autopost — Setup

This repo generates an on-brand Instagram graphic + caption on a schedule,
opens a GitHub Issue so you can review it, and only posts it via the
Instagram Graph API once you label that issue `approved` (label it
`declined` to skip it instead). Everything except the Meta/Instagram
credentials is already wired up — this doc covers the one-time setup only
you can do (it requires your own Meta login).

## 1. Prerequisites

- The `@producerflowacademy` Instagram account must be a **Business or
  Creator** account (Settings → Account type in the Instagram app).
- It must be **linked to a Facebook Page** (any Page — it can be minimal;
  Instagram → Settings → Linked accounts → Facebook).
- A free **Meta Developer account** at [developers.facebook.com](https://developers.facebook.com).

## 2. Create a Meta App

1. [developers.facebook.com](https://developers.facebook.com) → **My Apps** → **Create App** → type **Business**.
2. In the app dashboard, note the **App ID** and **App Secret** (App Settings → Basic).
3. Under **App Roles → Roles**, add the Facebook account that manages your
   Page/Instagram as an **Administrator**. This is the key step that lets
   your own app publish to your own account while the app is still in
   **Development mode** — no App Review needed for self-use.

## 3. Generate the access token

1. Go to the [Graph API Explorer](https://developers.facebook.com/tools/explorer).
2. Select your app, then **Get User Access Token**, and request these
   permissions: `instagram_basic`, `instagram_content_publish`,
   `pages_show_list`, `pages_read_engagement`, `business_management`.
3. Exchange that short-lived token for a **long-lived token** (valid ~60
   days) — either via the Explorer's token debugger "Extend token" action,
   or by calling:
   ```
   GET https://graph.facebook.com/v21.0/oauth/access_token
     ?grant_type=fb_exchange_token
     &client_id={app-id}
     &client_secret={app-secret}
     &fb_exchange_token={short-lived-user-token}
   ```
4. Use that long-lived **user** token to list your Pages and get the
   Page's own access token (Page tokens minted from a long-lived user token
   don't expire on a fixed schedule):
   ```
   GET https://graph.facebook.com/v21.0/me/accounts?access_token={long-lived-user-token}
   ```
   Copy the `access_token` for the Page linked to your Instagram account —
   this is your `IG_ACCESS_TOKEN`.
5. Get the Instagram Business Account ID (`IG_USER_ID`):
   ```
   GET https://graph.facebook.com/v21.0/{page-id}?fields=instagram_business_account&access_token={page-access-token}
   ```
   The `instagram_business_account.id` in the response is `IG_USER_ID`.

If a token ever stops working (password change, revoked app role, etc.),
just repeat steps 3-5 and update the secret below.

## 4. Add GitHub repo secrets

**Settings → Secrets and variables → Actions → New repository secret**

| Secret name       | Value                                  |
|-------------------|-----------------------------------------|
| `IG_ACCESS_TOKEN` | The Page access token from step 3.4     |
| `IG_USER_ID`      | The Instagram Business Account ID from step 3.5 |

## 5. Allow the workflow to push back

**Settings → Actions → General → Workflow permissions** → select
**"Read and write permissions"**. The workflow commits each generated
image and the rotation state back to the repo, which needs write access.

## 6. Keep the repo public (or swap the image host)

The workflow hosts each generated graphic at
`https://raw.githubusercontent.com/<repo>/<branch>/content/generated/...`
so Instagram's servers can fetch it — that only works if the repo (or at
least that path) is publicly readable without auth. If this repo is ever
made private, swap `scripts/generate_post.py` / the workflow's "Resolve
public image URL" step to upload to a public image host instead (e.g. an
S3 bucket or Cloudinary) before publishing.

## 7. Test it

**Actions tab → "Instagram Generate + Review" → Run workflow** → run. This
renders a real graphic, commits it, and opens a GitHub Issue titled
"Review: &lt;date&gt;-&lt;item&gt;" with the image and caption. Add the
`approved` label on that issue to actually publish it (or `declined` to
skip it) — a second workflow, "Instagram Publish on Approval", picks up
that label automatically and either publishes for real or closes the
issue as skipped.

After that, "Instagram Generate + Review" runs automatically on the
schedule in `.github/workflows/instagram-generate-review.yml` (defaults to
daily at 16:00 UTC — edit the cron expression to change cadence/time). It
skips generating a new candidate whenever one is already awaiting review,
so at most one issue is ever open at a time.

## 8. Run the local dashboard (optional but recommended)

A local web app to review/approve posts with real one-click buttons (no
need to go to GitHub and add labels by hand), preview what's coming up
next in the rotation before it's generated, and edit the content bank in
a form instead of hand-editing JSON.

1. Generate a **fine-grained personal access token** at
   [github.com/settings/personal-access-tokens/new](https://github.com/settings/personal-access-tokens/new):
   - Resource owner: you · Repository access: **Only this repository** → this repo
   - Permissions: **Issues → Read and write** (nothing else needed)
2. ```bash
   cd dashboard
   pip install -r requirements.txt
   playwright install chromium   # only needed once, for the Queue preview tab
   cp .env.example .env
   # edit .env and paste your token into GITHUB_TOKEN
   python3 app.py
   ```
3. Open [http://localhost:5000](http://localhost:5000).

This app never talks to Instagram directly — clicking **Approve** just
adds the `approved` label to the pending GitHub Issue via the GitHub API
(same as adding it by hand), which is what the "Instagram Publish on
Approval" workflow is already watching for. **Decline** works the same
way with the `declined` label. The **Queue** tab renders a preview of the
next several posts in rotation without generating or posting anything.
The **Content** tab edits `content/copy_bank.json` directly on disk —
commit and push the change yourself once you're happy with it.

Never commit `dashboard/.env` — it holds a real token. It's already
gitignored.

## Customizing content

- `content/copy_bank.json` — every fact, quote, chapter blurb, and
  testimonial the system draws from. Add new testimonials or stats here as
  they come in.
- `scripts/lib/captions.py` — caption templates, CTA copy, and the
  hashtag pool.
- `scripts/lib/cards.py` — the on-brand graphic templates (colors/fonts
  match `producer_flow_method_landing.html`).
- `state/rotation_state.json` / `state/history.json` — posting rotation
  and log. Delete `rotation_state.json` to force a fresh reshuffled cycle;
  `history.json` is a running audit log of every post generated, and its
  status (`pending_review`, `published`, `declined`, or `failed`).
- Posting time/frequency — edit the `cron:` line in
  `.github/workflows/instagram-generate-review.yml`.

The generator (`scripts/generate_post.py`) produces a caption + image pair
independent of Instagram, so the same output could later feed a second
publisher module (Threads, Facebook, etc.) without touching the content
system itself.
