"""Ready-made slide layouts. Each takes a ``Deck`` and returns the new slide."""
from __future__ import annotations

import math
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

from .deck import CONTENT_W, H, MARGIN, W, Deck


def title_slide(d: Deck, title: str, subtitle: str = "", byline: str = ""):
    """Dark opening slide: big title, accent bar, subtitle and byline."""
    t = d.theme
    s = d.slide(dark=True)
    d.rect(s, MARGIN, 2.2, 0.9, 0.08, t.on_dark_accent, "accent_bar")
    d.text(s, title, MARGIN, 2.5, 10.5, 1.9, 46, t.dark_ink, t.font_title, "title", spacing=0.95)
    if subtitle:
        d.text(s, subtitle, MARGIN, 4.5, 10.5, 0.9, 24, t.dark_ink, t.font_light, "subtitle")
    if byline:
        d.text(s, byline, MARGIN, 6.2, 10.5, 0.4, 18, t.on_dark_accent, t.font_body, "byline")
    return s


def section(d: Deck, kicker: str, title: str, figure=None, alt: str = "", caption: str = ""):
    """Section divider: large light title on the left, optional figure on the right."""
    t = d.theme
    s = d.slide(kicker)
    d.text(s, title, MARGIN, 2.3, 5.6, 2.7, 40, t.ink, t.font_light, "title", spacing=1.0)
    if figure:
        d.pic(s, figure, 6.7, 1.55, 5.88, 4.75, alt=alt, name="figure")
        if caption:
            d.text(s, caption, 6.7, 6.4, 5.88, 0.3, 14, t.muted, name="caption")
    return s


def bullets_figure(d: Deck, kicker: str, title: str, bullets: list[str], figure,
                   alt: str = "", caption: str = "", source: str = "", size: int = 22):
    """Left: up to ~5 short bullets. Right: a figure. Footer: source of numbers."""
    t = d.theme
    s = d.slide(kicker, title)
    y, step = 2.55, 0.92
    for b in bullets:
        d.circle(s, MARGIN, y + 0.1, 0.13, t.accent, "bullet_dot")
        d.text(s, b, MARGIN + 0.35, y, 5.3, step - 0.1, size, t.ink, name="bullet")
        y += step
    d.pic(s, figure, 6.9, 2.45, 5.68, 3.9, alt=alt, name="figure", fit=True)
    if caption:
        d.text(s, caption, 6.9, 6.35, 5.68, 0.3, 14, t.muted, name="caption")
    if source:
        d.text(s, source, MARGIN, 6.7, 10.0, 0.3, 14, t.muted, name="source")
    return s


def timeline(d: Deck, kicker: str, title: str, rows: list[tuple[str, str, str]],
             progress: tuple[int, int] | None = None):
    """Rows of ``(year, event, detail)``: accent year, semibold event, muted detail."""
    t = d.theme
    s = d.slide(kicker, title)
    y = 2.45
    step = min(1.05, 4.2 / max(len(rows), 1))
    for year, event, detail in rows:
        d.line(s, MARGIN, y - 0.1, W - MARGIN, y - 0.1, t.rule, 0.75, "row_rule")
        d.text(s, year, MARGIN, y, 1.6, 0.5, 26, t.accent, t.font_title, "year")
        d.text(s, event, 2.6, y, 4.6, 0.5, 22, t.ink, t.font_title, "event")
        d.text(s, detail, 7.4, y + 0.04, 5.18, 0.7, 18, t.muted, name="detail")
        y += step
    if progress:
        d.carrier(s, *progress)
    return s


def darken_side(path, out, fraction: float = 0.42, color: str = "000000",
                strength: float = 0.88, max_px: int = 1920) -> Path:
    """Fade the left ``fraction`` of an image toward ``color`` so light text stays legible."""
    im = Image.open(path).convert("RGB")
    im.thumbnail((max_px, max_px))
    w, h = im.size
    cut = int(w * fraction)
    ramp = np.zeros(w)
    ramp[:cut] = strength * (1 - 0.65 * np.arange(cut) / cut)
    base = np.asarray(im, float)
    tint = np.array([int(color[i:i + 2], 16) for i in (0, 2, 4)], float)
    a = ramp[None, :, None]
    im = Image.fromarray((base * (1 - a) + tint * a).astype("uint8"))
    out = Path(out)
    im.save(out, quality=88)
    return out


def opener(d: Deck, image, title: str, subtitle: str = "", credit: str = "", alt: str = "",
           ai_generated: bool = False):
    """Full-bleed image; text sits on the darkened left third. Credit bottom right."""
    t = d.theme
    s = d.slide(dark=True)
    with tempfile.TemporaryDirectory() as tmp:
        dark = darken_side(image, Path(tmp) / "opener.jpg", color=t.dark_bg)
        d.full_bleed(s, dark, alt=alt or title)
    d.rect(s, MARGIN, 2.3, 0.9, 0.08, t.on_dark_accent, "accent_bar")
    d.text(s, title, MARGIN, 2.6, 4.4, 2.6, 36, t.dark_ink, t.font_title, "title", spacing=0.98)
    if subtitle:
        d.text(s, subtitle, MARGIN, 5.3, 4.4, 0.9, 20, t.dark_ink, t.font_light, "subtitle")
    if credit or ai_generated:
        text = credit + (" " if credit and ai_generated else "") + \
            ("AI-generated illustration." if ai_generated else "")
        d.text(s, text, 6.0, 6.55, 6.58, 0.3, 14, "FFFFFF", name="credit", align="right")
    return s


def names_reveal(d: Deck, kicker: str, title: str, people: list[tuple[str, str]]):
    """Names appear one per click (fade) followed by a pulse; ``people`` = (name, role)."""
    t = d.theme
    s = d.slide(kicker, title)
    cols = 2 if len(people) > 4 else 1
    per_col = math.ceil(len(people) / cols)
    rows = []
    for i, (name, role) in enumerate(people):
        col, r = divmod(i, per_col)
        x = MARGIN + col * 6.0
        y = 2.55 + r * 1.0
        n = d.text(s, name, x, y, 5.6, 0.5, 26, t.ink, t.font_title, "person_name")
        ro = d.text(s, role, x, y + 0.48, 5.6, 0.4, 18, t.muted, name="person_role")
        g = d.group(s, [n, ro], f"person_{i + 1}")
        rows += [(g, "fade", "click"), (g, "pulse", "after")]
    d.anim(s, rows)
    return s


def layers_figure(d: Deck, kicker: str, title: str, layers: list, captions: list[str],
                  alt: str = "", notes: str = ""):
    """Stacked transparent figure layers revealed one per click, each with a side caption."""
    t = d.theme
    s = d.slide(kicker, title)
    colors = [t.accent, t.accent2, t.accent3]
    rows = []
    for i, (layer, cap) in enumerate(zip(layers, captions)):
        pic = d.pic(s, layer, MARGIN, 2.45, 7.65, 3.95, alt=f"{alt} (layer {i + 1})",
                    name=f"layer_{i + 1}", fit=True)
        text = d.text(s, cap, 8.9, 2.9 + i * 1.1, 3.68, 0.9, 20, colors[i % 3], t.font_title,
                      f"layer_text_{i + 1}")
        rows += [(pic, "fade", "click"), (text, "fade", "with")]
    d.anim(s, rows)
    if notes:
        d.notes(s, notes)
    return s


def closing(d: Deck, title: str, lines: list[str]):
    """Dark closing slide with contact/thanks lines."""
    t = d.theme
    s = d.slide(dark=True)
    d.rect(s, MARGIN, 2.2, 0.9, 0.08, t.on_dark_accent, "accent_bar")
    d.text(s, title, MARGIN, 2.5, 10.5, 1.4, 44, t.dark_ink, t.font_title, "title")
    for i, line in enumerate(lines):
        d.text(s, line, MARGIN, 4.3 + i * 0.6, 10.5, 0.5, 22, t.on_dark_accent if i == 0
               else t.dark_ink, t.font_body, "contact")
    return s
