"""Find, fetch and inspect source footage with yt-dlp and ffmpeg.

Rules of thumb (see docs/MEDIA.md): prefer authoritative sources, credit them on the
slide, record provenance, never caption footage as something it is not.
Install yt-dlp in a fresh venv: ``pip install -U yt-dlp`` (distribution packages go stale).
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from . import _ffmpeg

SEARCH_FORMAT = "%(id)s | %(duration_string)s | %(view_count)s | %(channel)s | %(title)s"


def _ytdlp() -> list[str]:
    exe = os.environ.get("YT_DLP") or shutil.which("yt-dlp")
    if exe:
        return [exe]
    try:
        import yt_dlp  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("yt-dlp not found: pip install 'scislides[video]'") from exc
    return [sys.executable, "-m", "yt_dlp"]


def _run(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed:\n" + "\n".join(proc.stderr.splitlines()[-8:]))
    return proc.stdout


def search(query: str, n: int = 10) -> list[dict]:
    """``ytsearchN:`` without downloading: id, duration, views, channel, title."""
    out = _run([*_ytdlp(), f"ytsearch{n}:{query}", "--flat-playlist", "--print", SEARCH_FORMAT])
    rows = []
    for line in out.splitlines():
        parts = [p.strip() for p in line.split(" | ", 4)]
        if len(parts) == 5:
            rows.append(dict(zip(("id", "duration", "views", "channel", "title"), parts)))
    return rows


def download(video: str, out_dir, max_height: int = 720) -> Path:
    """Download an id/URL at <= ``max_height`` as MP4 named ``<id>.mp4``; returns the path."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fmt = f"bv*[height<={max_height}]+ba/b[height<={max_height}]/b"
    out = _run([*_ytdlp(), video, "-f", fmt, "--merge-output-format", "mp4", "--no-playlist",
                "-o", str(out_dir / "%(id)s.%(ext)s"), "--print", "after_move:filepath"])
    return Path(out.strip().splitlines()[-1])


def contact_sheet(video, out, cols: int = 6, rows: int = 5, width: int = 320) -> Path:
    """Evenly spaced thumbnails in one image: skim a clip in seconds."""
    dur = _ffmpeg.info(video)["duration"] or 1.0
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    _ffmpeg.run(["-i", str(video), "-vf",
                 f"fps={cols * rows}/{dur:.3f},scale={width}:-2,tile={cols}x{rows}",
                 "-frames:v", "1", str(out)])
    return out


def _stderr_of(args: list[str]) -> str:
    proc = subprocess.run([_ffmpeg.ffmpeg_bin(), "-hide_banner", *args], text=True,
                          capture_output=True)
    return proc.stderr + proc.stdout


def brightness_series(video) -> list[tuple[float, float]]:
    """``(time, mean luma)`` for every frame, from ffmpeg ``signalstats``."""
    with tempfile.TemporaryDirectory() as tmp:
        stats = Path(tmp) / "yavg.txt"
        _ffmpeg.run(["-i", str(video), "-vf",
                     "signalstats,metadata=print:key=lavfi.signalstats.YAVG:file="
                     + _ffmpeg.escape_filter_path(stats), "-an", "-f", "null", "-"])
        out = stats.read_text()
    series, t = [], None
    for line in out.splitlines():
        if "pts_time:" in line:
            t = float(re.search(r"pts_time:([\d.]+)", line)[1])
        elif "YAVG=" in line and t is not None:
            series.append((t, float(line.split("YAVG=")[1])))
    return series


def flash_frame(video) -> tuple[float, float]:
    """Time and brightness of the largest frame-to-frame brightness jump (a flash/detonation).

    Returns ``(seconds, jump)``; cut a few frames before it to show the lead-up.
    """
    s = brightness_series(video)
    if len(s) < 2:
        raise RuntimeError("no brightness data (is this a video file?)")
    jumps = [(b[1] - a[1], b[0]) for a, b in zip(s, s[1:])]
    jump, t = max(jumps)
    return t, jump


def scene_cuts(video, threshold: float = 0.3) -> list[float]:
    """Timestamps of scene changes (``select='gt(scene,T)',showinfo``)."""
    out = _stderr_of(["-i", str(video), "-vf", f"select='gt(scene,{threshold})',showinfo",
                      "-an", "-f", "null", "-"])
    return [float(m) for m in re.findall(r"pts_time:([\d.]+)", out)]


def vtt_to_text(vtt: str) -> str:
    """Plain text from WebVTT auto-captions (timing, tags and rolling duplicates removed)."""
    lines, last = [], ""
    for raw in vtt.splitlines():
        line = re.sub(r"<[^>]+>", "", raw).strip()
        if not line or "-->" in line or line.startswith(("WEBVTT", "Kind:", "Language:")):
            continue
        if line != last:
            lines.append(line)
            last = line
    return "\n".join(lines)


def fetch_subtitles(video: str, out_dir, lang: str = "en") -> str:
    """Download auto-captions and return them as text: check what the narration really claims."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    _run([*_ytdlp(), video, "--skip-download", "--write-auto-subs", "--write-subs",
          "--sub-langs", lang, "--sub-format", "vtt", "-o", str(out_dir / "%(id)s")])
    files = sorted(out_dir.glob("*.vtt"))
    if not files:
        raise RuntimeError("no subtitles available for this video/language")
    return vtt_to_text(files[-1].read_text(encoding="utf-8", errors="replace"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="scislides-video", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("search"); p.add_argument("query"); p.add_argument("-n", type=int, default=10)
    p = sub.add_parser("download"); p.add_argument("video"); p.add_argument("-o", default="media")
    p.add_argument("--max-height", type=int, default=720)
    p = sub.add_parser("sheet"); p.add_argument("video"); p.add_argument("out")
    p.add_argument("--cols", type=int, default=6); p.add_argument("--rows", type=int, default=5)
    p = sub.add_parser("flash"); p.add_argument("video")
    p = sub.add_parser("cuts"); p.add_argument("video"); p.add_argument("--threshold", type=float, default=0.3)
    p = sub.add_parser("subs"); p.add_argument("video"); p.add_argument("-o", default="subs")
    p.add_argument("--lang", default="en")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "search":
            for r in search(a.query, a.n):
                print(" | ".join(r.values()))
        elif a.cmd == "download":
            print(download(a.video, a.o, a.max_height))
        elif a.cmd == "sheet":
            print(contact_sheet(a.video, a.out, a.cols, a.rows))
        elif a.cmd == "flash":
            t, jump = flash_frame(a.video)
            print(f"largest brightness jump at {t:.3f} s (+{jump:.1f} luma)")
        elif a.cmd == "cuts":
            print("\n".join(f"{t:.2f}" for t in scene_cuts(a.video, a.threshold)))
        else:
            print(fetch_subtitles(a.video, a.o, a.lang))
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
