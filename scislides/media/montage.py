"""Build a captioned video montage (MP4 with sound + palette GIF) from a YAML/JSON spec.

Spec keys (all optional unless noted)::

    output: out/montage          # base name -> .mp4 and .gif
    size: [560, 420]             # width, height of every segment
    fps: 15
    crf: 20
    font: /path/to/font.ttf      # default: DejaVu Sans Bold (bundled with matplotlib)
    caption: {size: 21, color: white, box_opacity: 0.62, box_height: 86}
    segments:                    # required
      - source: clip.mp4         # relative paths resolve against the spec file
        start: 9.0               # seconds into the source
        duration: 4.8            # seconds of SOURCE material
        crop: [640, 480, 100, 90]   # w, h, x, y before scaling (e.g. zoom on the action)
        speed: 1.0               # 0.33 = three times slower (audio follows with atempo)
        caption: "Text burned into a dark strip at the bottom"
        label: "3x slower"       # small highlighted tag, top right
    end_card:                    # optional closing card
      duration: 4
      background: "000000"
      lines: [{text: "Source: ...", size: 24, color: white}]
    gif: {width: 480, fps: 12, colors: 128}   # or false to skip
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import textwrap
from pathlib import Path

from . import _ffmpeg

AUDIO = "aresample=44100,aformat=channel_layouts=stereo"


def atempo_chain(factor: float) -> str:
    """ffmpeg ``atempo`` only accepts 0.5-2.0 per stage; chain stages for other factors."""
    if factor <= 0:
        raise ValueError("speed must be positive")
    stages = []
    while factor < 0.5:
        stages.append(0.5)
        factor /= 0.5
    while factor > 2.0:
        stages.append(2.0)
        factor /= 2.0
    stages.append(factor)
    return ",".join(f"atempo={s:.6f}" for s in stages)


def load_spec(path) -> dict:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError("pyyaml is required for YAML specs (or use JSON)") from exc
        spec = yaml.safe_load(text)
    else:
        spec = json.loads(text)
    spec["_base"] = str(path.resolve().parent)
    return spec


def _drawtext(font: str, textfile: Path, size: int, color: str, x: str, y: str,
              spacing: int = 6) -> str:
    return (f"drawtext=fontfile={_ffmpeg.escape_filter_path(font)}:"
            f"textfile={_ffmpeg.escape_filter_path(textfile)}:fontcolor={color}:fontsize={size}:"
            f"line_spacing={spacing}:x={x}:y={y}")


def _segment(seg: dict, idx: int, spec: dict, tmp: Path, base: Path) -> Path:
    w, h = spec.get("size", [560, 420])
    fps = spec.get("fps", 15)
    font = spec.get("font") or _ffmpeg.default_font()
    cap = {"size": 21, "color": "white", "box_opacity": 0.62, "box_height": 86,
           **spec.get("caption", {})}
    src = Path(seg["source"])
    src = src if src.is_absolute() else base / src
    speed = float(seg.get("speed", 1.0))
    dur = float(seg["duration"])
    vf = []
    if seg.get("crop"):
        cw, ch, cx, cy = seg["crop"]
        vf.append(f"crop={cw}:{ch}:{cx}:{cy}")
    vf += [f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}",
           f"setpts=PTS/{speed}", f"fps={fps}"]
    if seg.get("caption"):
        text = seg["caption"]
        if "\n" not in text:
            text = textwrap.fill(text, max(int(w / (cap["size"] * 0.6)), 10))
        tf = tmp / f"cap{idx}.txt"
        tf.write_text(text, encoding="utf-8")
        bh = cap["box_height"]
        vf.append(f"drawbox=y=ih-{bh}:w=iw:h={bh}:color=black@{cap['box_opacity']}:t=fill")
        vf.append(_drawtext(font, tf, cap["size"], cap["color"], "(w-text_w)/2",
                            f"h-{bh}+({bh}-text_h)/2"))
    if seg.get("label"):
        lf = tmp / f"lab{idx}.txt"
        lf.write_text(seg["label"], encoding="utf-8")
        vf.append(_drawtext(font, lf, 20, "yellow", "w-text_w-14", "14"))
    out = tmp / f"seg{idx}.mp4"
    has_audio = _ffmpeg.info(src)["has_audio"]
    args = ["-ss", str(seg.get("start", 0)), "-t", str(dur), "-i", str(src)]
    if has_audio:
        af = ([atempo_chain(speed)] if speed != 1.0 else []) + [AUDIO]
        args += ["-vf", ",".join(vf), "-af", ",".join(af)]
    else:
        args += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-vf", ",".join(vf),
                 "-map", "0:v", "-map", "1:a"]
    args += ["-t", f"{dur / speed:.3f}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
             "-c:a", "aac", str(out)]
    _ffmpeg.run(args)
    return out


def _end_card(card: dict, spec: dict, tmp: Path) -> Path:
    w, h = spec.get("size", [560, 420])
    fps = spec.get("fps", 15)
    font = spec.get("font") or _ffmpeg.default_font()
    dur = float(card.get("duration", 4))
    lines = card.get("lines", [])
    step = [int(l.get("size", 24) * 1.7) for l in lines]
    top = -sum(step) // 2
    vf, y = [], top
    for i, line in enumerate(lines):
        tf = tmp / f"end{i}.txt"
        tf.write_text(line["text"], encoding="utf-8")
        vf.append(_drawtext(font, tf, line.get("size", 24), line.get("color", "white"),
                            "(w-text_w)/2", f"(h-text_h)/2+{y + step[i] // 2}"))
        y += step[i]
    out = tmp / "end.mp4"
    _ffmpeg.run(["-f", "lavfi", "-i", f"color=c=0x{card.get('background', '000000')}:s={w}x{h}"
                 f":r={fps}:d={dur}", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                 "-t", str(dur), "-vf", ",".join(vf) or "null", "-c:v", "libx264",
                 "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(out)])
    return out


def build_montage(spec: "dict | str | Path", base_dir=None) -> tuple[Path, Path | None]:
    """Render the montage; returns ``(mp4_path, gif_path_or_None)``."""
    if not isinstance(spec, dict):
        spec = load_spec(spec)
    base = Path(base_dir or spec.get("_base", "."))
    out_base = Path(spec.get("output", "montage"))
    out_base = out_base if out_base.is_absolute() else base / out_base
    out_base.parent.mkdir(parents=True, exist_ok=True)
    mp4 = out_base.with_suffix(".mp4")
    with tempfile.TemporaryDirectory(prefix="scislides_montage_") as t:
        tmp = Path(t)
        parts = [_segment(s, i, spec, tmp, base) for i, s in enumerate(spec["segments"], 1)]
        if spec.get("end_card"):
            parts.append(_end_card(spec["end_card"], spec, tmp))
        lst = tmp / "list.txt"
        lst.write_text("".join(f"file '{p}'\n" for p in parts))
        _ffmpeg.run(["-f", "concat", "-safe", "0", "-i", str(lst), "-c:v", "libx264",
                     "-crf", str(spec.get("crf", 20)), "-pix_fmt", "yuv420p", "-c:a", "aac",
                     "-b:a", "128k", str(mp4)])
    gif = None
    g = spec.get("gif", {})
    if g is not False:
        g = {"width": 480, "fps": 12, "colors": 128, **(g or {})}
        gif = out_base.with_suffix(".gif")
        _ffmpeg.run(["-i", str(mp4), "-vf",
                     f"fps={g['fps']},scale={g['width']}:-2:flags=lanczos,split[a][b];"
                     f"[a]palettegen=max_colors={g['colors']}:stats_mode=diff[p];"
                     "[b][p]paletteuse=dither=bayer:bayer_scale=4", "-loop", "0", str(gif)])
    return mp4, gif


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="scislides-montage", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", help="YAML or JSON spec")
    ap.add_argument("--no-gif", action="store_true")
    a = ap.parse_args(argv)
    spec = load_spec(a.spec)
    if a.no_gif:
        spec["gif"] = False
    try:
        mp4, gif = build_montage(spec)
    except (RuntimeError, KeyError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(mp4)
    if gif:
        print(gif)
    return 0


if __name__ == "__main__":
    sys.exit(main())
