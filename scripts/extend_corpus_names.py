"""Udvid corpus/da_synthetic.json med tekster, der måler navnelisten (docs/NAVNELISTE.md). Kan køres igen: eksisterende `nl*`-tekster
erstattes.

1. Lagdelte stikprøver af fornavne fra data/fornavne_da.txt (fast frø, ikke håndplukket), efter hvor ofte navnet findes i nyhedskorpusset:
   topp1000 (blandt DK's 1000 mest frekvente, ikke i den gamle håndskrevne liste), m100 (mindst 100 forekomster), m20 (20-99), m5 (5-19),
   m1 (1-4), m0 (registreret, men aldrig set i korpusset), og `uregistreret` (opdigtede navne, der ikke står på listen). Hvert navn står
   (a) med småt midt i en sætning og (b) med stort først i en sætning.
2. Svære tilfælde: dobbeltnavne, genitiv og apostrof, initial, navne i versaler, navne der ligner almindelige ord, og almindelig tekst
   (børnehaveord), der ikke må ødelægges.

Navnene er opdigtede eksempler i forhold til hinanden: de er trukket tilfældigt fra offentlig statistik og peger ikke på nogen bestemt person.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from pseudonymizer import names_da  # noqa: E402

CORPUS = ROOT / "corpus" / "da_synthetic.json"
PER_STRATUM = 8
SEED = 20261020

LOWER = ["ring til {n}, hun ved besked", "{n} henter i dag kl. 15", "vi mødtes med {n} i parken", "kan {n} komme med på fredag?",
         "mormor og {n} bager kager", "hils {n} og sig tak for sidst", "{n} skal på tur i morgen", "tak til {n} for hjælpen"]
START = ["{N} har det fint i dag.", "{N} skal med på tur.", "{N} blev hentet tidligt.", "{N} og hendes far kommer til festen.",
         "{N} har fået en ny jakke.", "{N} sover nu.", "{N} har haft en god dag.", "{N} ringede lige."]
UNREGISTERED = ["valtyra", "zelmira", "orvokka", "brynhilde", "thorgunna", "ingvarda", "sunnivaa", "halfrida"]
KEEP_COMMON = [
    ("Vi skal tage på tur, og børnene har en sten i skoen.", ["tage på tur", "en sten i skoen"]),
    ("Det blev en lykke at få en kaj ved havnen.", ["en kaj ved havnen"]),
    ("Der kommer storm i morgen, så vi holder os inde.", ["Der kommer storm i morgen"]),
    ("Den vilde saga om silke og anker var spændende.", ["Den vilde saga"]),
    ("Pigerne har en bil, et tog og en bold med i dag.", ["en bil, et tog og en bold"]),
    ("Vi skal sætte pris på maj, juni og juli, og hans mor kommer.", ["maj, juni og juli", "hans mor kommer"]),
    ("Husk rosa tøj, gule støvler og en blå hue til tirsdag.", ["gule støvler", "en blå hue"]),
    ("Bær tøjet i en pose, og find en frugt og en mælk til frokost.", ["en frugt og en mælk til frokost"]),
    ("Det koster 5 mia. kr., og mia. betyder milliard.", ["5 mia. kr."]),
    ("Efter sommerferien er der fødselsdag, fest og kage i stuen.", ["fødselsdag, fest og kage i stuen"]),
]


def strata() -> dict[str, list[str]]:
    legacy = names_da.LEGACY_FIRST_NAMES
    rows = [(n, int(r), int(c)) for n, r, c in names_da._rows("fornavne_da.txt") if "-" not in n and len(n) >= 4]
    cuts = {
        "topp1000": lambda r, c, n: r >= 300 and n not in legacy,
        "m100": lambda r, c, n: r == 0 and c >= 100,
        "m20": lambda r, c, n: r == 0 and 20 <= c < 100,
        "m5": lambda r, c, n: r == 0 and 5 <= c < 20,
        "m1": lambda r, c, n: r == 0 and 1 <= c < 5,
        "m0": lambda r, c, n: r == 0 and c == 0,
    }
    rng = random.Random(SEED)
    out = {}
    for key, ok in cuts.items():
        pool = sorted(n for n, r, c in rows if ok(r, c, n))
        out[key] = rng.sample(pool, PER_STRATUM)
    known = {n for n, _r, _c in rows}
    out["uregistreret"] = [n for n in UNREGISTERED if n not in known]
    return out


def main() -> int:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    docs = [d for d in corpus["docs"] if not d["id"].startswith("nl")]
    new = []
    for key, names in strata().items():
        for i, n in enumerate(names):
            new.append({"id": f"nl-{key}-s{i}", "text": LOWER[i % len(LOWER)].format(n=n),
                        "remove": [{"text": n, "type": f"liste-{key}-småt"}], "keep": []})
            new.append({"id": f"nl-{key}-t{i}", "text": START[i % len(START)].format(N=n.capitalize()),
                        "remove": [{"text": n.capitalize(), "type": f"liste-{key}-start"}], "keep": []})
    hard = [
        ("nl-h01", "ring til anne-mette og lise-lotte i morgen", [("anne-mette", "navn-dobbelt-småt"), ("lise-lotte", "navn-dobbelt-småt")], []),
        ("nl-h02", "Anne-Mette og Per-Olof kommer også.", [("Anne-Mette", "navn-dobbelt-stort"), ("Per-Olof", "navn-dobbelt-stort")], []),
        ("nl-h03", "Thorvalds mor og oline's far henter dem.", [("Thorvalds", "navn-genitiv"), ("oline's", "navn-genitiv")], ["mor og"]),
        ("nl-h04", "Det er Oline K. og torvald b. der skal med.", [("Oline K.", "navn-initial"), ("torvald b.", "navn-initial")], ["der skal med"]),
        ("nl-h05", "RING TIL OLINE OG GUDRUN I DAG", [("OLINE", "navn-versaler"), ("GUDRUN", "navn-versaler")], []),
        ("nl-h06", "Ebbe og Hjalte har bygget en kæmpe borg.", [("Ebbe", "navn-start-sjælden"), ("Hjalte", "navn-start-sjælden")], ["har bygget en kæmpe borg"]),
        ("nl-h07", "Gudrun, Ingvild og Solveig er med på turen.", [("Gudrun", "navn-start-sjælden"), ("Ingvild", "navn-start-sjælden"), ("Solveig", "navn-start-sjælden")], ["er med på turen"]),
        ("nl-h08", "tak til mie, nanna og ellen for kagerne", [("mie", "navn-sjælden-småt"), ("nanna", "navn-sjælden-småt"), ("ellen", "navn-sjælden-småt")], ["for kagerne"]),
    ]
    for id_, text, rem, keep in hard:
        new.append({"id": id_, "text": text, "remove": [{"text": t, "type": ty} for t, ty in rem], "keep": keep})
    for i, (text, keep) in enumerate(KEEP_COMMON):
        new.append({"id": f"nl-k{i + 1:02d}", "text": text, "remove": [], "keep": keep})
    corpus["docs"] = docs + new
    CORPUS.write_text(json.dumps(corpus, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(new)} nye tekster; i alt {len(corpus['docs'])}")
    for k, v in strata().items():
        print(k, ", ".join(v))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
