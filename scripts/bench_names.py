"""Mål navnelisten: indlæsningstid, hukommelse, tid pr. tekst og overmaskering på dansk tekst, vi ikke selv har skrevet.

Overmaskering måles som andelen af ord med SMÅT begyndelsesbogstav, som navnelisten maskerer i en offentlig dansk tekstprøve
(fx Leipzig Corpora Collection, sætningsfilen "*-sentences.txt", CC BY 4.0). Ord med småt er sjældent navne i skrevet dansk, så hvert
fund er næsten altid et almindeligt ord, der ikke burde være væk. (Ord med stort tælles ikke: de er oftest rigtige navne.)

Kør:  PYTHONPATH=src python scripts/bench_names.py SÆTNINGSFIL [SÆTNINGSFIL ...] [--thresholds 0,1,5,20,100]
"""
from __future__ import annotations

import argparse
import re
import statistics
import sys
import time
import tracemalloc
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from pseudonymizer import Pseudonymizer, TokenStore, names_da  # noqa: E402


def sentences(paths) -> list[str]:
    out = []
    for p in paths:
        for line in Path(p).read_text(encoding="utf-8").splitlines():
            parts = line.split("\t", 1)
            if len(parts) == 2:
                out.append(parts[1])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--thresholds", default="0,1,5,20,100")
    ap.add_argument("--surname-rank", type=int, default=0)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    sents = sentences(a.files)
    texts = [" ".join(sents[i:i + 12]) for i in range(0, len(sents) - 12, 12)][:400]  # ca. 1500-2500 tegn pr. tekst
    lower_tokens = sum(1 for s in sents for w in re.findall(r"[\wæøåÆØÅ]+", s) if w[:1].islower())
    print(f"{len(sents)} sætninger, {lower_tokens} ord med småt; {len(texts)} tekster à ca. {sum(map(len, texts)) // len(texts)} tegn\n")
    print("| min_count | navne i listen | indlæsning | hukommelse (sæt) | ms pr. tekst (gns / p95) | små ord maskeret | pr. 10.000 |")
    print("|---|---|---|---|---|---|---|")
    offenders: dict[int, Counter] = {}
    for t in (int(x) for x in a.thresholds.split(",")):
        names_da.first_names.cache_clear()
        names_da.surnames.cache_clear()
        names_da.core_names.cache_clear()
        tracemalloc.start()
        t0 = time.perf_counter()
        n = len(names_da.first_names(t) | names_da.surnames(a.surname_rank))
        load = time.perf_counter() - t0
        mem = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()
        p = Pseudonymizer(TokenStore(), min_count=t, surname_rank=a.surname_rank)
        p.clean("opvarmning")
        times = []
        for tx in texts[:200]:
            t1 = time.perf_counter()
            p.clean(tx, strict=0)
            times.append((time.perf_counter() - t1) * 1000)
        # overmaskering
        p.trace = []
        for s in sents:
            p._common_names(s)
        hits = Counter(orig.casefold() for _tok, orig, layer in p.trace if layer == "navneliste" and orig[:1].islower())
        offenders[t] = hits
        total = sum(hits.values())
        times.sort()
        print(f"| {t} | {n} | {load * 1000:.0f} ms | {mem / 1e6:.1f} MB | {statistics.mean(times):.2f} / {times[int(len(times) * .95)]:.2f} | "
              f"{total} | {total / lower_tokens * 10000:.1f} |")
    for t, c in offenders.items():
        print(f"\nmin_count={t}: hyppigste små ord, der blev maskeret: " + ", ".join(f"{w} ({k})" for w, k in c.most_common(25)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
