"""Color/font themes and WCAG contrast checks.

All colors are 6-digit hex strings without the leading ``#`` (the form python-pptx
expects). Accent colors follow the Okabe-Ito idea: distinguishable under common
color-vision deficiencies and never the only carrier of meaning (use line style
and labels too).
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path


def _channel(v: int) -> float:
    c = v / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color: str) -> float:
    """WCAG 2.x relative luminance of ``RRGGBB``."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast_ratio(fg: str, bg: str) -> float:
    """WCAG contrast ratio between two colors (1.0 to 21.0)."""
    a, b = relative_luminance(fg), relative_luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


@dataclass(frozen=True)
class Theme:
    """A complete look for a deck. Create your own or tweak a preset with ``replace``."""

    name: str
    background: str
    ink: str
    muted: str
    rule: str
    accent: str
    accent2: str
    accent3: str
    dark_bg: str
    dark_ink: str = "FFFFFF"
    accent_on_dark: str = ""          # accent variant used on dark slides ("" = accent)
    dark: bool = False                # True when ``background`` itself is dark
    font_title: str = "Segoe UI Semibold"
    font_body: str = "Segoe UI"
    font_light: str = "Segoe UI Light"
    min_body: int = 18                # pt, smallest regular text
    min_caption: int = 14             # pt, captions, credits, sources, kickers
    min_number: int = 10              # pt, page numbers only
    fallback_fonts: tuple = field(default=("DejaVu Sans",))

    @property
    def on_dark_accent(self) -> str:
        return self.accent_on_dark or self.accent

    def check(self) -> list[str]:
        """Return human-readable contrast problems (empty list = OK)."""
        bad: list[str] = []

        def need(label: str, fg: str, bg: str, minimum: float) -> None:
            r = contrast_ratio(fg, bg)
            if r < minimum:
                bad.append(f"{self.name}: {label} {fg} on {bg} = {r:.2f} (< {minimum})")

        need("ink", self.ink, self.background, 7.0)
        need("muted", self.muted, self.background, 4.5)
        need("accent", self.accent, self.background, 4.5)
        need("accent2", self.accent2, self.background, 3.0)
        need("accent3", self.accent3, self.background, 3.0)
        need("dark_ink", self.dark_ink, self.dark_bg, 7.0)
        need("accent_on_dark", self.on_dark_accent, self.dark_bg, 4.5)
        return bad

    def to_dict(self) -> dict:
        d = asdict(self)
        d["fallback_fonts"] = list(self.fallback_fonts)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Theme":
        data = dict(data)
        if "fallback_fonts" in data:
            data["fallback_fonts"] = tuple(data["fallback_fonts"])
        return cls(**data)


PRESETS: dict[str, Theme] = {t.name: t for t in (
    Theme("paper-blue", background="FAFAF7", ink="15171A", muted="5F636B", rule="D9D7D2",
          accent="0072B2", accent2="D55E00", accent3="007A5A", dark_bg="0B1F33",
          accent_on_dark="56B4E9"),
    Theme("night-amber", background="14161A", ink="F2EFE8", muted="A6A9B0", rule="3A3D44",
          accent="F5A623", accent2="56B4E9", accent3="CC79A7", dark_bg="0D0F12",
          dark_ink="F2EFE8", dark=True, font_title="Calibri", font_body="Calibri",
          font_light="Calibri Light"),
    Theme("forest-teal", background="F3F8F5", ink="10241D", muted="4F625A", rule="C9D8D0",
          accent="0B6E5F", accent2="B35A00", accent3="6A4C93", dark_bg="0B2B25",
          accent_on_dark="5FD3BC", font_title="Trebuchet MS", font_body="Trebuchet MS",
          font_light="Trebuchet MS"),
    Theme("graphite-coral", background="F5F5F6", ink="202329", muted="5A5F69", rule="D3D5DA",
          accent="C23B2E", accent2="2F5D8C", accent3="5B7A1F", dark_bg="25282E",
          accent_on_dark="FF8A7A", font_title="Arial", font_body="Arial", font_light="Arial"),
    Theme("sand-terracotta", background="F6EFE4", ink="2B2118", muted="64544A", rule="DCCDB8",
          accent="A63F1B", accent2="2A6B73", accent3="7A5C00", dark_bg="3A2A1E",
          accent_on_dark="F2A27C", font_title="Georgia", font_body="Georgia",
          font_light="Georgia"),
    Theme("ink-violet", background="FBFAFE", ink="1A1530", muted="5A5474", rule="DAD6EA",
          accent="5B3FB5", accent2="B35400", accent3="0F7480", dark_bg="1B1440",
          accent_on_dark="B7A4F5", font_title="Verdana", font_body="Verdana",
          font_light="Verdana"),
)}


def get_theme(theme: "str | Theme | None" = None) -> Theme:
    """Resolve a preset name, a JSON/YAML theme file path, or a Theme instance."""
    if theme is None:
        return PRESETS["paper-blue"]
    if isinstance(theme, Theme):
        return theme
    if theme in PRESETS:
        return PRESETS[theme]
    path = Path(theme)
    if path.is_file():
        return load_theme(path)
    raise KeyError(f"unknown theme {theme!r}; presets: {', '.join(PRESETS)}")


def load_theme(path: "str | Path") -> Theme:
    """Load a theme from JSON or YAML (needs ``pyyaml``). Missing keys use defaults."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        import yaml  # optional dependency
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    return Theme.from_dict(data)


__all__ = ["Theme", "PRESETS", "get_theme", "load_theme", "contrast_ratio",
           "relative_luminance", "replace"]
