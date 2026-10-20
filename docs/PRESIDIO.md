# Presidio som valgfrit lag: målinger

Målt 20. oktober 2026 på det syntetiske korpus (`corpus/da_synthetic.json`, 61 tekster, 5 navne først i en sætning). Kørt i Docker med
`--cpus=2 --memory=3g` (en lille serverprofil), Python 3.12, `presidio-analyzer` og `spacy`, danske spaCy-modeller. Script:
`scripts/bench_presidio.py`.

| Opsætning | Navne først i sætning fanget | Overmaskering | Lækager i alt | Indlæsning | Pr. tekst | Spids-RAM |
|---|---|---|---|---|---|---|
| Kerne alene | 2 af 5 | 3,5 % | 3 | - | - | lille |
| + Presidio, `da_core_news_sm` | 3 af 5 | 4,7 % | 2 | 1,4 s | 2 ms | ca. 150 MB |
| + Presidio, `da_core_news_md` | **4 af 5** | 3,5 % | 1 | 1,6 s | 3 ms | ca. 340 MB |
| + Presidio, `da_core_news_lg` | 4 af 5 | 3,5 % | 1 | 1,8 s | 3 ms | ca. 910 MB |

Alle andre kategorier (CPR, telefon, e-mail, adresse, link, konto, kendte navne, stavefejl, ukendte navne midt i en sætning) var allerede
100 % med kernen alene; Presidio ændrer dem ikke.

## Hvad tallene siger, og ikke siger
- Presidio med `md` fanger de ukendte navne først i en sætning, som kernen ikke kan se ("Tobias ...", "Mille ..."). Det mangler stadig kælenavne
  ("Ossi"). Det er det, laget er til: et ekstra net for navne, kernen ikke kender.
- `md` er det fornuftige valg: samme resultat som `lg` med en tredjedel af hukommelsen. `sm` overmaskerer lidt mere og fanger færre.
- Det er **billigt**: under 4 ms pr. tekst og ca. 340 MB, også på 2 CPU-kerner. Det passer fint til en lille hjemmeserver.
- Korpusset er lille og skrevet af os. Tallene er et fingerpeg, ikke en garanti. Den rigtige måling kræver klientens egen mærkede prøve (lokalt).
- Laget kan give flere falske fund (steder, firmanavne, sygdomsnavne som PERSON). Motoren godtager kun spænd, der starter med stort bogstav (danske navne skrives med stort), og det fjernede fx "hånd-fod-mundsyge" som falsk fund. Overmaskeringen i korpusset er uændret, men prøv det på rigtige tekster.

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
