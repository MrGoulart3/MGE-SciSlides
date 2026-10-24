# Media: footage, montage, GIFs, provenance, illustrations

Requires `ffmpeg` (PATH or `FFMPEG=/path/to/ffmpeg`) and, for downloads, `yt-dlp`
(`pip install -U yt-dlp` in a fresh venv: distribution packages go stale and break).

## 1. Find footage

```bash
scislides-video search "slow motion reaction demonstration" -n 15
# id | duration | views | channel | title
scislides-video download VIDEO_ID -o media/ --max-height 720
scislides-video sheet media/VIDEO_ID.mp4 sheet.png        # 6x5 contact sheet of the clip
scislides-video flash media/VIDEO_ID.mp4                  # biggest brightness jump (flash)
scislides-video cuts media/VIDEO_ID.mp4 --threshold 0.3   # scene-cut times
scislides-video subs VIDEO_ID --lang en                   # auto-captions as plain text
```

How it works: `ytsearchN:` with `--flat-playlist --print` lists candidates without
downloading; downloads are capped at 720p; the contact sheet is
`fps=cols*rows/duration,scale=320:-2,tile=6x5`; the flash is the largest frame-to-frame jump of
`signalstats` YAVG; cuts come from `select='gt(scene,0.3)',showinfo`.

Read the auto-captions: check what the narration *claims* before you reuse the footage.

### Selection rules

- Prefer authoritative sources (public agencies, laboratories, universities, established
  news organizations). Views are not evidence.
- Never label footage as something it is not: caption what it shows, where and when it was
  filmed, and who published it.
- No how-to content for hazardous materials or processes; use footage that explains, not
  instructs.
- Check the license; when in doubt, ask the owner or use a different clip.
- Credit on the slide ("Footage: publisher, year") and record provenance (below).

## 2. Montage

`examples/montage_example.yaml` documents every key. Build it:

```bash
scislides-montage spec.yaml          # writes <output>.mp4 (with sound) and <output>.gif
```

Per segment: `source`, `start`, `duration`, `crop: [w, h, x, y]` (zoom on the action),
`speed` (0.33 = 3x slower; audio is stretched with chained `atempo`), `caption` (burned into a
dark strip with `drawbox` + `drawtext textfile=`, so any characters work), `label`
(top-right tag). `end_card` adds a closing card of text lines. Sources without sound get
silent audio so the concat stays valid. Allow slow-motion segments enough time to *read* the
caption: about 0.3 s per word.

From Python: `from scislides.media.montage import build_montage`.

### GIF size tips

- 480 px wide, 12 fps, 128 colors is a good start; halve `colors` or `fps` before shrinking
  the picture.
- Two-pass palette (`palettegen` + `paletteuse`) is used automatically; `stats_mode=diff`
  favors moving areas.
- Keep each GIF below ~5 MB; a 20 s montage at 480 px is typically 1 to 3 MB. For sound,
  keep the MP4 and insert it as video instead.
- Shorter loops read better on stage: 5 to 15 s.

## 3. Provenance file

Keep `ORIGIN.md` next to the media and fill one block per item:

```markdown
## clip_a.mp4
- Source URL: https://...
- Publisher / channel: ...
- Date published / filmed: ...
- Retrieved: YYYY-MM-DD, with: scislides-video download (720p)
- License / permission: ...
- Used for: slide 12, 4.8 s starting at 9.0 s, 3x slower at 12.0 s
- What it shows (checked against captions): ...
- Credit line on slide: "Footage: ..."
- Edits: crop 640x480+100+90, caption added, speed 0.33 for 1.4 s
```

## 4. Ethics and credits

Credit creators, do not alter footage to change its meaning (crop and slow motion for clarity
are fine when disclosed in the caption), respect people's privacy, and avoid sensational
material when a diagram teaches better. Generated images are labelled as such.

## 5. AI-generated illustration (optional)

Use any generator you like. `examples/prompt_illustration.md` holds a prompt template:
style, 16:9, an empty dark left third for the title, and restrictions (no text, logos, gore or
instructions). Add the illustration with `layouts.opener(..., ai_generated=True)` for the
"AI-generated illustration." credit, store prompt and tool in the provenance file, and never
use generated images in place of data figures.
