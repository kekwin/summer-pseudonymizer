# Roadmap

## Nu (0.2.0)
Kerne uden afhængigheder, valgfrit Presidio-lag, evaluering og et syntetisk korpus (207 tekster), og en navneliste på ca. 133.000 fornavne fra Danmarks Statistik
med justerbar tærskel ([NAVNELISTE.md](NAVNELISTE.md)). Første klient: summer-aula.

## Næste
1. **Større og bedre korpus.** Flere syntetiske tekster (breve, beskeder, ugeplaner, referater), også med sværere tilfælde: kælenavne, navne i
   overskrifter, dobbeltnavne, emojis, sammenskrevne tekster. Hver fejl, en klient finder, bliver en ny testcase (uden rigtige navne).
2. **Flag-og-tillad-løkken som bibliotek.** I dag ligger den lokale visning i summer-aula. Den generelle del (liste over flaggede og tilladte
   ord, regressionstestcases fra flagninger) kan flyttes hertil, så flere klienter får den.
3. **Pakning.** Tagget versioner og en fast måde at hente motoren på (pin til commit-SHA i klientens Dockerfile). Kernen skal blive ved at
   være lille og uden afhængigheder, så en container ikke vokser.
4. **Flere genkendere:** danske virksomhedsnumre (CVR), registreringsnumre, mere præcise adresser (vejnavne med flere ord, stednavne), IBAN.
5. ✅ **Større navneliste** (0.2.0): ca. 133.000 fornavne fra Danmarks Statistik, renset for almindelige ord, tærskel `min_count`. Resten af hullet:
   navne uden for statistikken (se NAVNELISTE.md), fx via flag-og-tillad-løkken, en lille fejltolerant sammenligning med listen (som for kendte navne) eller en NER-model.
6. **Genopfrisk listen** hvert år med `scripts/build_names.py`, når Danmarks Statistik udgiver nye navnelister, og se, om der er kommet antal bærere (så kan
   `min_count` blive til rigtige antal i stedet for forekomster i et nyhedskorpus). Tjek Leipzig-vilkårene (kommerciel brug) før en eventuel udgivelse.

## Træning på stationær maskine (idé, ikke påbegyndt)
Ejerens stationære computer har rigelig CPU og et grafikkort. Den kan bruges til at give motoren "flere muskler", når den kører på en lille
hjemmeserver (6 kerner, 16 GB, ingen GPU, delt med andre tjenester):

- **Finjustere en lille dansk NER-model** (fx en spaCy- eller DaCy-model) **med småt-augmentering**: navne tilfældigt skrevet med småt og med
  stavefejl, så modellen også ser navne som "oline" og "torvald" (i dag fanger ingen af lagene sjældne navne med småt, se PRESIDIO.md).
  Eksportér en lille model til CPU-inferens på serveren.
  Evaluering altid med servervilkår (`docker run --cpus=2 --memory=2g`, se `scripts/bench_presidio.py`).
- **Træne en klassifikator** (vigtig/fyld) hører hjemme i klienten, ikke her.
- **Hurtigere eksperimenter:** lade GPU'en køre sammenligninger af modeller og tærskler, så serveren kun får den vindende, lille model.

**Hård regel:** modeller kan huske navne fra deres træningsdata. Alt, der er trænet på rigtige data (rigtige beskeder, rigtige navne), er
rådata: det må **aldrig** committes til dette offentlige repo (`models/`, `*.pt` m.fl. er git-ignoreret), og det må ikke ligge i et image, der
udgives. Offentlige danske korpusser (fx DaNE) og syntetiske tekster må bruges i åbent regi; tjek licensen først. Rigtige data bruges kun lokalt
hos ejeren, til evaluering og til modeller, der aldrig forlader hans maskiner.

## Hvad der aldrig kommer hertil
Rigtige navne, token-lagre, `.env`, modeller trænet på rigtige data, rigtige beskeder (heller ikke "anonymiserede" uddrag).
