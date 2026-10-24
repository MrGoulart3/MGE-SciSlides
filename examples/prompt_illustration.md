# Illustration prompt template (optional, tool-agnostic)

An opening slide with a full-bleed illustration works well when the left third stays calm and
dark so the title can sit on it (see `scislides.layouts.opener`). Any image generator, stock
library or commissioned artwork will do; this is the prompt pattern that worked.

## Template

```
Editorial illustration for a science talk about {TOPIC}.
Style: {STYLE, e.g. "flat vector with soft grain", "ink and watercolor", "dark-mode technical poster"}.
Palette: {2-3 colors that match your theme, e.g. deep navy background, amber and teal accents}.
Format: 16:9 landscape, 1920x1080 or larger.
Composition: the subject is on the right two thirds; the LEFT THIRD is an empty, dark, low-detail
area (gradient or plain) reserved for a slide title.
Restrictions: no text, no letters, no logos, no watermarks, no real people or faces, no gore,
no instructions or step-by-step apparatus, nothing resembling a recipe for a hazardous process.
```

## Rules of thumb

1. Generate three or four candidates; choose the one with the cleanest dark left third.
2. If the dark third is not dark enough, `layouts.darken_side` fades it further.
3. Credit it on the slide (`opener(..., ai_generated=True)` adds "AI-generated illustration.").
4. Keep the prompt and the tool/version next to the image in your provenance file
   (template in `docs/MEDIA.md`).
5. Never use generated images as data figures; plot data with real code (`media/plots.py`).
6. Add alt text describing what the image shows, not how it was made.

## Example with a command-line image tool

Tools differ; with any CLI that takes a prompt file, the call is of the form:

```
<image-tool> generate --prompt-file prompt.txt --size 1920x1080 --out illustration.png
```
