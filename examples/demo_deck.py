"""Build a short demo deck for any theme.

    python examples/demo_deck.py --theme night-amber -o out/demo.pptx
    python examples/demo_deck.py --list-themes

Everything (figures, the opener illustration) is generated on the fly; the content is
fictitious. RDKit is optional: without it the molecule figure falls back to a text card.
"""
from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from scislides import PRESETS, Deck, get_theme, layouts
from scislides.media.plots import energy_profile_layers


def opener_art(theme, path: Path, size=(1920, 1080)) -> Path:
    """Abstract hexagon-lattice illustration in theme colors (stand-in for a real image)."""
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w]
    base = np.array([int(theme.dark_bg[i:i + 2], 16) for i in (0, 2, 4)], float)
    glow = np.array([int(theme.accent2[i:i + 2], 16) for i in (0, 2, 4)], float)
    k = np.exp(-(((xx - w * 0.72) / (w * 0.35)) ** 2 + ((yy - h * 0.45) / (h * 0.55)) ** 2))
    img = Image.fromarray((base + (glow - base) * 0.55 * k[..., None]).astype("uint8"))
    d = ImageDraw.Draw(img, "RGBA")
    acc = tuple(int(theme.on_dark_accent[i:i + 2], 16) for i in (0, 2, 4))
    r = 70
    for row in range(-1, 14):
        for col in range(-1, 20):
            cx = col * r * 1.732 + (r * 0.866 if row % 2 else 0)
            cy = row * r * 1.5
            if cx < w * 0.4:
                continue
            pts = [(cx + r * 0.95 * np.cos(np.pi / 3 * i + np.pi / 6),
                    cy + r * 0.95 * np.sin(np.pi / 3 * i + np.pi / 6)) for i in range(6)]
            d.polygon(pts, outline=acc + (110,))
    img.save(path)
    return path


def molecule_card(theme, path: Path, smiles: str, label: str) -> Path:
    """RDKit 2D depiction if available, else a plain text card."""
    from scislides.media.molecules import MissingDependency, depict_2d
    try:
        return depict_2d(smiles, path, size=(900, 700), background=None, color=theme.ink)
    except MissingDependency:
        img = Image.new("RGB", (900, 700), "#" + theme.background)
        ImageDraw.Draw(img).text((40, 40), label, fill="#" + theme.ink)
        img.save(path)
        return path


def build(theme_name: str, out: Path) -> Path:
    os.environ.setdefault("OMP_NUM_THREADS", "2")
    theme = get_theme(theme_name)
    d = Deck(theme, title="Demo: from molecule to mechanism", author="Example Author",
             lang="en-US")
    tmp = Path(tempfile.mkdtemp(prefix="scislides_demo_"))

    s = layouts.title_slide(d, "Demo: from molecule to mechanism",
                            "Toolkit example with fictitious content", "Example Author · Example Lab")
    d.transition(s)

    s = layouts.opener(d, opener_art(theme, tmp / "art.png"), "How a molecule becomes a story",
                       "A fictitious talk for first-year students",
                       alt="Abstract hexagon lattice glowing on a dark background",
                       ai_generated=False)
    d.notes(s, "Open with the question, not the title. Pause two seconds.")

    s = layouts.section(d, "Part 1", "What is in your coffee?",
                        molecule_card(theme, tmp / "caffeine.png",
                                      "CN1C=NC2=C1C(=O)N(C(=O)N2C)C", "caffeine"),
                        alt="Skeletal formula of caffeine", caption="Caffeine, C8H10N4O2")

    s = layouts.bullets_figure(
        d, "Part 1", "One small ring change turns a stimulant into a painkiller",
        ["Caffeine: a purine with three methyl groups", "Aspirin: a benzene ring with an ester",
         "Shape decides which receptor listens"],
        molecule_card(theme, tmp / "aspirin.png", "CC(=O)OC1=CC=CC=C1C(=O)O", "aspirin"),
        alt="Skeletal formula of aspirin", caption="Aspirin, C9H8O4",
        source="Source: textbook values, fictitious example.")
    d.carrier(s, 1, 3, ["Molecules", "Energy", "People"])

    layers = energy_profile_layers(
        ["Reactant", "TS1", "Int", "TS2", "Product"],
        [{"label": "ΔH", "values": [0, 14, -22, -6, -48], "color": "accent", "style": "--"},
         {"label": "−TΔS", "values": [0, 6, 7, 6, 9], "color": "accent2", "style": ":"},
         {"label": "ΔG", "values": [0, 20, -15, 0, -32], "color": "accent3", "style": "-"}],
        tmp / "layers", theme)
    s = layers_s = layouts.layers_figure(
        d, "Part 2", "The free energy tells the story the enthalpy alone cannot", layers,
        ["Enthalpy: bonds made and broken", "Entropy term: order lost on the way",
         "Free energy: the sum decides the pathway"],
        alt="Energy profile of a fictitious two-step reaction",
        notes="Click once per layer; say the idea before the curve appears.")
    d.carrier(s, 2, 3)

    s = layouts.timeline(d, "Part 3", "A fictitious lab grew in four steps",
                         [("2015", "Founded", "Two students, one borrowed fume hood"),
                          ("2018", "First paper", "Open data and a short methods note"),
                          ("2021", "Shared instrument", "Joint purchase with a neighbor lab"),
                          ("2024", "Teaching module", "Course unit built from the lab's data")],
                         progress=(3, 3))
    d.transition(s, morph=False)

    layouts.names_reveal(d, "Part 3", "Thanks to the team",
                         [("Ada Example", "Group leader"), ("Ben Sample", "Postdoc"),
                          ("Chi Placeholder", "PhD student"), ("Dana Demo", "Technician")])

    layouts.closing(d, "Questions?", ["hello@example.org", "github.com/example/scislides"])
    return d.save(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--theme", default="paper-blue",
                    help="preset name or path to a JSON/YAML theme file")
    ap.add_argument("-o", "--out", default="out/demo.pptx")
    ap.add_argument("--list-themes", action="store_true")
    a = ap.parse_args()
    if a.list_themes:
        print("\n".join(PRESETS))
        return
    print(build(a.theme, Path(a.out)))


if __name__ == "__main__":
    main()
