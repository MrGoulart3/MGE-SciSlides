"""Locate ffmpeg and run it. Binary: ``FFMPEG`` env var, else ``ffmpeg`` on PATH."""
from __future__ import annotations

import os
import re
import shutil
import subprocess


def ffmpeg_bin() -> str:
    exe = os.environ.get("FFMPEG") or shutil.which("ffmpeg")
    if not exe:
        raise RuntimeError("ffmpeg not found: install it or set the FFMPEG environment variable")
    return exe


def run(args: list[str], capture: bool = False) -> subprocess.CompletedProcess:
    """Run ffmpeg quietly; raises with the tail of stderr on failure."""
    proc = subprocess.run([ffmpeg_bin(), "-hide_banner", "-y", *args], text=True,
                          capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError("ffmpeg failed:\n" + "\n".join(proc.stderr.splitlines()[-12:]))
    return proc


def info(path) -> dict:
    """``{"duration": seconds, "has_audio": bool, "size": (w, h)}`` parsed from ``ffmpeg -i``."""
    proc = subprocess.run([ffmpeg_bin(), "-hide_banner", "-i", str(path)], text=True,
                          capture_output=True)
    err = proc.stderr
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.?\d*)", err)
    dur = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else 0.0
    v = re.search(r"Video:.*?(\d{2,5})x(\d{2,5})", err)
    return {"duration": dur, "has_audio": "Audio:" in err,
            "size": (int(v[1]), int(v[2])) if v else (0, 0)}


def escape_filter_path(path) -> str:
    """Escape a file path for use inside an ffmpeg filter argument."""
    return str(path).replace("\\", "/").replace(":", r"\:").replace("'", r"\'")


def default_font(bold: bool = True) -> str:
    """A TrueType font file for drawtext: DejaVu Sans via matplotlib's bundled copy."""
    from matplotlib import font_manager
    return font_manager.findfont("DejaVu Sans:bold" if bold else "DejaVu Sans")
