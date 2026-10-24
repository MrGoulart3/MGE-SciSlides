"""Render a deck to look at it: pptx -> PDF (LibreOffice) -> PNG (pdftoppm) -> contact sheet."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image


def _need(binary: str) -> str:
    found = shutil.which(binary)
    if not found:
        raise RuntimeError(f"'{binary}' not found on PATH (set SOFFICE or pass the path)")
    return found


def pptx_to_pdf(pptx, out_dir=None, soffice: str | None = None, timeout: int = 300) -> Path:
    """Convert with ``soffice --headless``. Binary: argument, ``SOFFICE`` env var, or PATH."""
    pptx = Path(pptx).resolve()
    out_dir = Path(out_dir or pptx.parent).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    binary = _need(soffice or os.environ.get("SOFFICE", "soffice"))
    with tempfile.TemporaryDirectory() as profile:  # private profile: no lock clashes
        subprocess.run([binary, f"-env:UserInstallation=file://{profile}", "--headless",
                        "--convert-to", "pdf", "--outdir", str(out_dir), str(pptx)],
                       check=True, capture_output=True, timeout=timeout)
    pdf = out_dir / (pptx.stem + ".pdf")
    if not pdf.exists():
        raise RuntimeError("LibreOffice produced no PDF")
    return pdf


def pdf_to_png(pdf, out_dir, dpi: int = 80, prefix: str = "slide") -> list[Path]:
    """One PNG per page with ``pdftoppm`` (poppler)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run([_need("pdftoppm"), "-r", str(dpi), "-png", str(pdf), str(out_dir / prefix)],
                   check=True, capture_output=True)
    return sorted(out_dir.glob(f"{prefix}-*.png"))


def contact_sheet(images, out, cols: int = 4, thumb_w: int = 480, gap: int = 12,
                  background: str = "#808080") -> Path:
    """Tile images into one PNG for a quick look at the whole deck."""
    imgs = [Image.open(p).convert("RGB") for p in images]
    if not imgs:
        raise ValueError("no images")
    thumbs = []
    for im in imgs:
        im.thumbnail((thumb_w, thumb_w * 10))
        thumbs.append(im)
    tw, th = max(t.width for t in thumbs), max(t.height for t in thumbs)
    rows = -(-len(thumbs) // cols)
    sheet = Image.new("RGB", (cols * (tw + gap) + gap, rows * (th + gap) + gap), background)
    for i, t in enumerate(thumbs):
        r, c = divmod(i, cols)
        sheet.paste(t, (gap + c * (tw + gap), gap + r * (th + gap)))
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return out


def render_deck(pptx, out_dir, dpi: int = 80, cols: int = 4, soffice: str | None = None):
    """Full pipeline; returns ``(pdf, [png...], contact_sheet_png)``."""
    out_dir = Path(out_dir)
    pdf = pptx_to_pdf(pptx, out_dir, soffice)
    pngs = pdf_to_png(pdf, out_dir, dpi)
    return pdf, pngs, contact_sheet(pngs, out_dir / "contact.png", cols)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="scislides-render", description=__doc__)
    ap.add_argument("pptx")
    ap.add_argument("-o", "--out", default="render")
    ap.add_argument("--dpi", type=int, default=80)
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--soffice", default=None)
    a = ap.parse_args(argv)
    pdf, pngs, sheet = render_deck(a.pptx, a.out, a.dpi, a.cols, a.soffice)
    print(pdf, f"{len(pngs)} pages", sheet, sep="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
