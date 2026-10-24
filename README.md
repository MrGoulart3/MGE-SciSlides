# MGE-SciSlides

[Leia em português](README.pt-BR.md)

A small, self-contained Python toolkit for making **scientific and academic presentations**
(`.pptx`) with [python-pptx](https://python-pptx.readthedocs.io): themed 16:9 decks, ready
layouts, click animations, a deck checker, media helpers (video montage, molecule figures,
energy profiles) and a render-and-look loop.

It grew out of a real talk for first-year students and keeps the lessons: one idea per slide,
big type, a progress line, click-by-click reveals, and always rendering the deck to *look* at it.

![palettes](docs/img/palettes.png)

## Features

| Area | What you get |
|---|---|
| `scislides.theme` | 6 color-blind-aware presets (light and dark), WCAG contrast checker, your own theme from JSON/YAML |
| `scislides.deck` | `Deck`: kicker + assertion title, page number, text with enforced minimum sizes, picture fit/crop, full-bleed, notes, groups, progress "carrier" line, fade/appear/pulse click animations, fade/morph transitions (self-written XML, no external skill) |
| `scislides.layouts` | title, section divider, bullets + figure, timeline, full-bleed opener, names revealed one per click, figure layers revealed per click, closing |
| `scislides.edit` | edit existing decks: find shape, set text, remove, reorder, renumber, replace an image/GIF in place, drop orphan animations |
| `scislides.check` | verifier: font floors, shapes off-slide, overflow heuristic, missing alt text, file-size budget, forbidden characters |
| `scislides.render` | pptx to PDF (LibreOffice) to PNG (pdftoppm) to contact sheet |
| `scislides.media.video` | search, download, contact sheets, flash detection, scene cuts, subtitles (yt-dlp + ffmpeg) |
| `scislides.media.montage` | captioned MP4 with sound plus palette GIF from a YAML/JSON spec: crop, slow motion, labels, end card |
| `scislides.media.molecules` | RDKit 2D formulas; rotating 3D GIFs from XYZ/SMILES (3Dmol.js + headless Chromium) |
| `scislides.media.plots` | energy profile exported as transparent layers for click reveal, theme swatches |

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .              # core: python-pptx, lxml, Pillow, numpy, matplotlib
pip install -e '.[molecules]' # optional: rdkit, playwright  (then: playwright install chromium)
pip install -e '.[video]'     # optional: yt-dlp, pyyaml
```

External programs (optional, only for the features that need them): `soffice` (LibreOffice)
and `pdftoppm` (poppler) for rendering; `ffmpeg` for video (or set `FFMPEG=/path/to/ffmpeg`).

## Quick start

```python
from scislides import Deck, layouts

d = Deck("night-amber", title="My talk", author="A. Researcher")
layouts.title_slide(d, "Why molecules wiggle", "A short introduction", "A. Researcher")
s = layouts.timeline(d, "History", "Three ideas, three decades",
                     [("1990", "Idea one", "What changed"), ("2005", "Idea two", "Why it mattered")])
d.notes(s, "Say the dates last, not first.")
d.save("out/talk.pptx")
```

Or run the full demo with any theme:

```bash
python examples/demo_deck.py --list-themes
python examples/demo_deck.py --theme forest-teal -o out/demo.pptx
scislides-check out/demo.pptx
scislides-render out/demo.pptx -o out/render     # PDF, PNGs and contact.png
```

## Command-line tools

| Command | Purpose |
|---|---|
| `scislides-check deck.pptx [--forbid "—"]` | verify a deck; exit code 1 on errors |
| `scislides-render deck.pptx -o dir` | render to PDF/PNG and a contact sheet |
| `scislides-video search\|download\|sheet\|flash\|cuts\|subs` | footage research helpers |
| `scislides-montage spec.yaml` | build a captioned montage and GIF |
| `scislides-mol 2d SMILES out.png` / `scislides-mol gif SMILES_or_XYZ out.gif` | molecule figures |

## Documentation

- [docs/GUIDE.md](docs/GUIDE.md): design rules that make talks work
- [docs/THEMES.md](docs/THEMES.md): presets, previews, writing your own
- [docs/MEDIA.md](docs/MEDIA.md): finding footage, montage, GIF sizes, provenance, ethics, AI illustration
- [docs/MOLECULES.md](docs/MOLECULES.md): 2D and 3D molecule figures

## Related projects

- **[mpl-animation](https://github.com/hugogontijomachado/mpl-animation)** by
  [@hugogontijomachado](https://github.com/hugogontijomachado): animated explainer clips with
  matplotlib, built from steps that each end in a pause. It renders MP4/GIF, cuts the clips at the
  pauses, and can build a PowerPoint deck where each click plays the next clip. Use it when a chart
  should *move* on stage. It pairs well with `scislides.media.plots` (static layers) and with the
  GIF tools here.
- **[MGE-MolecularMotionVideo](https://github.com/MrGoulart3/MGE-MolecularMotionVideo)**: a skill
  for narrated, scientifically accurate molecular motion videos. It uses Blender with real
  geometry and motion from calculations (MD, IRC/NEB, normal modes), plus text-to-speech and
  captions. Use it when a GIF is not enough and the slide needs a short film.

## Tests

```bash
pip install -e '.[test]' && pytest
```

Tests needing optional pieces (RDKit, ffmpeg) skip themselves when those are missing.

## License

MIT. See [LICENSE](LICENSE). Footage, images and fonts you use remain under their own licenses.
