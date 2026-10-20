"""Kør korpusset ved flere tærskler for navnelisten og skriv en markdown-tabel (docs/NAVNELISTE.md).

Kør:  PYTHONPATH=src python scripts/eval_thresholds.py [corpus/da_synthetic.json] [--thresholds 0,1,5,20,100,none]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from pseudonymizer.evaluation import evaluate  # noqa: E402

GROUPS = [
    ("Stikprøve: blandt de 1000 mest frekvente (ikke i den gamle liste)", "liste-topp1000"),
    ("Stikprøve: mindst 100 forekomster i nyhedskorpusset", "liste-m100"),
    ("Stikprøve: 20-99 forekomster", "liste-m20"),
    ("Stikprøve: 5-19 forekomster", "liste-m5"),
    ("Stikprøve: 1-4 forekomster", "liste-m1"),
    ("Stikprøve: registreret, men 0 forekomster", "liste-m0"),
    ("Opdigtede navne, der ikke står på listen", "liste-uregistreret"),
    ("Håndskrevne svære navne (dobbelt, genitiv, initial, versaler, sjældne)", ("navn-dobbelt", "navn-genitiv", "navn-initial", "navn-versaler", "navn-sjælden", "navn-start-sjælden")),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("corpus", nargs="?", default=str(ROOT / "corpus" / "da_synthetic.json"))
    ap.add_argument("--thresholds", default="0,1,5,20,100,none")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    corpus = json.loads(Path(a.corpus).read_text(encoding="utf-8"))
    ts = [None if x == "none" else int(x) for x in a.thresholds.split(",")]
    results = {t: evaluate(corpus, min_count=10**9 if t is None else t) for t in ts}
    head = ["Tærskel (`min_count`)"] + ["kun top 1000" if t is None else str(t) for t in ts]
    print("| " + " | ".join(head) + " |\n|" + "---|" * len(head))
    for label, prefix in GROUPS:
        cells = []
        for t in ts:
            f = i = 0
            for typ, v in results[t]["recall"].items():
                if typ.startswith(prefix + "-" if isinstance(prefix, str) else prefix):
                    f += v["fjernet"]
                    i += v["i_alt"]
            cells.append(f"{f} af {i}")
        print(f"| {label} | " + " | ".join(cells) + " |")
    print("| **Overmaskering i korpusset** (nyttige ord ødelagt) | " + " | ".join(
        f"{results[t]['overmaskering']['tabt']} af {results[t]['overmaskering']['i_alt']}" for t in ts) + " |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
