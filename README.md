# Producer Flow Academy — Book Site + Instagram Autopost

- `producer_flow_method_landing.html` / `thank_you.html` — the sales page and
  post-checkout page for *The Producer Flow Method* ebook (€47, Stripe checkout).
- `content/`, `scripts/`, `state/`, `.github/workflows/` — a content system
  that generates on-brand Instagram graphics and captions from the book's
  real copy (chapters, testimonials, key insights, credibility stats),
  opens a GitHub Issue for you to review each one, and posts it via the
  Instagram Graph API only once you approve it there.

## How the system works

**`scripts/generate_post.py`**, run on a schedule:

1. Picks the next item from a round-robin rotation across 7 content
   pillars (pain points, key insights, chapter teasers, testimonials,
   credibility stats, offer breakdown, "is this your book?" qualifiers) —
   see `scripts/lib/state.py`. No pillar repeats back-to-back, and the
   full 30-item bank cycles before anything repeats, with new caption
   wording each cycle.
2. Renders a 1080×1350 on-brand PNG for that item (`scripts/lib/cards.py`),
   matching the landing page's colors/fonts.
3. Writes a caption from `scripts/lib/captions.py` (rotating templates +
   hashtags, always ending with a link-in-bio CTA).

The **"Instagram Generate + Review"** workflow commits that image, waits
for it to be publicly fetchable, and opens a GitHub Issue with the preview
and caption — then stops. It skips generating a new candidate whenever one
is already awaiting review, so at most one is ever open at once.

You review it on the Issue (or the dashboard preview, if published — see
below) and label it:
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
