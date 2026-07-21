"""Renders on-brand Instagram feed graphics (1080x1350 PNG) for each content
card_type, reusing the color palette and type treatment from
producer_flow_method_landing.html.
"""
import html
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

WIDTH, HEIGHT = 1080, 1350

FONTS_IMPORT = (
    "https://fonts.googleapis.com/css2?"
    "family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400;1,600"
    "&family=DM+Mono:wght@300;400;500"
    "&family=Syne:wght@400;600;700;800&display=swap"
)

BASE_CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1350px;overflow:hidden}
body{
  background:#08080A;color:#F0F4F8;font-family:'Syne',sans-serif;
  position:relative;
}
.bg-grid{
  position:absolute;inset:0;
  background-image:linear-gradient(rgba(201,168,76,0.06) 1px,transparent 1px),
                    linear-gradient(90deg,rgba(201,168,76,0.06) 1px,transparent 1px);
  background-size:60px 60px;
}
.bg-glow{
  position:absolute;inset:0;
  background:radial-gradient(ellipse 90% 60% at 50% 15%,rgba(91,155,213,0.14),transparent 60%);
}
.card{
  position:relative;z-index:2;width:1080px;height:1350px;
  display:flex;flex-direction:column;justify-content:space-between;
  padding:90px 86px 70px;
}
.eyebrow{
  font-family:'DM Mono',monospace;font-size:22px;letter-spacing:5px;
  color:#7AA7D9;text-transform:uppercase;display:flex;align-items:center;gap:16px;
}
.eyebrow::before{content:'';width:36px;height:2px;background:#4A7FAD;display:block;flex-shrink:0}
.content{flex:1;display:flex;flex-direction:column;justify-content:center;margin:50px 0}
.footer{
  display:flex;justify-content:space-between;align-items:center;
  border-top:1px solid rgba(91,155,213,0.25);padding-top:32px;
}
.footer-logo{font-family:'DM Mono',monospace;font-size:19px;letter-spacing:3px;color:#A0AABB;text-transform:uppercase}
.footer-logo span{color:#5B9BD5}
.footer-cta{
  font-family:'DM Mono',monospace;font-size:19px;letter-spacing:2px;color:#08080A;
  background:#5B9BD5;padding:10px 22px;text-transform:uppercase;font-weight:500;
}
.headline{font-family:'Cormorant Garamond',serif;font-weight:300;line-height:1.08;color:#F0F4F8}
.headline em{font-style:italic;color:#5B9BD5}
.body-text{font-size:30px;line-height:1.75;color:#A0AABB;max-width:900px;margin-top:34px}
.pull{font-family:'Cormorant Garamond',serif;font-style:italic;font-size:34px;color:#5B9BD5;line-height:1.5;margin-top:40px}
.tag-pill{
  display:inline-block;font-family:'DM Mono',monospace;font-size:18px;letter-spacing:2px;
  color:#5B9BD5;border:1px solid rgba(91,155,213,0.4);padding:8px 18px;margin-top:30px;text-transform:uppercase;
}
.giant-num{
  position:absolute;top:60px;right:80px;font-family:'Cormorant Garamond',serif;font-style:italic;
  font-size:220px;color:rgba(91,155,213,0.08);line-height:1;z-index:1;
}
.quote-mark{font-family:'Cormorant Garamond',serif;font-size:130px;color:rgba(91,155,213,0.18);line-height:0.6}
.testi-name{font-family:'DM Mono',monospace;font-size:22px;letter-spacing:3px;color:#5B9BD5;text-transform:uppercase;margin-top:30px}
.testi-role{font-family:'DM Mono',monospace;font-size:19px;letter-spacing:2px;color:#A0AABB;text-transform:uppercase;margin-top:6px}
.result-pill{
  display:inline-block;font-family:'DM Mono',monospace;font-size:17px;letter-spacing:1.5px;color:#5B9BD5;
  border:1px solid rgba(91,155,213,0.3);padding:6px 16px;margin-top:16px;text-transform:uppercase;
}
.stat-number{font-family:'Cormorant Garamond',serif;font-weight:300;font-size:220px;color:#5B9BD5;line-height:1;text-align:center}
.stat-label{font-family:'DM Mono',monospace;font-size:26px;letter-spacing:3px;color:#A0AABB;text-transform:uppercase;text-align:center;margin-top:24px}
.qual-heading{font-family:'Cormorant Garamond',serif;font-style:italic;font-weight:300;font-size:64px;line-height:1.15;margin-bottom:44px}
.qual-list{list-style:none;display:flex;flex-direction:column;gap:24px}
.qual-list li{font-size:28px;line-height:1.6;color:#A0AABB;display:flex;gap:18px;align-items:flex-start}
.qual-icon{flex-shrink:0;font-size:26px;margin-top:2px}
"""


def _esc(s):
    return html.escape(str(s), quote=False)


def _fit_headline_size(text, max_len_for_full=40):
    length = len(text)
    if length <= max_len_for_full:
        return 96
    if length <= 70:
        return 72
    if length <= 110:
        return 56
    return 44


def _shell(inner, footer_right="Link in bio"):
    return f"""<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="{FONTS_IMPORT}">
<style>{BASE_CSS}</style></head><body>
<div class="bg-grid"></div><div class="bg-glow"></div>
<div class="card">
{inner}
<div class="footer">
  <div class="footer-logo">Producer Flow Academy — <span>The Book</span></div>
  <div class="footer-cta">{_esc(footer_right)}</div>
</div>
</div>
</body></html>"""


def _card_problem(item, brand):
    size = _fit_headline_size(item["headline"])
    return f"""
<div class="eyebrow">{_esc(item['eyebrow'])}</div>
<div class="content">
  <div class="headline" style="font-size:{size}px">{_esc(item['headline'])}</div>
  <p class="body-text">{_esc(item['body'])}</p>
</div>"""


def _card_quote(item, brand):
    size = _fit_headline_size(item["headline"], max_len_for_full=55)
    return f"""
<div class="eyebrow">{_esc(item['eyebrow'])}</div>
<div class="content">
  <div class="headline" style="font-size:{size}px;font-style:italic">{_esc(item['headline'])}</div>
  <p class="body-text">{_esc(item['body'])}</p>
</div>"""


def _card_insight(item, brand):
    size = _fit_headline_size(item["headline"], max_len_for_full=35)
    return f"""
<div class="eyebrow">{_esc(item['eyebrow'])}</div>
<div class="content">
  <div class="headline" style="font-size:{size}px">{_esc(item['headline'])}</div>
  <p class="body-text">{_esc(item['body'])}</p>
  <p class="pull">&ldquo;{_esc(item['pull'])}&rdquo;</p>
</div>"""


def _card_chapter(item, brand):
    tag = f'<span class="tag-pill">{_esc(item["tag"])}</span>' if item.get("tag") else ""
    size = _fit_headline_size(item["title"], max_len_for_full=35)
    return f"""
<div class="giant-num">{_esc(item['number'])}</div>
<div class="eyebrow">Inside the book — {_esc(item['number'])}</div>
<div class="content">
  <div class="headline" style="font-size:{size}px">{_esc(item['title'])}</div>
  <p class="body-text">{_esc(item['body'])}</p>
  {tag}
</div>"""


def _card_testimonial(item, brand):
    return f"""
<div class="eyebrow">What Producers Say</div>
<div class="content">
  <div class="quote-mark">&rdquo;</div>
  <div class="headline" style="font-size:40px;font-style:italic;margin-top:-40px">{_esc(item['quote'])}</div>
  <div class="testi-name">{_esc(item['name'])}</div>
  <div class="testi-role">{_esc(item['role'])}</div>
  <span class="result-pill">{_esc(item['result'])}</span>
</div>"""


def _card_stat(item, brand):
    return f"""
<div class="eyebrow">Producer Flow Academy</div>
<div class="content">
  <div class="stat-number">{_esc(item['number'])}</div>
  <div class="stat-label">{_esc(item['label'])}</div>
</div>"""


def _card_offer(item, brand):
    return f"""
<div class="giant-num">{_esc(item['number'])}</div>
<div class="eyebrow">Your Purchase Includes — {_esc(item['number'])}</div>
<div class="content">
  <div class="headline" style="font-size:64px">{_esc(item['title'])}</div>
  <p class="body-text">{_esc(item['body'])}</p>
</div>"""


def _card_qualifier(item, brand):
    icon = "&#10003;" if item["tone"] == "yes" else "&mdash;"
    color = "#5B9BD5" if item["tone"] == "yes" else "#F0F4F8"
    items_html = "\n".join(
        f'<li><span class="qual-icon" style="color:{color}">{icon}</span>{_esc(line)}</li>'
        for line in item["lines"]
    )
    return f"""
<div class="eyebrow">Is This Your Book?</div>
<div class="content">
  <div class="qual-heading" style="color:{color}">{_esc(item['heading'])}</div>
  <ul class="qual-list">{items_html}</ul>
</div>"""


_RENDERERS = {
    "problem": _card_problem,
    "quote": _card_quote,
    "insight": _card_insight,
    "chapter": _card_chapter,
    "testimonial": _card_testimonial,
    "stat": _card_stat,
    "offer": _card_offer,
    "qualifier": _card_qualifier,
}


def build_card_html(item, brand):
    renderer = _RENDERERS[item["card_type"]]
    footer_right = f"{brand['price']} · Bio"
    return _shell(renderer(item, brand), footer_right=footer_right)


def render_png(html_str, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    launch_kwargs = {}
    executable_override = os.environ.get("PLAYWRIGHT_CHROMIUM_PATH")
    if executable_override:
        launch_kwargs["executable_path"] = executable_override
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})
        page.set_content(html_str, wait_until="networkidle")
        page.screenshot(path=str(out_path))
        browser.close()
    return out_path
