"""Theme-aware figures for slides: energy profiles as click-reveal layers, palette swatches."""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np

from ..theme import PRESETS, Theme, get_theme


def _mpl(theme: Theme):
    os.environ.setdefault("MPLBACKEND", "Agg")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    have = {f.name for f in font_manager.fontManager.ttflist}
    fams = [f for f in (theme.font_body, *theme.fallback_fonts) if f in have] or ["DejaVu Sans"]
    plt.rcParams.update({
        "font.family": fams,
        "axes.unicode_minus": False, "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": 0.8,
    })
    return plt


def energy_profile_layers(states: list[str], series: list[dict], out_dir, theme=None,
                          ylabel: str = "Relative energy / kcal/mol",
                          xlabel: str = "Reaction coordinate", cumulative: bool = False,
                          size: tuple[float, float] = (7.65, 3.95), dpi: int = 200,
                          prefix: str = "layer") -> list[Path]:
    """Render one transparent PNG per series, all with identical geometry.

    ``series`` items: ``{"label": "ΔG", "values": [...], "color": "accent"|hex,
    "style": "-"|"--"|":"}``. The first layer carries the axes. Stack the PNGs in the same
    box and reveal them one per click. With ``cumulative=True`` layer *i* also repeats
    series 1..i-1 (use it when layers replace each other instead of stacking).
    """
    theme = get_theme(theme)
    plt = _mpl(theme)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    n = len(states)
    allv = np.concatenate([np.asarray(s["values"], float) for s in series])
    pad = 0.12 * (allv.max() - allv.min())
    ylim = (allv.min() - pad, allv.max() + pad)
    palette = {"accent": theme.accent, "accent2": theme.accent2, "accent3": theme.accent3}

    def smooth(y):
        xx, yy = [], []
        for i in range(n - 1):
            t = np.linspace(0, 1, 65)
            xx.extend(i + t)
            yy.extend(y[i] + (y[i + 1] - y[i]) * (0.5 - 0.5 * np.cos(np.pi * t)))
        return xx, yy

    paths = []
    for k in range(len(series)):
        fig = plt.figure(figsize=size, dpi=dpi)
        ax = fig.add_axes([0.16, 0.20, 0.80, 0.72])
        ax.set_xlim(-0.2, n - 0.3 + 0.5)
        ax.set_ylim(*ylim)
        ax.set_facecolor("none")
        fig.patch.set_alpha(0)
        if k == 0:
            ax.spines[["left", "bottom"]].set_color("#" + theme.rule)
            ax.set_xticks(range(n), states)
            ax.tick_params(length=0, pad=7, labelsize=14, colors="#" + theme.muted)
            ax.set_ylabel(ylabel, fontsize=16, labelpad=9, color="#" + theme.ink)
            ax.set_xlabel(xlabel, fontsize=16, labelpad=12, color="#" + theme.ink)
            ax.axhline(0, color="#" + theme.rule, lw=0.8, zorder=0)
            ax.grid(axis="y", color="#" + theme.rule, lw=0.5, alpha=0.5)
        else:
            ax.set_axis_off()
        shown = range(k + 1) if cumulative else [k]
        for j in shown:
            s = series[j]
            y = np.asarray(s["values"], float)
            col = "#" + palette.get(s.get("color", "accent"), s.get("color", theme.accent))
            xx, yy = smooth(y)
            ax.plot(xx, yy, color=col, lw=3 if j == len(series) - 1 else 2,
                    ls=s.get("style", "-"))
            ax.scatter(range(n), y, color=col, s=16, zorder=4)
            ax.text(n - 1 + 0.18, y[-1], s["label"], color=col, ha="left", va="center",
                    fontsize=17, fontweight="bold")
        path = out_dir / f"{prefix}_{k + 1}.png"
        fig.savefig(path, transparent=True, dpi=dpi)
        plt.close(fig)
        paths.append(path)
    return paths


def swatch_image(themes: "list[str | Theme] | None", path, width: int = 1200) -> Path:
    """One row per theme: background chip with ink, muted, rule and the three accents."""
    from PIL import Image, ImageDraw, ImageFont
    items = [get_theme(t) for t in (themes or list(PRESETS))]
    row, label_w = 70, 220
    img = Image.new("RGB", (width, row * len(items) + 20), "white")
    d = ImageDraw.Draw(img)
    try:
        from matplotlib import font_manager
        font = ImageFont.truetype(font_manager.findfont("DejaVu Sans"), 20)
    except Exception:  # pragma: no cover - font lookup is best effort
        font = ImageFont.load_default()
    chip = (width - label_w - 20) // 8
    for i, t in enumerate(items):
        y = 10 + i * row
        d.text((14, y + 20), t.name, fill="#222222", font=font)
        cols = [t.background, t.dark_bg, t.ink, t.muted, t.accent, t.accent2, t.accent3,
                t.rule]
        for j, c in enumerate(cols):
            x = label_w + j * chip
            d.rectangle([x, y, x + chip - 6, y + row - 10], fill="#" + c, outline="#999999")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=True)
    return path
