"""summer-pseudonymizer: dansk pseudonymisering af tekst, så den kan vises for en AI uden at andre kan genkendes.

Kernen er uden afhængigheder (kun standardbibliotek). Presidio/spaCy er et valgfrit lag (`pip install .[presidio]`).
Se README.md og docs/DESIGN.md.
"""
from .engine import AMBIGUOUS_CHILD, AMBIGUOUS_PERSON, Cleaned, Layer, Pseudonymizer
from .names import first_name, name_variants
from .store import DEFAULT_GROUPS, DEFAULT_PREFIXES, TokenStore
from .textclean import PLACEHOLDERS, find_identifiers, html_to_text, scrub
from .topics import find_topics

__version__ = "0.1.0"

__all__ = [
    "AMBIGUOUS_CHILD", "AMBIGUOUS_PERSON", "Cleaned", "DEFAULT_GROUPS", "DEFAULT_PREFIXES", "Layer", "PLACEHOLDERS",
    "Pseudonymizer", "TokenStore", "find_identifiers", "find_topics", "first_name", "html_to_text", "name_variants", "scrub",
]
