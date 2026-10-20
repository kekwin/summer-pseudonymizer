# CLAUDE.md – summer-pseudonymizer

Dansk pseudonymiseringsmotor (tokens, rens, lækagevagt, evaluering; valgfrit Presidio). Repo: https://github.com/kekwin/summer-pseudonymizer
(**offentligt**). Tal med ejeren på dansk. Push direkte til `main`. `python -m unittest discover tests` skal være grøn før push.
Fælles regler: [summer-hub/CLAUDE.md](https://github.com/kekwin/summer-hub/blob/main/CLAUDE.md) (privat repo).

## Regler

- **Offentligt repo, ingen hemmeligheder eller rigtige data.** Kun kode, danske ordlister og syntetiske, opdigtede tekster (`example.invalid`).
  Aldrig token-lagre (de har rigtige navne), `.env`, rigtige beskeder (heller ikke "anonymiserede" uddrag) eller modeller trænet på rigtige data.
  `tests/test_no_secrets.py` fanger de fleste fejl; tænk selv, før du committer.
- **Kernen har ingen afhængigheder** (kun standardbibliotek). Presidio/spaCy kun som valgfrit lag.
- **Fejl lukker.** Er motoren i tvivl, skal klienten få "tilbehold", ikke ufiltreret tekst.
- Motoren kender ikke Aula eller andre klienter. Klient-specifik viden (felter, trådtyper, hvidlister) hører hjemme i klienten.
- **Licens: MIT**, ejer "Kewin Sommer Pedersen" (valgt 20. oktober 2026). README skal blive ved at sige, at værktøjet ikke garanterer
  anonymisering.

## Kør og test

`python -m unittest discover tests` · `PYTHONPATH=src python -m pseudonymizer corpus/da_synthetic.json [--presidio]` (Presidio køres i Docker,
se [docs/PRESIDIO.md](docs/PRESIDIO.md)).

## Struktur

`src/pseudonymizer/` (`engine.py`, `store.py`, `textclean.py`, `names.py`, `topics.py`, `lexicon.py`, `evaluation.py`, `presidio_layer.py`),
`corpus/da_synthetic.json`, `scripts/bench_presidio.py`, `tests/`, `docs/` (DESIGN, PRESIDIO, ROADMAP).

## Status

0.1.0 (20. oktober 2026): udtrukket fra summer-aulas filter. Evaluering: 100 % på identifikatorer, kendte navne (også med småt), stavefejl og
almindelige fornavne; **kendt hul: sjældne ukendte navne med småt (0 af 10)**; Presidio `md` hjælper på sjældne navne med stort. Første klient: summer-aula.

## Næste skridt

1. Lad summer-aula bruge motoren (pin til commit-SHA i Dockerfile) og fjerne sin egen kopi.
2. Større syntetisk korpus og flag-og-tillad-løkken som bibliotek ([docs/ROADMAP.md](docs/ROADMAP.md)).
3. Tag versioner.
4. Idé: træning/finjustering på ejerens stationære computer; aldrig på rigtige data i dette repo.
