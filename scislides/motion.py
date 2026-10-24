"""Minimal, self-written PresentationML for click animations and slide transitions."""
from __future__ import annotations

from lxml import etree

NS_P = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
EFFECTS = ("appear", "fade", "pulse")
TRIGGERS = ("click", "with", "after")


class _Ids:
    def __init__(self) -> None:
        self.n = 2

    def __call__(self) -> int:
        self.n += 1
        return self.n


def _target(spid: int) -> str:
    return f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl>'


def _effect_xml(spid: int, effect: str, trigger: str, duration_ms: int, ids: _Ids) -> str:
    node = {"click": "clickEffect", "with": "withEffect", "after": "afterEffect"}[trigger]
    if effect in ("appear", "fade"):
        preset = 'presetID="1" presetClass="entr"' if effect == "appear" else \
                 'presetID="10" presetClass="entr"'
        body = (f'<p:set><p:cBhvr><p:cTn id="{ids()}" dur="1" fill="hold"><p:stCondLst>'
                f'<p:cond delay="0"/></p:stCondLst></p:cTn>{_target(spid)}<p:attrNameLst>'
                '<p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>'
                '<p:to><p:strVal val="visible"/></p:to></p:set>')
        if effect == "fade":
            body += (f'<p:animEffect transition="in" filter="fade"><p:cBhvr>'
                     f'<p:cTn id="{ids()}" dur="{duration_ms}"/>{_target(spid)}</p:cBhvr>'
                     '</p:animEffect>')
    elif effect == "pulse":
        preset = 'presetID="6" presetClass="emph"'
        body = (f'<p:animScale><p:cBhvr><p:cTn id="{ids()}" dur="{duration_ms}" '
                f'autoRev="1" fill="hold"/>{_target(spid)}</p:cBhvr>'
                '<p:by x="112000" y="112000"/></p:animScale>')
    else:
        raise ValueError(f"effect must be one of {EFFECTS}, got {effect!r}")
    return (f'<p:par><p:cTn id="{ids()}" {preset} presetSubtype="0" fill="hold" grpId="0" '
            f'nodeType="{node}"><p:stCondLst><p:cond delay="0"/></p:stCondLst>'
            f'<p:childTnLst>{body}</p:childTnLst></p:cTn></p:par>')


def timing_xml(rows: list[dict], duration: float = 0.4) -> str:
    """Build ``<p:timing>``. Each row: ``shape_id``, ``effect``, ``trigger``, optional ``duration``.

    ``click`` starts a new click step, ``with`` runs together with the previous effect,
    ``after`` runs once the previous effect has finished.
    """
    ids = _Ids()
    steps: list[list[dict]] = []        # click step -> inner groups {delay, fx}
    end = 0
    for row in rows:
        trig = row.get("trigger", "click")
        if trig not in TRIGGERS:
            raise ValueError(f"trigger must be one of {TRIGGERS}, got {trig!r}")
        ms = round(row.get("duration", duration) * 1000)
        if trig == "click" or not steps:
            trig = "click"
            steps.append([{"delay": 0, "fx": []}])
            end = 0
        elif trig == "after":
            steps[-1].append({"delay": end, "fx": []})
        inner = steps[-1][-1]
        inner["fx"].append((row["shape_id"], row["effect"], trig, ms))
        end = max(end, inner["delay"] + ms) if trig == "with" else inner["delay"] + ms
    out = []
    for click in steps:
        pars = []
        for inner in click:
            xml = "".join(_effect_xml(s, e, t, d, ids) for s, e, t, d in inner["fx"])
            pars.append(f'<p:par><p:cTn id="{ids()}" fill="hold"><p:stCondLst>'
                        f'<p:cond delay="{inner["delay"]}"/></p:stCondLst><p:childTnLst>{xml}'
                        '</p:childTnLst></p:cTn></p:par>')
        out.append(f'<p:par><p:cTn id="{ids()}" fill="hold"><p:stCondLst>'
                   '<p:cond delay="indefinite"/></p:stCondLst><p:childTnLst>'
                   f'{"".join(pars)}</p:childTnLst></p:cTn></p:par>')
    builds = "".join(f'<p:bldP spid="{r["shape_id"]}" grpId="0" animBg="1"/>'
                     for r in rows if r.get("is_sp", True))
    return (f'<p:timing xmlns:p="{NS_P}"><p:tnLst><p:par><p:cTn id="1" dur="indefinite" '
            'restart="never" nodeType="tmRoot"><p:childTnLst><p:seq concurrent="1" '
            'nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>'
            f'{"".join(out)}</p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" '
            'delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst><p:nextCondLst>'
            '<p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond>'
            '</p:nextCondLst></p:seq></p:childTnLst></p:cTn></p:par></p:tnLst>'
            f'<p:bldLst>{builds}</p:bldLst></p:timing>')


def _drop(slide_el, tag: str) -> None:
    for el in slide_el.findall(f"{{{NS_P}}}{tag}"):
        slide_el.remove(el)


def set_timing(slide_el, rows: list[dict], duration: float = 0.4) -> None:
    """Replace the slide's animation timing."""
    _drop(slide_el, "timing")
    if not rows:
        return
    slide_el.append(etree.fromstring(timing_xml(rows, duration)))


def set_transition(slide_el, kind: str = "fade", click: bool = True) -> None:
    """Set a ``fade`` or ``morph`` transition (morph falls back to fade in old viewers)."""
    if kind not in ("fade", "morph"):
        raise ValueError("kind must be 'fade' or 'morph'")
    adv = "" if click else ' advTm="0"'
    if kind == "fade":
        xml = f'<p:transition xmlns:p="{NS_P}" spd="med"{adv}><p:fade/></p:transition>'
    else:
        xml = (f'<mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/'
               f'markup-compatibility/2006" xmlns:p="{NS_P}"><mc:Choice '
               'xmlns:p159="http://schemas.microsoft.com/office/powerpoint/2015/09/main" '
               'Requires="p159"><p:transition spd="slow" xmlns:p14="http://schemas.'
               f'microsoft.com/office/powerpoint/2010/main" p14:dur="900"{adv}>'
               '<p159:morph option="byObject"/></p:transition></mc:Choice><mc:Fallback>'
               f'<p:transition spd="slow"{adv}><p:fade/></p:transition></mc:Fallback>'
               '</mc:AlternateContent>')
    for el in list(slide_el):
        if el.tag == f"{{{NS_P}}}transition" or (
                el.tag.endswith("AlternateContent") and el.find(".//" + f"{{{NS_P}}}transition")
                is not None):
            slide_el.remove(el)
    node = etree.fromstring(xml)
    clr = slide_el.find(f"{{{NS_P}}}clrMapOvr")
    anchor = clr if clr is not None else slide_el.find(f"{{{NS_P}}}cSld")
    anchor.addnext(node)


def animated_ids(slide_el) -> set[int]:
    """Shape ids referenced by the slide's animation timing."""
    return {int(e.get("spid")) for e in slide_el.iter(f"{{{NS_P}}}spTgt")}
