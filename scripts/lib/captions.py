"""Caption copywriting: templates per card_type, hashtag rotation, and assembly.

Voice: confident, direct, mentor-not-hype-bro — matching the landing page's
"essential guide" positioning. Two template variants per card_type so the
wording changes each time a piece of content comes back around in a new cycle.
"""

CTA_VARIANTS = [
    "The full method — with the framework, the workflow, and the sound identity "
    "system behind it — is in the book. Link in bio → producerflowacademy.com",
    "This is one page of it. The complete system is in The Producer Flow Method — "
    "link in bio, instant PDF, {price}.",
    "Want the whole framework, not just the fragment? The Producer Flow Method is "
    "in bio. {price}, instant download.",
]

HASHTAG_BRAND = ["#ProducerFlowMethod", "#ProducerFlowAcademy"]

HASHTAG_POOL = [
    "#MusicProduction", "#MusicProducer", "#ElectronicMusicProducer",
    "#HouseMusicProducer", "#TechHouse", "#StudioLife", "#AbletonLive",
    "#FLStudio", "#BedroomProducer", "#MusicProductionTips", "#SoundDesign",
    "#ElectronicMusic", "#HouseMusic", "#TechnoMusic", "#MusicMakers",
    "#ProducerLife", "#MixingAndMastering", "#DeepHouse", "#ProgressiveHouse",
    "#MelodicHouse", "#MusicCareer", "#DJLife", "#UndergroundHouse", "#SignedArtist",
]

TEMPLATES = {
    "problem": [
        "{headline}\n\n{body}\n\nSound familiar? It's not a talent problem — it's a "
        "systems problem.\n\nThe Producer Flow Method breaks down exactly where the "
        "real work happens (hint: it's not the mix).\n\n{cta}",
        "Be honest — does this sound like you?\n\n“{headline}”\n\n{body}\n\n"
        "That's exactly what The Producer Flow Method was built to fix.\n\n{cta}",
    ],
    "quote": [
        "{headline}\n\n{body}\n\nMost producers spend all their energy fixing in the "
        "mix what should've been handled three stages earlier.\n\n{cta}",
        "Save this one.\n\n{headline}\n\n{body}\n\n{cta}",
    ],
    "insight": [
        "Big Shift: {headline}\n\n{body}\n\n“{pull}”\n\n{cta}",
        "Unlearn this: {headline}\n\n{body}\n\n{pull}\n\n{cta}",
    ],
    "chapter": [
        "Inside the book — {number}: {title}\n\n{body}\n\n{cta}",
        "What you'll actually learn ({title}):\n\n{body}\n\n{cta}",
    ],
    "testimonial": [
        "“{quote}”\n\n— {name}, {role}\n{result}\n\nReal producer, real "
        "result. That's what happens when you fix the system instead of chasing "
        "another plugin.\n\n{cta}",
        "This is why the method exists.\n\n“{quote}”\n\n— {name} ({role})\n"
        "{result}\n\n{cta}",
    ],
    "stat": [
        "{number} {label}.\n\nThe Producer Flow Method isn't theory — it's the "
        "distillation of two decades in real studios with real releases.\n\n{cta}",
        "{number} — {label}.\n\nEvery page of the book is built on this, not on "
        "guesswork.\n\n{cta}",
    ],
    "offer": [
        "What's inside — {title}\n\n{body}\n\n{cta}",
        "Part of what you get: {title}.\n\n{body}\n\n{cta}",
    ],
    "qualifier_yes": [
        "Is this your book?\n\nThis is for you if:\n{lines}\n\n{cta}",
        "Read this list. If more than two hit — keep reading.\n\n{lines}\n\n{cta}",
    ],
    "qualifier_no": [
        "To be clear about who this ISN'T for:\n\n{lines}\n\nThis isn't a beginner "
        "tutorial pack. It's a creative system for producers ready to do the "
        "work.\n\n{cta}",
        "Honesty first. The Producer Flow Method is not for you if:\n\n{lines}\n\n"
        "If none of those are you — you're exactly who this was written for.\n\n{cta}",
    ],
}


def _format_lines(lines):
    return "\n".join(f"→ {line}" for line in lines)


def rotating_hashtags(cycle, count=10):
    if not HASHTAG_POOL:
        return list(HASHTAG_BRAND)
    start = (cycle * 4) % len(HASHTAG_POOL)
    rotated = HASHTAG_POOL[start:] + HASHTAG_POOL[:start]
    return HASHTAG_BRAND + rotated[:count]


def render_caption(item, brand, cycle):
    card_type = item["card_type"]
    key = card_type
    if card_type == "qualifier":
        key = "qualifier_yes" if item["tone"] == "yes" else "qualifier_no"

    templates = TEMPLATES[key]
    template = templates[cycle % len(templates)]
    cta = CTA_VARIANTS[cycle % len(CTA_VARIANTS)].format(price=brand["price"])

    fields = dict(item)
    fields["cta"] = cta
    fields["price"] = brand["price"]
    if "lines" in fields:
        fields["lines"] = _format_lines(fields["lines"])

    body = template.format(**fields)
    tags = " ".join(rotating_hashtags(cycle))
    return f"{body}\n\n.\n.\n.\n{tags}"
