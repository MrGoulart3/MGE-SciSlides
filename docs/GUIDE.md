# Design guide for scientific slides

[Leia em português](GUIDE.pt-BR.md)

Rules distilled from building and revising a real talk for first-year students. Each rule is
cheap to follow and expensive to ignore. The toolkit enforces the mechanical ones
(`scislides-check`); the rest is judgment.

## Content

1. **One idea per slide.** If you need "and" in the title, you need two slides.
2. **Assertion titles.** "The free energy tells the story the enthalpy alone cannot" beats
   "Energy profile". The title is the take-home; the figure is the evidence.
3. **Audience first.** For freshmen: define every acronym once, prefer a picture of a
   molecule to its name, replace jargon by the thing it does, and start with a question or a
   surprising object, not with an outline.
4. **Numbers carry their source.** Put the origin in a small footer line (`source`) on the
   slide: "Source: author, year" or "own calculation, method X". A number without a source
   is an opinion.
5. **Credit every image and clip** on the slide where it appears, and keep a provenance
   file (see [MEDIA.md](MEDIA.md)).
6. **Speaker notes** hold what you will say, the transition sentence, and the timing.
   Write them as you build the slide, not the night before (`Deck.notes`).

## Typography and layout

7. **Minimum sizes.** Body text 18 pt or more, captions/credits/sources/kickers 14 pt, page
   number 10 pt. `Deck.text` raises small sizes to the theme floor and the checker flags
   anything smaller in an existing deck.
8. **Three lines beat nine.** If text overflows, cut words instead of shrinking the font.
9. **Grid.** 13.333 x 7.5 in, 0.75 in side margins, kicker at y = 0.6, title at y = 1.11,
   content from y = 2.4, footer around y = 6.7. Reusing the grid makes slides feel related.
10. **Color means something.** One accent for structure (kicker, bullets, progress), the
    other two for data series. Never rely on color alone: vary line style and add labels.
11. **Contrast.** Themes ship with checked WCAG ratios; if you build your own, call
    `Theme.check()`.
12. **Alt text** on every picture (`alt=` in `Deck.pic`); it also documents the slide.

## Navigation and rhythm

13. **Progress line ("carrier").** A thin line with N stations and a marker tells the
    audience where they are (`Deck.carrier`). Use it on the content slides of a talk longer
    than ten minutes.
14. **Click reveals.** Reveal layers, names or steps one per click so you control the pace
    (`layouts.layers_figure`, `layouts.names_reveal`). Say the idea first, then click.
15. **Transitions.** Fade between sections, morph only when two slides share objects.
    Nothing flies, spins or bounces.
16. **Section openers.** A full-bleed image with the title on a dark side
    (`layouts.opener`) resets attention after a dense part.

## Process

17. **Render and look before delivering.** `scislides-render deck.pptx` gives PNGs and a
    contact sheet. Overflow, wrong fonts and cut-off figures only show up when you look.
    Fonts missing on the rendering machine are substituted, so also open the deck on the
    presentation computer.
18. **Keep originals untouched.** Never edit the file you were given. Work on copies named
    `v1`, `v2`, ... and write a one-line change log for each. `scislides.edit` helpers
    (reorder, renumber, set text, replace an image in place) make small revisions safe.
19. **Check, then ship.** `scislides-check` for fonts, off-slide shapes, overflow warnings,
    missing alt text and file size; `--forbid` for characters your style guide bans.
20. **Weigh the file.** Compress photos to the size they are shown at, convert video clips to
    short GIFs or keep MP4 for sound, and set a size budget (default 50 MB in the checker).
21. **Rehearse with the real deck** on the real projector at least once; keep a PDF backup.
