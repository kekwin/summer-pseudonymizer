"""Evaluering: hvor meget af det, der skulle være væk, er væk, og hvor meget nyttig tekst blev ødelagt?

Korpusformat (JSON):
  {"registry": [{"prefix": "Forælder", "key": "p:1", "names": ["Pernille Lindholm"]}, ...],   # kendte personer
   "protected": ["Mikkel"],  "allowed": ["Rævene"],                                            # bevares / tilladte ord
   "docs": [{"id": "k01", "strict": 1, "text": "...",
             "remove": [{"text": "Pernille", "type": "navn-kendt"}],                           # skal være væk
             "keep": ["torsdag"]}]}                                                            # skal bevares

Typer: `navn-kendt` (står i registret), `navn-ukendt`, `navn-stavefejl`, og identifikatorer: cpr, telefon, email, adresse,
link, konto. Overmaskering = andel af `keep`, der er ødelagt eller tabt, fordi hele teksten blev tilbageholdt af vagten.

Kør:  python -m pseudonymizer.evaluation corpus/da_synthetic.json [--presidio] [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from .engine import Pseudonymizer
from .store import TokenStore

ZERO_TOLERANCE = ("cpr", "telefon", "email", "adresse", "link", "konto")


def _present(needle: str, haystack: str) -> bool:
    if len(needle) <= 3:
        return re.search(rf"(?<!\w){re.escape(needle)}(?!\w)", haystack) is not None
    return needle.casefold() in haystack.casefold()


def build(corpus: dict, layers=()) -> Pseudonymizer:
    store = TokenStore()
    for r in corpus.get("registry", []):
        store.token(r["prefix"], r["key"], r["names"], unique_first_name=bool(r.get("unique_first_name")))
    store.add_protected(corpus.get("protected", []))
    return Pseudonymizer(store, extra_words=corpus.get("extra_words", ()), layers=layers)


def evaluate(corpus: dict, layers=(), default_strict: int = 1) -> dict:
    pseudo = build(corpus, layers)
    allowed = set(corpus.get("allowed", []))
    by_type: dict[str, list[int]] = defaultdict(lambda: [0, 0])  # [fjernet, i alt]
    leaks, lost, withheld = [], [], []
    keep_total = keep_lost = 0
    for d in corpus["docs"]:
        c = pseudo.clean(d["text"], strict=d.get("strict", default_strict), allowed=allowed)
        held = bool(c.leak)  # vagten tilbageholder hele teksten
        out = "" if held else c.text
        if held:
            withheld.append({"id": d["id"], "grund": c.leak})
        for item in d.get("remove", []):
            t = item["type"]
            by_type[t][1] += 1
            if not _present(item["text"], out):
                by_type[t][0] += 1
            else:
                leaks.append({"doc": d["id"], "tekst": item["text"], "type": t, "output": out})
        for k in d.get("keep", []):
            keep_total += 1
            if k not in out:
                keep_lost += 1
                lost.append({"doc": d["id"], "tekst": k, "tilbageholdt": held, "output": out})
    return {
        "recall": {t: {"fjernet": a, "i_alt": b, "andel": (a / b if b else None)} for t, (a, b) in sorted(by_type.items())},
        "overmaskering": {"tabt": keep_lost, "i_alt": keep_total, "andel": (keep_lost / keep_total if keep_total else None)},
        "tilbageholdte_dokumenter": withheld, "lækager": leaks, "ødelagt": lost,
        "docs": len(corpus["docs"]),
    }


def format_report(r: dict, title: str = "") -> str:
    lines = [f"# Evaluering {title}".rstrip(), "", f"{r['docs']} tekster.", "", "| Type | Fjernet | I alt | Recall |", "|---|---|---|---|"]
    for t, v in r["recall"].items():
        lines.append(f"| {t} | {v['fjernet']} | {v['i_alt']} | {v['andel']:.1%} |")
    o = r["overmaskering"]
    lines += ["", f"Overmaskering: {o['tabt']} af {o['i_alt']} ({o['andel']:.1%}) bevaringsord ødelagt eller tabt.",
              f"Tilbageholdt af vagten: {len(r['tilbageholdte_dokumenter'])} tekster."]
    if r["lækager"]:
        lines += ["", "## Lækager"] + [f"- {x['doc']} [{x['type']}]: {x['tekst']!r}" for x in r["lækager"]]
    if r["ødelagt"]:
        lines += ["", "## Ødelagt nyttig tekst"] + [f"- {x['doc']}: {x['tekst']!r}" for x in r["ødelagt"]]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Evaluer pseudonymisering mod et mærket korpus")
    ap.add_argument("corpus")
    ap.add_argument("--presidio", action="store_true", help="tilføj Presidio-laget (kræver [presidio] og en dansk spaCy-model)")
    ap.add_argument("--model", default="da_core_news_md", help="spaCy-model til Presidio")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    corpus = json.loads(Path(a.corpus).read_text(encoding="utf-8"))
    layers = ()
    title = "(kerne)"
    if a.presidio:
        from .presidio_layer import PresidioLayer
        layers = (PresidioLayer(model=a.model),)
        title = f"(kerne + Presidio, {a.model})"
    r = evaluate(corpus, layers)
    print(json.dumps(r, ensure_ascii=False, indent=1) if a.json else format_report(r, title))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
