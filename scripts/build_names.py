"""Byg navnelisterne i src/pseudonymizer/data/ af offentlig statistik. Kun standardbibliotek.

Kilder (se docs/NAVNELISTE.md for licens og kildeangivelse):
  1. Danmarks Statistik, "Navne registreret i Danmark" (januar 2020), udgivet af Digitaliseringsstyrelsen på sprogteknologi.dk
     (CC BY 4.0): alle fornavne med mindst 3 bærere (kvinder, mænd) samt de 1000 mest frekvente fornavne og de 5000 mest frekvente
     efternavne, sorteret efter frekvens.
  2. Leipzig Corpora Collection (CC BY 4.0), ordfrekvenser fra dan_news_2021_1M (nyheder, 1 mio. sætninger, ca. 20 mio. ord) og
     dan_wikipedia_2021_1M (Wikipedia, 1 mio. sætninger). Bruges til to ting: (a) at fjerne navne, der også er almindelige ord
     (hyppighed med småt i begge korpusser, også navnet + "s", fx "mart" -> "marts"), og (b) som "forekomster" pr. navn (hyppighed med
     stort i nyhedskorpusset), der giver et hak mellem "alle registrerede navne" og "de mest almindelige".

Filerne indeholder kun navn og tal. Intet om enkeltpersoner.

Kør:  python scripts/build_names.py [--cache MAPPE] [--max-lower 20]
Første kørsel henter ca. 400 MB (Leipzig-korpusserne); brug --cache for at genbruge hentede filer. Udskriver sha256 af hentede filer.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import re
import sys
import tarfile
import unicodedata
import urllib.request
import zipfile
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "pseudonymizer" / "data"
sys.path.insert(0, str(ROOT / "src"))

DST_URL = "https://sprogtek-ressources.digst.govcloud.dk/danmarks%20statistik/navne_registreret_i_danmark_2020.zip"
LEIPZIG = ("dan_news_2021_1M", "dan_wikipedia_2021_1M")  # det første bruges til "forekomster"; begge til ordfiltret
LEIPZIG_URL = "https://downloads.wortschatz-leipzig.de/corpora/{}.tar.gz"

NAME_RE = re.compile(r"^[a-zæøåéèüöäëïáàóòúûñçð]+(?:-[a-zæøåéèüöäëïáàóòúûñçð]+)*$")
MIN_LETTERS = 3


# Meget almindelige navne, der kun fjernes af ordfiltret, fordi forkortelser/udenlandske ord ligner dem ("mia." = milliard):
RESTORE = frozenset("mia ebbe frede".split())


def fetch(url: str, cache: Path | None) -> bytes:
    name = url.rsplit("/", 1)[-1].replace("%20", "_")
    if cache:
        f = cache / name
        if f.exists():
            return f.read_bytes()
    print(f"henter {url}", file=sys.stderr)
    with urllib.request.urlopen(url, timeout=600) as r:
        data = r.read()
    if cache:
        cache.mkdir(parents=True, exist_ok=True)
        (cache / name).write_bytes(data)
    return data


def norm(name: str) -> str:
    return unicodedata.normalize("NFC", name.strip().casefold())


def read_dst(blob: bytes) -> dict:
    z = zipfile.ZipFile(io.BytesIO(blob))
    out = {}
    for info in z.infolist():
        key = unicodedata.normalize("NFC", info.filename)
        out[key] = z.read(info).decode("utf-8").replace("\r", "").split("\n")
    return out


def ranked(lines: list[str]) -> dict[str, int]:
    res: dict[str, int] = {}
    for i, line in enumerate(l.strip() for l in lines if l.strip()):
        res.setdefault(norm(line), i + 1)
    return res


def read_leipzig(blob: bytes, corpus: str) -> tuple[Counter, Counter]:
    """(lower, capitalised): hyppighed af ordet med småt / ikke helt med småt, nøglet på casefold."""
    lower, cap = Counter(), Counter()
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as t:
        f = t.extractfile(f"{corpus}/{corpus}-words.txt")
        assert f is not None
        for raw in io.TextIOWrapper(f, encoding="utf-8"):
            parts = raw.rstrip("\n").split("\t")
            if len(parts) != 3:
                continue
            w, c = parts[1], int(parts[2])
            key = norm(w)
            if w == w.casefold():
                lower[key] += c
            else:
                cap[key] += c
    return lower, cap


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", type=Path, help="mappe til hentede filer (genbruges)")
    ap.add_argument("--max-lower", type=int, default=20,
                    help="et navn fjernes, hvis det står med småt så mange gange i Leipzig-korpusset (ca. 20 mio. ord)")
    ap.add_argument("--rank-factor", type=int, default=2, help="grænsen ganges med dette for de 1000 mest frekvente navne")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    dst_blob = fetch(DST_URL, a.cache)
    sha = {"dst": hashlib.sha256(dst_blob).hexdigest()}
    dst = read_dst(dst_blob)
    lower, cap = Counter(), Counter()
    for i, corpus in enumerate(LEIPZIG):
        blob = fetch(LEIPZIG_URL.format(corpus), a.cache)
        sha[corpus] = hashlib.sha256(blob).hexdigest()
        lo, ca = read_leipzig(blob, corpus)
        lower.update(lo)
        if i == 0:
            cap = ca
        del blob

    def get(prefix: str) -> list[str]:
        for k, v in dst.items():
            if k.startswith(prefix):
                return v
        raise SystemExit(f"mangler {prefix} i DST-filen")

    first_all = {norm(x) for p in ("Fornavne - kvinder - alle", "Fornavne - mænd - alle") for x in get(p) if x.strip()}
    rank_f, rank_m = ranked(get("Fornavne - kvinder - 1000")), ranked(get("Fornavne - mænd - 1000"))
    rank = {n: min(rank_f.get(n, 10**9), rank_m.get(n, 10**9)) for n in set(rank_f) | set(rank_m)}
    first_all |= set(rank)
    sur_rank = ranked(get("Efternavne - 5000"))

    # Den gamle, håndskrevne liste er stadig med som ekstra sikkerhed (de er alle kendte danske fornavne).
    from pseudonymizer import names_da
    legacy = set(names_da.LEGACY_FIRST_NAMES)
    manual = names_da.AMBIGUOUS

    def keep(n: str, why: Counter) -> bool:
        if not NAME_RE.match(n) or len(n.replace("-", "")) < MIN_LETTERS:
            why["form"] += 1
            return False
        if n in manual:
            why["manuel undtagelse"] += 1
            return False
        # Den håndskrevne liste er gennemgået og undtaget fra ordfiltret. De 1000 mest frekvente navne får en højere grænse
        # (--rank-factor gange), så fx "ebbe" og "frede" ikke tabes, selv om de også er ord; de værste er i undtagelseslisten (AMBIGUOUS).
        limit = a.max_lower * (a.rank_factor if n in rank else 1)
        if n not in legacy and n not in RESTORE and (lower.get(n, 0) >= limit or lower.get(n + "s", 0) >= limit):
            why["almindeligt ord"] += 1
            return False
        return True

    why_f, why_s = Counter(), Counter()
    firsts = {n for n in first_all | legacy if keep(n, why_f)}
    surs = {n: r for n, r in sur_rank.items() if keep(n, why_s)}
    removed_words = sorted((n for n in first_all - legacy - firsts if NAME_RE.match(n) and n not in manual), key=lambda n: rank.get(n, 10**9))

    DATA.mkdir(parents=True, exist_ok=True)
    header = [
        "# Fornavne i Danmark (offentlig statistik; ingen oplysninger om enkeltpersoner).",
        "# Kolonner: navn <TAB> rang (1-1000 blandt de mest frekvente hos Danmarks Statistik, 0 = ikke blandt dem) <TAB> forekomster",
        "# med stort/blandet i Leipzig-nyhedskorpusset (ca. 20 mio. ord).",
        "# Kilder og licens (CC BY 4.0): Danmarks Statistik (navne, januar 2020; udgivet af Digitaliseringsstyrelsen) og",
        "# Leipzig Corpora Collection (dan_news_2021_1M, dan_wikipedia_2021_1M). Se docs/NAVNELISTE.md. Bygget af scripts/build_names.py.",
        f"# Bygget {date.today().isoformat()}; ordfilter: fjernet hvis mindst {a.max_lower} forekomster med småt.",
    ]
    rows = sorted(firsts, key=lambda n: (rank.get(n, 10**9), -cap.get(n, 0), n))
    body = [f"{n}\t{rank.get(n, 0) if rank.get(n, 10**9) < 10**9 else 0}\t{cap.get(n, 0)}" for n in rows]
    (DATA / "fornavne_da.txt").write_text("\n".join(header + body) + "\n", encoding="utf-8", newline="\n")

    sheader = [
        "# Efternavne i Danmark: de 5000 mest frekvente (rang efter frekvens), renset for almindelige ord. Offentlig statistik.",
        "# Kilder og licens (CC BY 4.0): Danmarks Statistik / Digitaliseringsstyrelsen og Leipzig Corpora Collection. Se docs/NAVNELISTE.md.",
        f"# Bygget {date.today().isoformat()}; ordfilter: fjernet hvis mindst {a.max_lower} forekomster med småt.",
    ]
    sbody = [f"{n}\t{r}" for n, r in sorted(surs.items(), key=lambda kv: kv[1])]
    (DATA / "efternavne_da.txt").write_text("\n".join(sheader + sbody) + "\n", encoding="utf-8", newline="\n")

    for k, v in sha.items():
        print(f"sha256 {k}: {v}")
    print(f"fornavne: {len(firsts)} (registrerede {len(first_all)}; frasorteret: {dict(why_f)})")
    print(f"efternavne: {len(surs)} af {len(sur_rank)} (frasorteret: {dict(why_s)})")
    print("mest frekvente fornavne, der blev fjernet som almindelige ord:", ", ".join(removed_words[:80]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
