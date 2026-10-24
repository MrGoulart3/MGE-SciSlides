# Molecule figures

Install: `pip install -e '.[molecules]'` and `playwright install chromium`.

## 2D skeletal formulas (RDKit)

```python
from scislides.media.molecules import depict_2d
depict_2d("CN1C=NC2=C1C(=O)N(C(=O)N2C)C", "caffeine.png", size=(900, 700),
          background=None, color="15171A")   # transparent PNG in the ink color
```

Publication style: single-color atoms, uniform bond width, generous padding. Use
`background=None` plus `color=theme.ink` so the figure works on light and dark themes.
CLI: `scislides-mol 2d "CC(=O)Oc1ccccc1C(=O)O" aspirin.png --transparent`.

## Rotating 3D GIF (3Dmol.js + headless Chromium)

```python
from scislides.media.molecules import rotating_gif
rotating_gif("CN1C=NC2=C1C(=O)N(C(=O)N2C)C", "caffeine.gif", frames=36, size=(480, 480),
             fps=18, background="FFFFFF")
rotating_gif("my_molecule.xyz", "mine.gif", threedmol_js="3Dmol-min.js")   # offline
```

- `source` is an `.xyz` file (any geometry, e.g. from your own calculation) or a SMILES
  string (embedded with ETKDG and relaxed with MMFF/UFF; needs RDKit).
- 3Dmol.js is loaded from a CDN by default; pass `threedmol_js` for offline use.
- Chromium: Playwright's own build, or any Chrome/Chromium via `chromium=` / `CHROMIUM_PATH`.
- The background is a solid color (GIF has no partial transparency): match your slide.
- 36 frames at 480 px with 64 colors is roughly 150 to 400 kB. Use fewer frames for a
  faster spin, and keep GIFs below ~2 MB each.
- Put the GIF in a slide with `Deck.pic`; to swap one later without touching layout, use
  `scislides.edit.replace_blob`.

CLI: `scislides-mol gif "SMILES or file.xyz" out.gif --frames 36 --size 480 --js 3Dmol-min.js`.

If RDKit or Playwright is missing, the functions raise `MissingDependency` with the install
command and the CLI exits with code 2.

## Energy profiles

`scislides.media.plots.energy_profile_layers(states, series, out_dir, theme)` writes one
transparent PNG per series with identical geometry (the first carries the axes). Stack them in
the same box and reveal one per click: `layouts.layers_figure`. Use real numbers from your
calculation and cite the method in the slide footer.
