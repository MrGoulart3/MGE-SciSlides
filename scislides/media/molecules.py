"""Molecule figures: RDKit 2D depictions and rotating 3D GIFs (3Dmol.js + headless Chromium).

Optional dependencies: ``rdkit`` for SMILES handling, ``playwright`` (plus a Chromium
build: ``playwright install chromium``) for the 3D GIF. Missing pieces raise
``MissingDependency`` with the install command.
"""
from __future__ import annotations

import argparse
import base64
import io
import os
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageOps

THREEDMOL_URL = "https://cdnjs.cloudflare.com/ajax/libs/3Dmol/2.4.2/3Dmol-min.js"


class MissingDependency(RuntimeError):
    """An optional package or program is not installed."""


def _rdkit():
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem, Draw
        from rdkit.Chem.Draw import rdMolDraw2D
    except ImportError as exc:
        raise MissingDependency("RDKit is required: pip install 'scislides[molecules]'") from exc
    return Chem, AllChem, Draw, rdMolDraw2D


def depict_2d(smiles: str, out, size: tuple[int, int] = (900, 700),
              background: str | None = "FFFFFF", bond_width: float = 2.0,
              color: str = "000000") -> Path:
    """Publication-style skeletal formula as PNG.

    Single-color atoms (no CPK palette), uniform bond width, clean text. ``background=None``
    gives a transparent PNG.
    """
    Chem, AllChem, _, rdMolDraw2D = _rdkit()
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"invalid SMILES: {smiles!r}")
    drawer = rdMolDraw2D.MolDraw2DCairo(*size)
    opts = drawer.drawOptions()
    AllChem.Compute2DCoords(mol)
    opts.bondLineWidth = bond_width
    opts.multipleBondOffset = 0.14
    opts.padding = 0.08
    opts.baseFontSize = 0.6
    transparent = background is None
    # transparent output: draw black on white, then turn darkness into alpha in ``color``
    rgb = (0.0, 0.0, 0.0) if transparent else tuple(int(color[i:i + 2], 16) / 255
                                                   for i in (0, 2, 4))
    opts.setSymbolColour(rgb)
    opts.updateAtomPalette({k: rgb for k in range(0, 119)})
    opts.setBackgroundColour((1.0, 1.0, 1.0, 1.0) if transparent else
                             tuple(int(background[i:i + 2], 16) / 255 for i in (0, 2, 4)) + (1,))
    drawer.DrawMolecule(mol)
    drawer.FinishDrawing()
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(io.BytesIO(drawer.GetDrawingText()))
    if transparent:
        alpha = ImageOps.invert(img.convert("L"))
        img = Image.new("RGBA", img.size, "#" + color)
        img.putalpha(alpha)
    img.save(out)
    return out


def smiles_to_xyz(smiles: str, seed: int = 7) -> str:
    """Embed in 3D with ETKDG, relax with MMFF (or UFF) and return an XYZ block."""
    Chem, AllChem, _, _ = _rdkit()
    mol = Chem.AddHs(Chem.MolFromSmiles(smiles))
    if AllChem.EmbedMolecule(mol, randomSeed=seed) != 0:
        raise ValueError(f"could not embed {smiles!r} in 3D")
    if AllChem.MMFFOptimizeMolecule(mol) == -1:
        AllChem.UFFOptimizeMolecule(mol)
    return Chem.MolToXYZBlock(mol)


_PAGE = """<!doctype html><html><head><meta charset="utf-8">
<script src="{js}"></script>
<style>html,body{{margin:0;background:{bg}}}#v{{width:{w}px;height:{h}px;position:relative}}</style>
</head><body><div id="v"></div><script>
const v = $3Dmol.createViewer('v', {{backgroundColor: '{bg}'}});
v.addModel({xyz}, 'xyz');
v.setStyle({{}}, {{stick: {{radius: 0.14, colorscheme: 'Jmol'}},
                  sphere: {{scale: 0.28, colorscheme: 'Jmol'}}}});
v.zoomTo(); v.render(); window.ready = true;
</script></body></html>"""


def rotating_gif(source: str, out, frames: int = 36, size: tuple[int, int] = (480, 480),
                 fps: int = 18, background: str = "FFFFFF", axis: str = "y",
                 threedmol_js: str | None = None, chromium: str | None = None) -> Path:
    """Render a 360-degree turntable GIF.

    ``source``: path to an ``.xyz`` file, or a SMILES string (needs RDKit). 3Dmol.js comes from
    ``threedmol_js`` (local file, works offline) or the CDN. ``chromium`` may point to a
    Chromium/Chrome binary (also ``CHROMIUM_PATH``); otherwise Playwright's own build is used.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise MissingDependency("Playwright is required: pip install playwright && "
                                "playwright install chromium") from exc
    import json
    xyz = Path(source).read_text() if Path(source).is_file() else smiles_to_xyz(source)
    js = Path(threedmol_js).resolve().as_uri() if threedmol_js else THREEDMOL_URL
    w, h = size
    page_html = _PAGE.format(js=js, bg="#" + background, w=w, h=h, xyz=json.dumps(xyz))
    exe = chromium or os.environ.get("CHROMIUM_PATH")
    imgs = []
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as pw:
        html = Path(tmp) / "view.html"
        html.write_text(page_html)
        browser = pw.chromium.launch(executable_path=exe) if exe else pw.chromium.launch()
        page = browser.new_page(viewport={"width": w, "height": h})
        page.goto(html.as_uri())
        page.wait_for_function("window.ready === true", timeout=30000)
        for _ in range(frames):
            png = page.screenshot(clip={"x": 0, "y": 0, "width": w, "height": h})
            imgs.append(Image.open(io.BytesIO(png)).convert("RGB"))
            page.evaluate(f"v.rotate({360 / frames}, '{axis}'); v.render();")
        browser.close()
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    pal = [im.quantize(colors=64, method=Image.Quantize.MEDIANCUT) for im in imgs]
    pal[0].save(out, save_all=True, append_images=pal[1:], duration=int(1000 / fps), loop=0,
                optimize=True)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="scislides-mol", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p2 = sub.add_parser("2d", help="SMILES -> PNG skeletal formula")
    p2.add_argument("smiles"); p2.add_argument("out")
    p2.add_argument("--transparent", action="store_true")
    p3 = sub.add_parser("gif", help="XYZ file or SMILES -> rotating GIF")
    p3.add_argument("source"); p3.add_argument("out")
    p3.add_argument("--frames", type=int, default=36)
    p3.add_argument("--size", type=int, default=480)
    p3.add_argument("--fps", type=int, default=18)
    p3.add_argument("--js", default=None, help="local 3Dmol-min.js (offline use)")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "2d":
            print(depict_2d(a.smiles, a.out, background=None if a.transparent else "FFFFFF"))
        else:
            print(rotating_gif(a.source, a.out, a.frames, (a.size, a.size), a.fps,
                               threedmol_js=a.js))
    except MissingDependency as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
