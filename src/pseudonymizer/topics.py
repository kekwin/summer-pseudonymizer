"""Følsomme emner. Rammer en tekst et emne, tilbageholdes den (med emnets navn), medmindre emnet er tilladt.

Ordlisterne er med vilje brede: overblokering er den acceptable fejl. Matcher på ordstamme (begyndelsen af ord),
så bøjninger og sammensætninger ("skoldkopper", "feberfri", "lægebesøg") fanges.
"""
from __future__ import annotations

import re

_STEMS = {
    "sygdom": [
        "syg", "feber", "læge", "hospital", "skadestue", "smitt", "lus", "hovedlus", "madorm", "orm", "skoldkopp",
        "hånd-fod", "hånd fod", "mundsyge", "mave-tarm", "maveonde", "opkast", "kaster op", "kastede op", "diar",
        "influenza", "covid", "corona", "forkølet", "forkøl", "hoste", "øreinfektion", "øjenbetænd", "udslæt",
        "bule", "skade", "brækk", "blød", "sting", "hjernerystelse", "faldt", "styrt", "vaccin", "tandlæge",
        "operation", "indlagt", "kræft", "ondt i",
    ],
    "helbred-medicin": [
        "medicin", "panodil", "ipren", "allergi", "allergisk", "nødde", "astma", "diabetes", "epilepsi",
        "diagnose", "handicap", "autis", "adhd", "ordblind", "høreapparat", "briller", "insulin", "epipen",
    ],
    "adfærd-trivsel": [
        "adfærd", "mobning", "mobbe", "drille", "slåsk", "slog", "bidt", "bider", "konflikt", "udadreager",
        "bekymr", "underretning", "støtte", "ppr", "pædagogisk-psykologisk", "speciallærer", "sprogvurdering",
        "trivsel", "ensom",
    ],
    "familie": [
        "skilsmisse", "skilt", "forældremyndighed", "samvær", "bopæl", "dødsfald", "død", "begravelse", "sorg",
        "gravid", "graviditet",
    ],
    "økonomi": ["restance", "friplads", "økonomisk", "gæld", "rykker"],
}

_PATTERNS = {
    cat: re.compile(r"(?<!\w)(?:" + "|".join(re.escape(s) for s in stems) + r")", re.I)
    for cat, stems in _STEMS.items()
}

def find_topics(text: str) -> set[str]:
    """Navne på de følsomme emner, teksten rammer (fx {"sygdom"}). Klienten afgør, hvad der må frigives."""
    return {cat for cat, rx in _PATTERNS.items() if rx.search(text or "")}
