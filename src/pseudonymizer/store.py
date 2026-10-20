"""Token-lageret: faste pseudonymer. Samme person får altid samme token, og et token genbruges aldrig.

Filen indeholder rigtige navne, så den skal behandles som rådata: aldrig i git, aldrig til en AI. Kun tokens gives videre.
Motoren kender ikke noget om Aula eller andre klienter; en klient kan gemme sin egen tilstand i `store.meta`.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .names import name_variants

# Standard-præfikser (dansk skole/institution). En klient kan bruge egne præfikser; "Person" bruges til ukendt/flertydig.
DEFAULT_PREFIXES = ("Barn", "Forælder", "Pædagog", "Lærer", "Ansat", "Person")
# Præfikser, der er udskiftelige for samme person (en ansat kan først ses som "Ansat" og senere få titlen "Pædagog").
DEFAULT_GROUPS = {"Pædagog": "Ansat", "Lærer": "Ansat", "Ansat": "Ansat"}
VERSION = 2


class TokenStore:
    def __init__(self, path: Path | str | None = None, groups: dict | None = None):
        self.path = Path(path) if path else None
        self.groups = dict(DEFAULT_GROUPS if groups is None else groups)
        self.data: dict = {
            "version": VERSION,
            "counters": {},
            "entries": {},    # token -> {"prefix", "names": [...], "keys": [...]}
            "keys": {},       # nøgle -> token
            "protected": [],  # navne, der aldrig maskeres (fx egen familie)
            "meta": {},       # fri tilstand til klienten
        }
        if self.path and self.path.exists():
            try:
                loaded = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                raise RuntimeError("token-lageret kan ikke læses; rør det ikke (fejl lukker)")
            if not isinstance(loaded, dict) or loaded.get("version") != VERSION:
                raise RuntimeError("token-lagerets version passer ikke; rør det ikke (fejl lukker)")
            for k in self.data:
                if k in loaded:
                    self.data[k] = loaded[k]

    # ------------------------------------------------------------------ beskyttede navne og klienttilstand
    @property
    def protected(self) -> set:
        return set(self.data["protected"])

    def add_protected(self, names) -> None:
        cur = self.data["protected"]
        new = [n for n in names if n and n not in cur]
        if new:
            cur.extend(new)
            self.save()

    @property
    def meta(self) -> dict:
        return self.data["meta"]

    # ------------------------------------------------------------------ tokens
    def _group(self, prefix: str) -> str:
        return self.groups.get(prefix, prefix)

    def _compatible(self, a: str, b: str) -> bool:
        return self._group(a) == self._group(b) or "Person" in (a, b)

    def prefixes(self) -> set:
        return set(DEFAULT_PREFIXES) | {e["prefix"] for e in self.data["entries"].values()}

    def token(self, prefix: str, key: str, names=(), unique_first_name: bool = False) -> str:
        """Find eller opret token til en person. `key` er id'et (fx p:123) eller et normaliseret navn (n:...)."""
        if not prefix or not prefix.isalpha():
            raise ValueError("præfikset skal være bogstaver")
        names = [n for n in names if n]
        tok = self.data["keys"].get(key)
        if tok is None:
            tok = self._match_by_name(prefix, names, unique_first_name)
            if tok is not None:
                self.data["keys"][key] = tok
                self.data["entries"][tok]["keys"].append(key)
        if tok is None:
            n = self.data["counters"].get(prefix, 0) + 1
            tok = f"{prefix}-{n}"
            while tok in self.data["entries"]:  # aldrig genbrug
                n += 1
                tok = f"{prefix}-{n}"
            self.data["counters"][prefix] = n
            self.data["entries"][tok] = {"prefix": prefix, "names": [], "keys": [key]}
            self.data["keys"][key] = tok
        entry = self.data["entries"][tok]
        for n in names:
            if n not in entry["names"]:
                entry["names"].append(n)
        self.save()
        return tok

    def _match_by_name(self, prefix: str, names: list[str], unique_first: bool) -> str | None:
        wanted = {" ".join(n.split()).casefold() for n in names if " " in n.strip()}
        if wanted:
            for tok, e in self.data["entries"].items():
                if not self._compatible(e["prefix"], prefix):
                    continue
                have = {" ".join(n.split()).casefold() for n in e["names"] if " " in n.strip()}
                if wanted & have:
                    return tok
        if unique_first:
            firsts = {n.split()[0].casefold() for n in names if n.split()}
            hits = [t for t, e in self.data["entries"].items()
                    if self._compatible(e["prefix"], prefix)
                    and firsts & {n.split()[0].casefold() for n in e["names"] if n.split()}]
            if len(hits) == 1:
                return hits[0]
        return None

    def variants(self) -> list[tuple[str, str]]:
        """Alle (variant, token) til genkendelse i fritekst. Beskyttede navne er aldrig med."""
        protected = {n.casefold() for n in self.protected}
        out: list[tuple[str, str]] = []
        for tok, e in self.data["entries"].items():
            for name in e["names"]:
                for v in name_variants(name):
                    if v.casefold() in protected:
                        continue
                    out.append((v, tok))
        return out

    # ------------------------------------------------------------------ fil
    def save(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(self.path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=1)
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
