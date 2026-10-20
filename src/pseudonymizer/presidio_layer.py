"""Valgfrit Presidio-lag: navnegenkendelse (NER) som et ekstra net oven på kernen.

Kræver `pip install summer-pseudonymizer[presidio]` og en dansk spaCy-model (fx `python -m spacy download da_core_news_md`).
Laget finder PERSON-spænd, kernen ikke allerede har maskeret, og motoren erstatter dem med `Person-?`. Presidio bruges som
detektor; selve pseudonymiseringen (tokens, beskyttede navne, vagt) ligger stadig i motoren.
Se docs/PRESIDIO.md for målte tal og for, hvornår laget er værd at slå til.
"""
from __future__ import annotations


class PresidioLayer:
    name = "presidio"

    def __init__(self, model: str = "da_core_news_md", language: str = "da", entities=("PERSON",), score_threshold: float = 0.0):
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_analyzer.nlp_engine import NlpEngineProvider
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("Presidio er ikke installeret: pip install 'summer-pseudonymizer[presidio]'") from e
        conf = {"nlp_engine_name": "spacy", "models": [{"lang_code": language, "model_name": model}]}
        engine = NlpEngineProvider(nlp_configuration=conf).create_engine()
        self.language = language
        self.entities = list(entities)
        self.score_threshold = score_threshold
        self.analyzer = AnalyzerEngine(nlp_engine=engine, supported_languages=[language])

    def find_spans(self, text: str) -> list[tuple[int, int, str]]:
        if not text.strip():
            return []
        results = self.analyzer.analyze(text=text, language=self.language, entities=self.entities,
                                        score_threshold=self.score_threshold)
        return [(r.start, r.end, r.entity_type) for r in results]
