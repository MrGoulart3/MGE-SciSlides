"""Helpers for editing an existing deck in place (never touch the original: save a new version)."""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation

from . import motion

NS_P = motion.NS_P


def open_deck(path):
    return Presentation(str(path))


def find_shape(slide, name: str):
    """First shape (searching inside groups) whose name equals ``name``, else ``None``."""
    def walk(shapes):
        for sh in shapes:
            if sh.name == name:
                return sh
            if sh.shape_type == 6:  # group
                hit = walk(sh.shapes)
                if hit is not None:
                    return hit
        return None
    return walk(slide.shapes)


def set_text(shape, text: str) -> None:
    """Replace the text, keeping the formatting of the first run of each paragraph."""
    tf = shape.text_frame
    lines = text.split("\n")
    paras = tf.paragraphs
    for i, line in enumerate(lines):
        if i < len(paras):
            p = paras[i]
        else:
            import copy
            p = tf.add_paragraph()
            p._p.getparent().replace(p._p, copy.deepcopy(paras[-1]._p))
            p = tf.paragraphs[-1]
        runs = p.runs
        if runs:
            runs[0].text = line
            for r in runs[1:]:
                r._r.getparent().remove(r._r)
        else:
            p.text = line
    for p in tf.paragraphs[len(lines):]:
        p._p.getparent().remove(p._p)


def remove_shape(shape) -> None:
    shape._element.getparent().remove(shape._element)


def reorder(prs, order: list[int]) -> None:
    """Reorder slides. ``order`` lists the current 0-based indexes in their new order.

    Slides not listed are dropped from the show (their parts stay in the file until saved
    through ``delete_slide``); to keep every slide, list all indexes.
    """
    lst = prs.slides._sldIdLst
    items = list(lst)
    if any(i < 0 or i >= len(items) for i in order):
        raise IndexError("order contains an index outside the deck")
    for el in items:
        lst.remove(el)
    for i in order:
        lst.append(items[i])


def delete_slide(prs, index: int) -> None:
    """Remove a slide and its relationship."""
    lst = prs.slides._sldIdLst
    sld = list(lst)[index]
    prs.part.drop_rel(sld.rId)
    lst.remove(sld)


def renumber(prs, name: str = "number", start: int = 1) -> int:
    """Rewrite page numbers in shapes called ``name``; returns how many were changed."""
    n = 0
    for i, slide in enumerate(prs.slides, start):
        sh = find_shape(slide, name)
        if sh is not None:
            set_text(sh, str(i))
            n += 1
    return n


def replace_blob(picture, new_file) -> None:
    """Swap the image/GIF bytes behind a picture shape without touching its size or position.

    The new file should have the same format (extension) as the old one.
    """
    rid = picture._element.blip_rEmbed if hasattr(picture._element, "blip_rEmbed") else \
        picture._element.xpath(".//a:blip/@r:embed")[0]
    part = picture.part.related_part(rid)
    part._blob = Path(new_file).read_bytes()


def drop_orphan_animations(slide) -> int:
    """Delete animation entries whose target shape no longer exists; returns how many were removed.

    If nothing valid is left, the whole timing block is removed.
    """
    el = slide._element
    alive = {sh.shape_id for sh in _all_shapes(slide.shapes)}
    dead = motion.animated_ids(el) - alive
    if not dead:
        return 0
    timing = el.find(f"{{{NS_P}}}timing")
    q = lambda t: f"{{{NS_P}}}{t}"  # noqa: E731
    for tgt in [t for t in timing.iter(q("spTgt")) if int(t.get("spid")) in dead]:
        node = tgt
        while node is not None and not (node.tag == q("cTn") and
                                        node.get("nodeType", "").endswith("Effect")):
            node = node.getparent()
        if node is not None and node.getparent() is not None:
            par = node.getparent()          # the <p:par> wrapping the effect
            if par.getparent() is not None:
                par.getparent().remove(par)
    for b in [b for b in timing.iter(q("bldP")) if int(b.get("spid")) in dead]:
        b.getparent().remove(b)
    changed = True
    while changed:                          # prune click/step groups left empty
        changed = False
        for lst in list(timing.iter(q("childTnLst"))):
            parent = lst.getparent()
            if len(lst) == 0 and parent.get("nodeType") is None and parent.getparent() is not None \
                    and parent.getparent().tag == q("par"):
                par = parent.getparent()
                par.getparent().remove(par)
                changed = True
    if not motion.animated_ids(el):
        el.remove(timing)
    return len(dead)


def _all_shapes(shapes):
    for sh in shapes:
        yield sh
        if sh.shape_type == 6:
            yield from _all_shapes(sh.shapes)
