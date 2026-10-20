"""Tekstrens: HTML til tekst og fjernelse af CPR, telefon, e-mail, links og adresser. Alt erstattes af [MÆRKE]."""
from __future__ import annotations

import html as _html
import re

PLACEHOLDERS = ("[CPR]", "[TELEFON]", "[EMAIL]", "[LINK]", "[ADRESSE]", "[KONTO]", "[NUMMER]")

_BLOCK_END = re.compile(r"</(?:p|div|li|h[1-6]|tr)>|<(?:p|div|li|h[1-6])[^>]*>|<br\s*/?>|<hr\s*/?>", re.I)
_TAG = re.compile(r"<[^>]*>")


def html_to_text(s: str) -> str:
    if not s:
        return ""
    s = _BLOCK_END.sub("\n", s)
    s = _TAG.sub("", s)
    s = _html.unescape(s)
    s = s.replace(" ", " ").replace("​", "")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r" *\n *", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_URL = re.compile(r"(?:https?://|www\.)[^\s<>\"')\]]+", re.I)
_CPR = re.compile(r"(?<!\d)(?:0[1-9]|[12]\d|3[01])(?:0[1-9]|1[0-2])\d{2}[-\s]?\d{4}(?!\d)")
# 8 cifre i grupper à 2 (evt. +45); ikke datoer som 2026-10-19 eller 12.10.2026 eller tidspunkter
_PHONE = re.compile(
    r"(?<![\d-])(?!\d{4}-\d{2}-\d{2})(?!\d{1,2}[./-]\d{1,2}[./-]\d{2,4})(?!(?:19|20)\d{2}[\s./–-]+(?:19|20)?\d{2}(?!\d))"
    r"(?:(?:\+|00)45[\s-]?)?(?:(?:\d{2}[\s.-]?){3}\d{2}|(?!(?:19|20)\d{2}[\s.]\d{4})\d{4}[\s.]\d{4})(?![\d])"
)
_STREET = (
    r"[A-ZÆØÅ][\wæøåÆØÅ]*(?:vej|gade|allé|alle|vænge|vænget|stræde|torv|plads|park|boulevard|sti|have|bakke|"
    r"ager|høj|lund|engen|toften|marken)"
)
_ADDRESS = re.compile(
    rf"(?<!\w){_STREET}\s+\d{{1,3}}[A-Za-z]?"
    r"(?:,?\s*(?:\d{1,2}\.?\s*(?:sal\.?|th\.?|tv\.?|mf\.?)|st\.?\s*(?:th|tv)?\.?|\d{1,2}\.\s*(?:th|tv|mf)\.?))*"
    r"(?:,?\s*[1-9]\d{3}\s+[A-ZÆØÅ][\wæøåÆØÅ]+(?:\s[A-ZÆØÅ]\b)?)?"
)
_ACCOUNT = re.compile(
    r"(?i:reg(?:istrerings)?\.?\s*(?:nr\.?|nummer)?|konto(?:nr\.?|nummer)?|mobilepay(?:\s*(?:nr\.?|nummer|box))?|iban)"
    r"\s*[:.]?\s*[A-Z]{0,2}\d[\d\s-]{3,}\d")
_HANDLE = re.compile(r"(?<![\w.])@[A-Za-z0-9_.]{3,}")
_LONGNUM = re.compile(r"(?<![\d-])\d{9,}(?![\d])")
_POSTCODE = re.compile(r"(?<!\d)[1-9]\d{3}\s+(?!Kr\b|DKK\b)[A-ZÆØÅ][a-zæøå]+(?:\s[A-ZÆØÅ]\b)?")


def scrub(text: str) -> tuple[str, dict[str, int]]:
    """Fjern direkte identifikatorer. Returnerer (ren tekst, antal pr. type)."""
    counts: dict[str, int] = {}

    def sub(rx: re.Pattern, mark: str, s: str) -> str:
        s, n = rx.subn(mark, s)
        if n:
            counts[mark] = counts.get(mark, 0) + n
        return s

    text = sub(_EMAIL, "[EMAIL]", text)
    text = sub(_URL, "[LINK]", text)
    text = sub(_HANDLE, "[LINK]", text)
    text = sub(_ACCOUNT, "[KONTO]", text)
    text = sub(_CPR, "[CPR]", text)
    text = sub(_ADDRESS, "[ADRESSE]", text)
    text = sub(_POSTCODE, "[ADRESSE]", text)
    text = sub(_PHONE, "[TELEFON]", text)
    text = sub(_LONGNUM, "[NUMMER]", text)
    return text, counts


def find_identifiers(text: str) -> list[str]:
    """Bruges af lækagevagten: hvilke typer identifikatorer står der stadig i teksten?"""
    probe = text
    for p in PLACEHOLDERS:
        probe = probe.replace(p, " ")
    found = []
    for name, rx in (("email", _EMAIL), ("link", _URL), ("link", _HANDLE), ("konto", _ACCOUNT), ("cpr", _CPR),
                     ("adresse", _ADDRESS), ("postnr", _POSTCODE), ("telefon", _PHONE), ("nummer", _LONGNUM)):
        if rx.search(probe):
            found.append(name)
    return found
