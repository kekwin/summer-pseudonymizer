"""Navnehjælp: opdel et fuldt navn i de varianter, der kan stå i fritekst."""
from __future__ import annotations

_PARTICLES = {"von", "van", "de", "den", "der", "af", "la", "le", "du"}
_STRIP = " .,;:()[]\"'"


def _clean(part: str) -> str:
    return part.strip(_STRIP)


def name_variants(full: str) -> set[str]:
    """Alle strenge, vi skal kunne genkende i tekst: hele navnet, hver del og hver del af et bindestregsnavn."""
    full = " ".join((full or "").split())
    out: set[str] = set()
    if not full:
        return out
    out.add(full)
    for part in full.split():
        part = _clean(part)
        if not part or part.lower() in _PARTICLES or not part[0].isalpha():
            continue
        out.add(part)
        if "-" in part:
            for q in part.split("-"):
                q = _clean(q)
                if len(q) >= 2 and q[0].isalpha():
                    out.add(q)
    return {v for v in out if len(v) >= 2}


def first_name(full: str) -> str:
    for part in (full or "").split():
        part = _clean(part)
        if part and part[0].isalpha():
            return part
    return ""
