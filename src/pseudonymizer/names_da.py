"""Danske fornavne (og valgfrit efternavne) som et billigt net for ukendte navne, også når de er skrevet med småt eller står først i en
sætning.

Hovedlisten ligger i `data/fornavne_da.txt` (bygget af `scripts/build_names.py` af offentlig statistik, se docs/NAVNELISTE.md). Den
gamle, håndskrevne liste (ca. 400 navne) er bevaret som `LEGACY_FIRST_NAMES` og er altid med. Navne, der også er almindelige danske ord,
er fjernet (automatisk ordfilter ved bygningen + `AMBIGUOUS`).

Tærsklen `min_count` styrer, hvor sjældne navne der er med: et navn er med, hvis det er blandt de 1000 mest frekvente hos Danmarks
Statistik, eller har mindst `min_count` forekomster med stort i et dansk nyhedskorpus (ca. 20 mio. ord). `0` = alle registrerede navne
(mindst 3 bærere).
"""
from __future__ import annotations

from functools import lru_cache
from importlib import resources

from .lexicon import ALWAYS_OK, STARTERS, WEEKDAYS_MONTHS

FEMALE = """
emma ida freja ella alma sofia sophia clara klara karla olivia agnes lærke mathilde josefine josephine laura marie anna sara sarah
nanna cecilie caroline johanne frida rosa vera naja emilie amalie ellen signe astrid alberte filippa liva selma luna nora anne
mette lene susanne camilla charlotte louise maria pernille katrine line helle tina hanne dorte lone karen birgit gitte pia trine
rikke malene mie stine julie kirsten inge lisbeth jette annette anita bente marianne ingeborg mille sofie tine christina kathrine
kristine maja gry ditte nete randi lis birte hanna henriette ulla vibeke lotte lisa linda mona sanne bodil ingrid grete grethe
helene else eva eve winnie yvonne jytte berit berit connie conny tanja tania sabrina natasja natascha nicoline nicole rebekka
stephanie sidsel sine sofia thea theresa trine tove ulrikke vivi vita zara maiken marlene malou louisa liv lea lina lisbet
lise lærke mai mathea merete mikkeline mira nikoline oda pernille ragnhild rigmor ronja rosa sabina simone sonja stella
tilde viola viktoria victoria wilma yasmin ylva
""".split()

MALE = """
william noah oscar oliver lucas lukas carl viktor victor alfred malthe emil valdemar frederik magnus elias mikkel mads rasmus
jesper anders peter henrik thomas michael martin lars søren jens morten kasper jakob jacob christian daniel simon tobias
nikolaj jonas mathias andreas casper kristian niels ole jørgen johan johannes jonathan jeppe jacob benjamin sebastian
alexander aksel axel anton aske aslak asger bastian bjarke bertil brian carsten claus dennis dan flemming frank frands
gustav gunnar hans-jørgen henning holger ib ivan jan jesper joachim john jørn karl kenneth kevin kim klaus knud kurt
lasse leif lennart lorenz marcus marius mark mathis max morten nick nicklas nicolai nikolai olav otto palle patrick
paul poul preben rene rené rolf rune rasmus sam samuel sigurd steen stefan steffen svend tim thor thorvald tommy
troels uffe ulrik valdemar vagn verner vilhelm villads vincent walter wilhelm åge aage
alfred august bo
""".split()

# Manuel undtagelsesliste: navne, der også er almindelige danske ord (eller forkortelser), og som derfor ikke må bruges som net (ellers
# ødelægges almindelig tekst). Gælder oven i det automatiske ordfilter (scripts/build_names.py).
# De findes stadig som kendte navne, hvis klienten kender personen.
AMBIGUOUS = frozenset("""bo per hans rune august bent dan mark rose sol tom maj ask bjørn liv rene max sky ven mor far barn dag god lys sne
ånd rosa drue karry adm ngo sars eid dat will aske chili ravn nikkel hindi gamma alpha java jeans alm find trille sultan silke birk flora ane""".split())

LEGACY_FIRST_NAMES = frozenset(n for n in set(FEMALE) | set(MALE) if len(n) >= 3 and n not in AMBIGUOUS and "-" not in n)
COMMON_FIRST_NAMES = LEGACY_FIRST_NAMES  # bagudkompatibelt navn

DEFAULT_MIN_COUNT = 0
_NOT_NAMES = STARTERS | ALWAYS_OK | WEEKDAYS_MONTHS | AMBIGUOUS


def _rows(filename: str):
    text = resources.files(__package__).joinpath("data", filename).read_text(encoding="utf-8")
    for line in text.splitlines():
        if line and not line.startswith("#"):
            yield line.split("	")


@lru_cache(maxsize=8)
def first_names(min_count: int = DEFAULT_MIN_COUNT) -> frozenset:
    """Fornavne (små bogstaver) til opslag. Se modulets beskrivelse af `min_count`."""
    out = set(LEGACY_FIRST_NAMES)
    for name, rank, mentions in _rows("fornavne_da.txt"):
        if int(rank) > 0 or int(mentions) >= min_count:
            out.add(name)
    return frozenset(out - _NOT_NAMES)


@lru_cache(maxsize=1)
def core_names() -> frozenset:
    """Den håndskrevne liste og de 1000 mest frekvente navne hos Danmarks Statistik."""
    return first_names(10**9)


@lru_cache(maxsize=8)
def surnames(max_rank: int = 0) -> frozenset:
    """De `max_rank` mest frekvente efternavne (højst 5000; 0 = ingen)."""
    if max_rank <= 0:
        return frozenset()
    return frozenset(n for n, r in _rows("efternavne_da.txt") if int(r) <= max_rank) - _NOT_NAMES
