"""Pseudonymiseringsmotoren og lækagevagten.

Rækkefølge: scrub (CPR, telefon, ...) -> kendte navne fra token-lageret -> udløsere ("mormor X") -> flaggede ord ->
valgfrie lag (fx Presidio/NER) -> (valgfrit) streng maskering af ukendte store ord -> lækagevagt.
Vagten kører til sidst og tilbageholder hele teksten, hvis noget af det, der skulle være væk, stadig står der.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Protocol

from .lexicon import ALWAYS_OK, STARTERS, WEEKDAYS_MONTHS
from .names_da import COMMON_FIRST_NAMES
from .store import TokenStore
from .textclean import find_identifiers, scrub
from .topics import find_topics

AMBIGUOUS_CHILD = "Barn-?"
AMBIGUOUS_PERSON = "Person-?"
_ZERO_WIDTH = ("​", "‌", "‍", "﻿", "­")

_TRIGGERS = (
    r"mor|far|mormor|morfar|farmor|farfar|bedstemor|bedstefar|oldemor|oldefar|onkel|tante|søster|bror|veninde|ven|"
    r"kammerat|klassekammerat|vikar|nabo|dagplejer|hr|fru|pædagog|lærer|assistent"
)
_TRIGGER_RE = re.compile(
    rf"(?<!\w)(?P<t>(?i:{_TRIGGERS}))\.?\s+(?P<n>[A-ZÆØÅ][a-zæøåé]+(?:\s[A-ZÆØÅ][a-zæøåé]+)?)(?![\w-])"
)
_CAP_WORD = re.compile(r"[A-ZÆØÅ][\wæøåÆØÅ'-]*")
_ACRONYM_HYPHEN = re.compile(r"^[A-ZÆØÅ]{2,}-")
_COMMON_NAMES_RE = re.compile(
    r"(?<!\w)(?P<n>" + "|".join(re.escape(n) for n in sorted(COMMON_FIRST_NAMES, key=len, reverse=True)) + r")(?P<g>['’]?s)?(?!\w)",
    re.I,
)
_TOKEN_LIKE = re.compile(r"^(?:[A-ZÆØÅ][a-zæøå]+)-(?:\d+|\?)")


def _within_one(a: str, b: str) -> bool:
    """Højst én tastefejl (ombytning, tilføjelse, fjernelse eller udskiftning af ét tegn)."""
    if a == b:
        return True
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if la == lb:
        diff = [i for i in range(la) if a[i] != b[i]]
        if len(diff) == 1:
            return True
        return len(diff) == 2 and diff[1] == diff[0] + 1 and a[diff[0]] == b[diff[1]] and a[diff[1]] == b[diff[0]]
    short, long_ = (a, b) if la < lb else (b, a)
    i = j = 0
    skipped = False
    while i < len(short) and j < len(long_):
        if short[i] == long_[j]:
            i += 1
            j += 1
        elif skipped:
            return False
        else:
            skipped = True
            j += 1
    return True


class Layer(Protocol):
    """Et ekstra genkendelseslag (fx Presidio). Får teksten og returnerer (start, slut, mærke) for det, der skal maskeres."""

    name: str

    def find_spans(self, text: str) -> list[tuple[int, int, str]]: ...


@dataclass
class Cleaned:
    text: str
    topics: set = field(default_factory=set)
    leak: list = field(default_factory=list)
    counts: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.leak


class Pseudonymizer:
    def __init__(self, store: TokenStore, extra_words=(), layers=(), common_names: bool = True):
        self.store = store
        self.layers = list(layers)
        self.extra_words = [w for w in extra_words if w and len(w.strip()) >= 2]
        self._sig = None
        self._long = None
        self._short = None
        self._lookup_long: dict[str, set] = {}
        self._lookup_short: dict[str, set] = {}
        self._extra_rx = None
        self._fuzzy_index: dict[str, list] = {}
        self.fuzzy = True
        self.common_names = common_names
        self.trace: list | None = None   # sættes af en visning: [(token, original, lag)]
        if self.extra_words:
            alt = "|".join(re.escape(w.strip()) for w in sorted(self.extra_words, key=len, reverse=True))
            self._extra_rx = re.compile(rf"(?<!\w)(?:{alt})s?(?!\w)", re.I)

    # ------------------------------------------------------------------ opbygning
    def _rebuild(self) -> None:
        entries = self.store.data["entries"]
        sig = (len(entries), sum(len(e["names"]) for e in entries.values()), len(self.store.protected))
        if sig == self._sig:
            return
        self._sig = sig
        self._lookup_long, self._lookup_short = {}, {}
        for variant, tok in self.store.variants():
            if len(variant) >= 3:
                self._lookup_long.setdefault(variant.casefold(), set()).add(tok)
            else:
                self._lookup_short.setdefault(variant, set()).add(tok)
        self._fuzzy_index = {}
        for variant, tok in self.store.variants():
            if len(variant) >= 4:
                cf = variant.casefold()
                self._fuzzy_index.setdefault(cf[0], []).append((cf, tok))
        tail = r"(?:\s(?-i:[A-ZÆØÅ])\.)?(?P<g>['’]?s)?(?!\w)"
        self._long = self._short = None
        if self._lookup_long:
            alt = "|".join(re.escape(v) for v in sorted(self._lookup_long, key=len, reverse=True))
            self._long = re.compile(rf"(?<!\w)(?P<n>{alt}){tail}", re.I)
        if self._lookup_short:
            alt = "|".join(re.escape(v) for v in sorted(self._lookup_short, key=len, reverse=True))
            self._short = re.compile(rf"(?<!\w)(?P<n>{alt}){tail}")

    def _trace(self, token: str, original: str, layer: str) -> None:
        if self.trace is not None:
            self.trace.append((token, original, layer))

    @staticmethod
    def _pick(tokens: set) -> str:
        if len(tokens) == 1:
            return next(iter(tokens))
        return AMBIGUOUS_CHILD if all(t.startswith("Barn-") for t in tokens) else AMBIGUOUS_PERSON

    def _sub_names(self, text: str) -> str:
        if self._long:
            def rep(m, lookup=self._lookup_long):
                tok = self._pick(lookup[m.group("n").casefold()])
                self._trace(tok, m.group(0), "navn")
                return tok + ("'s" if m.group("g") else "")
            text = self._long.sub(rep, text)
        if self._short:
            def rep2(m, lookup=self._lookup_short):
                tok = self._pick(lookup[m.group("n")])
                self._trace(tok, m.group(0), "navn")
                return tok + ("'s" if m.group("g") else "")
            text = self._short.sub(rep2, text)
        return text

    # ------------------------------------------------------------------ stavefejl i kendte navne
    def _fuzzy_names(self, text: str, allowed=frozenset()) -> str:
        """Et stort ord, der kun er én tastefejl fra et kendt navn (samme begyndelsesbogstav, mindst 4 tegn), maskeres som navnet."""
        if not self._fuzzy_index:
            return text
        allowed_cf = {a.casefold() for a in set(allowed) | self.store.protected}

        def rep(m: re.Match) -> str:
            w = m.group(0)
            if len(w) < 4 or _TOKEN_LIKE.match(w) or w.isupper() or _ACRONYM_HYPHEN.match(w) or w.endswith("-"):
                return w
            for cand, genitive in ((w, False), (w[:-1], True) if w.endswith("s") else (None, False)):
                if not cand or len(cand) < 4:
                    continue
                cf = cand.casefold()
                if cf in allowed_cf or cf in STARTERS or cf in ALWAYS_OK or cf in WEEKDAYS_MONTHS:
                    continue
                hits = {tok for v, tok in self._fuzzy_index.get(cf[0], ()) if v != cf and _within_one(cf, v)}
                if hits:
                    tok = self._pick(hits)
                    self._trace(tok, w, "stavefejl")
                    return tok + ("'s" if genitive else "")
            return w

        return _CAP_WORD.sub(rep, text)

    # ------------------------------------------------------------------ almindelige danske fornavne (også med småt)
    def _common_names(self, text: str, allowed=frozenset()) -> str:
        skip = {a.casefold() for a in set(allowed) | self.store.protected}

        def rep(m: re.Match) -> str:
            name = m.group("n")
            if name.casefold() in skip or name.casefold() in STARTERS or name.casefold() in ALWAYS_OK:
                return m.group(0)
            self._trace(AMBIGUOUS_PERSON, m.group(0), "navneliste")
            return AMBIGUOUS_PERSON + ("'s" if m.group("g") else "")

        return _COMMON_NAMES_RE.sub(rep, text)

    # ------------------------------------------------------------------ ekstra lag (NER/Presidio)
    @staticmethod
    def _looks_like_common_word(piece: str) -> bool:
        """Et spænd fra et NER-lag, der starter med småt: er det et almindeligt ord eller et emneord frem for et navn?"""
        if any(ch.isdigit() for ch in piece) or find_topics(piece):
            return True
        words = re.findall(r"[\wæøåÆØÅ]+", piece.casefold())
        return bool(words) and all(w in STARTERS or w in ALWAYS_OK or w in WEEKDAYS_MONTHS for w in words)

    def _apply_layers(self, text: str) -> str:
        for layer in self.layers:
            spans = sorted(layer.find_spans(text), key=lambda s: s[0])
            out, pos = [], 0
            for start, end, _label in spans:
                if start < pos or not (0 <= start < end <= len(text)):
                    continue
                piece = text[start:end]
                if "[" in piece or "]" in piece or _TOKEN_LIKE.match(piece) or piece in (AMBIGUOUS_PERSON, AMBIGUOUS_CHILD):
                    continue
                if piece.strip().casefold() in {p.casefold() for p in self.store.protected}:
                    continue
                if not piece[:1].isupper() and self._looks_like_common_word(piece):
                    continue  # navne kan være skrevet med småt, men almindelige ord og sygdomsnavne er ikke personer
                self._trace(AMBIGUOUS_PERSON, piece, layer.name)
                out.append(text[pos:start])
                out.append(AMBIGUOUS_PERSON)
                pos = end
            out.append(text[pos:])
            text = "".join(out)
        return text

    # ------------------------------------------------------------------ streng maskering
    def mask_unknown_caps(self, text: str, allowed=frozenset(), level: int = 2) -> str:
        """Maskér store ord, der ikke er kendte. Niveau 1: kun midt i en sætning (danske navneord er med småt, så det
        er næsten altid navne og steder). Niveau 2: også først i en sætning, medmindre det er et almindeligt åbningsord."""
        allowed_cf = {a.casefold() for a in set(allowed) | self.store.protected}

        def rep(m: re.Match) -> str:
            w = m.group(0)
            s = m.start()
            if len(w) == 1 or _TOKEN_LIKE.match(w) or w.isupper() or _ACRONYM_HYPHEN.match(w):
                return w
            if w.endswith("-") and text[m.end():m.end() + 1] == "?":  # "Person-?"
                return w
            base = w.rstrip("s").rstrip("'") if w.endswith(("s", "'s")) else w
            cf = w.casefold()
            if cf in allowed_cf or base.casefold() in allowed_cf or cf in WEEKDAYS_MONTHS:
                return w
            prev = text[:s].rstrip(" \t")
            if prev.endswith("["):  # [CPR]
                return w
            sentence_start = (not prev) or (prev[-1] in ".!?:\n" and not prev.endswith("-?")) or prev.endswith(("\n", "•", "-"))
            if sentence_start and (level < 2 or cf in STARTERS):
                return w
            if cf in ALWAYS_OK or base.casefold() in ALWAYS_OK:
                return w
            self._trace(AMBIGUOUS_PERSON, w, "ukendt stort ord")
            return AMBIGUOUS_PERSON

        return _CAP_WORD.sub(rep, text)

    # ------------------------------------------------------------------ hovedfunktion
    def clean(self, text: str, strict: int = 1, allowed=frozenset()) -> Cleaned:
        original = unicodedata.normalize("NFC", text or "")
        for z in _ZERO_WIDTH:
            original = original.replace(z, "")
        topics = find_topics(original)
        self._rebuild()
        t, counts = scrub(original)
        t = self._sub_names(t)
        if self.fuzzy:
            t = self._fuzzy_names(t, allowed)
        if self.common_names and strict:
            t = self._common_names(t, allowed)

        def trig(m):
            self._trace(AMBIGUOUS_PERSON, m.group("n"), "udløser")
            return f"{m.group('t')} {AMBIGUOUS_PERSON}"

        t = _TRIGGER_RE.sub(trig, t)
        if self._extra_rx:
            def extra(m):
                self._trace(AMBIGUOUS_PERSON, m.group(0), "flaget af dig")
                return AMBIGUOUS_PERSON
            t = self._extra_rx.sub(extra, t)
        if self.layers:
            t = self._apply_layers(t)
        if strict:
            t = self.mask_unknown_caps(t, allowed, int(strict))
        return Cleaned(text=t, topics=topics, leak=self.leaks(t), counts=counts)

    # ------------------------------------------------------------------ lækagevagt
    def leaks(self, text: str) -> list[str]:
        self._rebuild()
        found = list(find_identifiers(text))
        if self._long and self._long.search(text):
            found.append("kendt navn")
        if self._short and self._short.search(text):
            found.append("kendt navn (kort)")
        if _TRIGGER_RE.search(text):
            found.append("udløser + stort ord")
        if self._extra_rx and self._extra_rx.search(text):
            found.append("flaget ord")
        return found
