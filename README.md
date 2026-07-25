# Producer Flow Academy — Book Site + Instagram Autopost

- `producer_flow_method_landing.html` / `thank_you.html` — the sales page and
  post-checkout page for *The Producer Flow Method* ebook (€47, Stripe checkout).
- `content/`, `scripts/`, `state/`, `.github/workflows/` — a content system
  that generates on-brand Instagram graphics and captions from the book's
  real copy (chapters, testimonials, key insights, credibility stats),
  opens a GitHub Issue for you to review each one, and posts it via the
  Instagram Graph API only once you approve it there.

## How the system works

**`scripts/suggest_topics.py`**, run weekly:

Tops up a pending queue (default 6) of fresh content angles drawn from
`content/topic_bank.json` — a curated, evergreen bank of niche topic ideas
beyond the core 7-pillar copy — surfaced in the dashboard's **Topics** tab
for you to Accept/Decline. Never-suggested topics come first; once the
whole bank has been shown, the least-recently-suggested ones resurface.
Tracked in `state/topic_suggestions.json`.

**`scripts/generate_post.py`**, run on a schedule:

1. If a topic has been **Accepted** on the Topics tab, it jumps the queue:
   generates from that topic next, ahead of the normal rotation.
2. Otherwise, picks the next item from a round-robin rotation across 7
   content pillars (pain points, key insights, chapter teasers,
   testimonials, credibility stats, offer breakdown, "is this your book?"
   qualifiers) — see `scripts/lib/state.py`. No pillar repeats
   back-to-back, and the full 30-item bank cycles before anything repeats,
   with new caption wording each cycle.
3. Renders a 1080×1350 on-brand PNG for that item (`scripts/lib/cards.py`),
   matching the landing page's colors/fonts.
4. Writes a caption from `scripts/lib/captions.py` (rotating templates +
   hashtags, always ending with a link-in-bio CTA).

The **"Instagram Generate + Review"** workflow commits that image, waits
for it to be publicly fetchable, and opens a GitHub Issue with the preview
and caption — then stops. It skips generating a new candidate whenever one
is already awaiting review, so at most one is ever open at once.

You review it on the Issue itself, or from the **dashboard** (`dashboard/`)
— run it locally (`python3 dashboard/app.py`, includes a Queue preview tab)
or host it on Vercel for access from anywhere (`dashboard/api/`, password
protected, no Queue tab since that needs a real browser). See
[SETUP.md](SETUP.md#8-run-the-local-dashboard-optional-but-recommended)
for both. Either way it adds real one-click Approve/Decline buttons and a
form for editing the content bank, instead of adding GitHub labels or
hand-editing JSON by hand. Resolving a post means labeling its issue:
- **`approved`** → the **"Instagram Publish on Approval"** workflow calls
  `scripts/publish_post.py`, which actually posts to Instagram via the
  Graph API, then closes the issue with the resulting media id.
- **`declined`** → the issue closes as skipped; the next candidate
  generates on the regular schedule.

Old generated images are pruned automatically after ~2 weeks (Instagram
only needs the URL once, at publish time).

**One-time credential setup required — see [SETUP.md](SETUP.md).** Nothing
posts until `IG_ACCESS_TOKEN` / `IG_USER_ID` are configured as repo secrets.

## Local development

```bash
pip install -r requirements.txt
playwright install chromium

python3 scripts/generate_post.py          # picks next post, renders PNG, writes caption
python3 scripts/publish_post.py \
  --meta content/generated/<date>-<id>.json \
  --image-url https://example.com/preview.png \
  --dry-run                                # prints the caption without calling Instagram
```

Generated files land in `content/generated/`; rotation/history state lives
in `state/`.
