# Presidio som valgfrit lag: målinger

Målt 20. oktober 2026 på det syntetiske korpus (`corpus/da_synthetic.json`, 68 tekster). Kørt i Docker med `--cpus=2 --memory=3g` (en lille
serverprofil), Python 3.12, `presidio-analyzer` og `spacy`, danske spaCy-modeller. Script: `scripts/bench_presidio.py`.

| Opsætning | Ukendt, først i sætning | Ukendt, småt (almindeligt navn) | Sjældent navn, stort | Sjældent navn, **småt** | Overmaskering | Indlæsning | Pr. tekst | Spids-RAM |
|---|---|---|---|---|---|---|---|---|
| Kerne alene (med navneliste) | 4 af 5 | 6 af 6 | 2 af 4 | **0 af 10** | 2,8 % | - | - | lille |
| + Presidio, `sm` | 4 af 5 | 6 af 6 | 2 af 4 | 1 af 10 | 4,6 % | 1,4 s | 2 ms | ca. 150 MB |
| + Presidio, `md` | 4 af 5 | 6 af 6 | **4 af 4** | 1 af 10 | 2,8 % | 1,7 s | 3 ms | ca. 340 MB |
| + Presidio, `lg` | 4 af 5 | 6 af 6 | 4 af 4 | 0 af 10 | 2,8 % | 2,0 s | 3 ms | ca. 910 MB |

Navne, **motoren kender** (fra strukturerede felter), findes uanset store/små bogstaver: 100 % (også `navn-kendt-småt`). Identifikatorer (CPR,
telefon, e-mail, adresse, link, konto) og stavefejl er 100 % med kernen alene.

## Hvad tallene siger, og ikke siger
- **Små bogstaver er det svage punkt.** Navne kan sagtens være skrevet med småt i en besked ("ring til oline"). Kendte navne og almindelige danske
  fornavne (en indbygget liste) fanges, uanset hvordan de er skrevet. **Sjældne, ukendte navne med småt fanges stort set ikke**, hverken af
  kernen eller af Presidio: spaCys danske modeller genkender navne på store bogstaver og ser næsten intet, når navnet står med småt.
- Presidio (`md`) hjælper på **sjældne navne med stort** (4 af 4 mod 2 af 4), især først i en sætning. `md` er det fornuftige valg: samme resultat
  som `lg` med en tredjedel af hukommelsen; `sm` overmaskerer mere.
- Det er billigt: under 4 ms pr. tekst og ca. 340 MB på 2 kerner. Det passer til en lille hjemmeserver.
- **Navnelisten er skrevet af os og korpusset også**; kernens tal for almindelige navne er derfor optimistiske. Korpusset er lille og syntetisk.
  Den rigtige måling kræver klientens egen mærkede prøve (lokalt).
- Laget kan give falske fund (steder, firmanavne, sygdomsnavne). Små spænd, der ligner almindelige ord eller emneord (fx "hånd-fod-mundsyge"),
  afvises af motoren; men man kan ikke kræve stort begyndelsesbogstav, fordi navne med småt er virkelige.

## Hvad der kan løse hullet med sjældne navne med småt
1. En **langt større navneliste** bygget af offentlig navnestatistik (fx Danmarks Statistik), renset for navne, der også er almindelige ord.
2. En **NER-model trænet med småt-augmentering** (navne tilfældigt skrevet med småt og med stavefejl). Det er en oplagt opgave til en stationær
   maskine med grafikkort; se [ROADMAP](ROADMAP.md). Kør derefter modellen på CPU (spaCy-format) som et Presidio-lag.
3. Klientens egen flagning: hvert navn, der slap igennem, tilføjes til listen og huskes.
4. Streng tilstand (`strict=2`) og klientens egne regler for tråde, hvor en fejl er dyr.

## Sådan slår du det til

```bash
pip install "summer-pseudonymizer[presidio]"
python -m spacy download da_core_news_md
```

```python
from pseudonymizer import Pseudonymizer
from pseudonymizer.presidio_layer import PresidioLayer
p = Pseudonymizer(store, layers=[PresidioLayer(model="da_core_news_md")])
```

Husk at tjekke licensen for den spaCy-model, du vælger, før du udgiver noget, der indeholder den.
