# CLAUDE.md – summer-pseudonymizer

Dansk pseudonymiseringsmotor (tokens, rens, lækagevagt, evaluering; valgfrit Presidio). Repo: https://github.com/kekwin/summer-pseudonymizer
(**offentligt**). Tal med ejeren på dansk. Push direkte til `main`. `python -m unittest discover tests` skal være grøn før push.
Fælles regler: [summer-hub/CLAUDE.md](https://github.com/kekwin/summer-hub/blob/main/CLAUDE.md) (privat repo).

## Regler

- **Navnelisten** (`data/*.txt`) bygges kun af `scripts/build_names.py` af offentlig statistik, aldrig rettes i hånden; manuelle undtagelser hører hjemme i
  `names_da.AMBIGUOUS` (og `RESTORE` i scriptet). Kilder og licens står i docs/NAVNELISTE.md: oplys Danmarks Statistik og Leipzig, hvis listen udgives.

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

`src/pseudonymizer/` (`engine.py`, `store.py`, `textclean.py`, `names.py`, `names_da.py` + `data/fornavne_da.txt`/`efternavne_da.txt`, `topics.py`,
`lexicon.py`, `evaluation.py`, `presidio_layer.py`), `corpus/da_synthetic.json`, `scripts/` (`build_names.py`, `extend_corpus_names.py`,
`eval_thresholds.py`, `bench_names.py`, `bench_presidio.py`), `tests/`, `docs/` (DESIGN, NAVNELISTE, PRESIDIO, ROADMAP).

## Status

0.2.0 (20. oktober 2026): navnelisten er ca. 133.000 fornavne fra Danmarks Statistik (CC BY 4.0, via Digitaliseringsstyrelsen) renset for almindelige ord med
ordfrekvenser fra Leipzig Corpora Collection; tærskel `Pseudonymizer(min_count=N)` (standard 0 = alle; `surname_rank` til efternavne). ca. 0,8 ms ekstra pr. tekst,
16 MB, 250 ms indlæsning. Evaluering (207 tekster): 100 % på identifikatorer, kendte navne, stavefejl og navne på listen, også sjældne med småt
(var 0 af 10); **kendt hul: navne, der ikke står på listen**. Alt står i [docs/NAVNELISTE.md](docs/NAVNELISTE.md). Første klient: summer-aula (fastlåst på en commit).

## Næste skridt

1. Lad summer-aula bruge den nye motor (opdatér ENGINE_SHA/ENGINE_SHA256 i Dockerfile.filter) og vælg `min_count`.
2. Større syntetisk korpus og flag-og-tillad-løkken som bibliotek ([docs/ROADMAP.md](docs/ROADMAP.md)).
3. Tag versioner.
4. Idé: træning/finjustering på ejerens stationære computer; aldrig på rigtige data i dette repo.
