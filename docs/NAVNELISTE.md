# Navnelisten: kilder, licens, filter, tærskel og målinger

Hullet i 0.1.0 var **sjældne, ukendte navne skrevet med småt** ("ring til oline"): kernen kendte kun ca. 400 fornavne skrevet efter hukommelsen. Siden
0.2.0 bruger motoren en langt større liste (ca. 133.000 fornavne) bygget af offentlig statistik, med en **justerbar tærskel**. Listen er et billigt
opslag i et sæt på hele ord; kernen er stadig uden afhængigheder.

## Kilder

| Hvad | Kilde | Licens og kildeangivelse |
|---|---|---|
| Alle fornavne (kvinder, mænd) med mindst 3 bærere, de 1000 mest frekvente fornavne (rang) og de 5000 mest frekvente efternavne (rang) | **Danmarks Statistik**, "Navne registreret i Danmark", stand januar 2020 (CPR). Udgivet som åbne data af Digitaliseringsstyrelsen: [sprogteknologi.dk/dataset/fornavne-og-efternavne-i-befolkningen-i-danmark](https://sprogteknologi.dk/dataset/fornavne-og-efternavne-i-befolkningen-i-danmark), fil `navne_registreret_i_danmark_2020.zip` | **CC BY 4.0** ([tekst](https://creativecommons.org/licenses/by/4.0/)); Danmarks Statistik angives som kilde. Se også [Brug statistikken](https://www.dst.dk/da/Statistik/brug-statistikken) |
| Ordfrekvenser (til at finde navne, der også er almindelige ord, og til "forekomster" pr. navn) | **Leipzig Corpora Collection**, `dan_news_2021_1M` (nyheder, 1 mio. sætninger, ca. 20 mio. ord) og `dan_wikipedia_2021_1M` (Wikipedia, 1 mio. sætninger), [wortschatz.uni-leipzig.de](https://wortschatz.uni-leipzig.de/en/download). Citér: D. Goldhahn, T. Eckart, U. Quasthoff (2012), *Building Large Monolingual Dictionaries at the Leipzig Corpora Collection: From 100 to 200 Languages*, LREC 2012 | Udgiveren angiver **CC BY** for korpusserne. **Bemærk:** ældre udgaver af siden nævner også, at brug er gratis til ikke-kommercielle formål; jeg kunne ikke læse vilkårsiden maskinelt (den er bag en bot-kontrol), så **tjek [vilkårene](https://wortschatz.uni-leipzig.de/en/usage) før kommerciel brug**. Repoet indeholder ingen korpustekst, kun et tal pr. navn (hyppighed) |

Hentet 20. oktober 2026. Sha256 af de hentede filer (så kørslen kan genkendes):

- `navne_registreret_i_danmark_2020.zip`: `550f59b4368e0f1c76ecf6cf573d5bdf4bee1b9a409fdc4ef2bc6e4106c439c3`
- `dan_news_2021_1M.tar.gz`: `9d778504aab44fef53df07d99bb6c6b773914439fc2410bd277cc78c9784c32f`
- `dan_wikipedia_2021_1M.tar.gz`: `9ccad7f7fd5399e6040864cb1735bdd698c336b4119e788047352bdf48ada59a`

### Hvorfor ikke Statistikbanken?
Jeg undersøgte først Statistikbanken (API'et `api.statbank.dk`). **Danmarks Statistiks navnestatistik findes ikke i Statistikbanken**
(dokumentationen siger det udtrykkeligt), og emnet "Navne" indeholder ingen tabeller. Hjemmesiden har kun top-20-lister, "topscorer"-lister pr. region
og alder, nyfødte (top 50 pr. år) og et opslag pr. navn ("Hvor mange hedder...?"). Der er altså **ingen offentlig samlet tabel med antal bærere pr. navn**,
og et opslag pr. navn for titusinder af navne ville være skrabning af en tjeneste, som ikke er lavet til det. Den fulde liste findes kun som ovennævnte
åbne datasæt, og **den indeholder ikke antal bærere**: "alle"-filerne er alfabetiske lister over navne med mindst 3 bærere, og kun de 1000 (fornavne) og
5000 (efternavne) mest frekvente er sorteret efter frekvens. Navne med færre end 3 bærere er udeladt af Danmarks Statistik (fortrolighed).

## Hvad der ligger i repoet

`src/pseudonymizer/data/fornavne_da.txt` (1,6 MB, ca. 132.800 navne) og `efternavne_da.txt` (4.700). Kun navn og tal; intet om enkeltpersoner.

- `fornavne_da.txt`: `navn <TAB> rang <TAB> forekomster`. **Rang** er pladsen blandt Danmarks Statistiks 1000 mest frekvente fornavne (0 = ikke blandt dem).
  **Forekomster** er, hvor mange gange navnet står med stort (eller i versaler) i nyhedskorpusset (20 mio. ord).
- `efternavne_da.txt`: `navn <TAB> rang` (de 5000 mest frekvente).
- Bygges med `python scripts/build_names.py` (kun standardbibliotek; henter ca. 400 MB første gang, `--cache MAPPE` genbruger filerne). Samme
  kilder giver samme filer; datoen i filens hoved viser, hvornår den blev bygget.

### Den håndskrevne liste er bevaret
De ca. 400 fornavne fra 0.1.0 (`names_da.LEGACY_FIRST_NAMES`) er altid med og er undtaget fra ordfiltret (de er gennemgået).

## Navne, der også er almindelige ord

Uden filter ville listen ødelægge almindelig tekst ("bo", "per", "hans", "maj", "sten", "tage", "marts" som "mart"+s). To lag:

1. **Automatisk ordfilter** (`build_names.py --max-lower 20`): et navn fjernes, hvis det står **med småt** mindst 20 gange i de to Leipzig-korpusser
   (ca. 40 mio. ord), eller hvis navnet + "s" gør det (så "mart" falder, fordi "marts" er en måned, og "jere" falder pga. "jeres"). De 1000 mest
   frekvente navne har en dobbelt så høj grænse (`--rank-factor 2`), så "ebbe" og "frede" ikke går tabt. Navne bruges næsten altid med stort, så en navnekandidat
   med mange småt-forekomster er et ord. Resultat: 926 navne fjernet (fx kaj, tage, sten, lykke, anker, storm, vilde, sejr, bror, find, tone, ben, ville).
2. **Manuel undtagelsesliste** (`names_da.AMBIGUOUS`, nu 53 ord): den gamle liste (bo, per, hans, rune, august, bent, mark, sol, tom, maj, liv ...)
   plus ord fra målingerne nedenfor (aske, chili, ravn, silke, birk, flora, ane, rosa, karry ...). Den gælder altid, også for klientens `min_count`.
   Og en lille `RESTORE`-liste i bygge-scriptet bringer meget almindelige navne tilbage, som kun ligner udenlandske ord eller forkortelser (mia, ebbe, frede).

Motoren springer desuden over `lexicon.STARTERS`/`ALWAYS_OK`/ugedage/måneder, springer navne over efter et tal ("5 mia. kr."), og lader forkortelser i
versaler på højst 4 bogstaver være (kun medmindre de står blandt de mest almindelige navne). Navne på under 3 bogstaver (Bo, Ib, Jo) er slet ikke med.

**Ærlig begrænsning:** ordfiltret kender nyheder og Wikipedia, ikke børnehaveprosa. En stikprøve på ca. 193 hverdagsord fra børnehave og skole (madpakke,
bleer, regntøj, fødselsdag ...) gav kun "drue" og "rosa" som kollisioner (nu i undtagelseslisten). Ord, der kun bruges i en bestemt klients tekster,
fanges ikke; dem tilføjer klienten som `allowed` (se DESIGN.md).

## Tærsklen `min_count`

```python
Pseudonymizer(store, min_count=0)        # standard: alle registrerede navne (ca. 132.800)
Pseudonymizer(store, min_count=5)        # kun navne med mindst 5 forekomster i korpusset + de 1000 mest frekvente (ca. 5.000)
Pseudonymizer(store, surname_rank=1000)  # tag også de 1000 mest frekvente efternavne med (standard: 0 = fra)
```

Et navn er med, hvis det er blandt de 1000 mest frekvente hos Danmarks Statistik **eller** har mindst `min_count` forekomster med stort i
nyhedskorpusset (eller står i den gamle håndskrevne liste). `0` giver alle registrerede navne. Da Danmarks Statistik ikke udgiver antal bærere, er
"forekomster" en **stedfortræder for, hvor almindeligt navnet er**: det rammer skævt for navne, der også er efternavne eller kendte udlændinge, og det
siger intet om rigtige antal bærere. Tærsklen sættes pr. instans, altså pr. klient.

Efternavne er fra som standard: de er ofte ord eller stednavne (lund, holm, møller, dahl), også efter filtret, og de dukker sjældent op alene med småt.
Slå dem til, hvor en fejl er dyr.

## Ydeevne

Opslaget er et sæt på hele ord (ikke en regex med titusinder af alternativer): ét gennemløb af teksten med en lille regex, og et opslag pr. ord.
Målt på en almindelig Windows-pc (Python 3.14, én kerne), 20. oktober 2026:

| | |
|---|---|
| Indlæsning af 132.800 navne (første kald, ca. 1,6 MB tekst) | ca. 250 ms (ca. 175 ms for `min_count>=1`); delt mellem alle instanser i processen |
| Hukommelse til sættet | ca. 15,5 MB ved `min_count=0`; 1 MB ved 1; 0,5 MB ved 5 |
| Tid pr. tekst (ca. 2.700 tegn, `strict=1`, hele `clean()`) | 3,4 ms med listen, 2,6 ms uden: **listen koster ca. 0,8 ms pr. tekst**, uanset tærskel |
| Tid pr. tekst (ca. 1.300 tegn, kun `strict=0`) | gns. 1,2 ms, 95. percentil 1,7 ms |

Målt med `scripts/bench_names.py` på 400 tekster sat sammen af Leipzig-sætninger (nyheder og Wikipedia, ikke Aula-tekster). Til sammenligning går
Presidio/spaCy (`md`) på ca. 3 ms og 340 MB (PRESIDIO.md). På en hjemmeserver med 6 kerner og 16 GB er listen derfor ubetydelig.

## Målinger ved flere tærskler

Korpusset (`corpus/da_synthetic.json`) er udvidet fra 77 til 207 tekster med `scripts/extend_corpus_names.py`:

- **Lagdelte stikprøver** (fast frø, ikke håndplukket): 8 fornavne pr. lag, hver både med småt midt i en sætning og med stort først i en sætning.
  Lagene er navnets forekomster i nyhedskorpusset: blandt de 1000 mest frekvente (men ikke i den gamle liste), mindst 100, 20-99, 5-19, 1-4 og 0.
- 8 **opdigtede navne**, der ikke står i statistikken ("valtyra", "zelmira" ...).
- **Svære tilfælde:** dobbeltnavne (småt og stort), genitiv med og uden apostrof, initial, versaler, sjældne navne først i en sætning, og 10 hverdagstekster med
  ord, der ligner navne (tage, sten, lykke, kaj, storm, saga, maj, rosa, "5 mia. kr." ...).

**Recall (navne fjernet):**

| Tærskel (`min_count`) | 0 | 1 | 5 | 20 | 100 | kun top 1000 |
|---|---|---|---|---|---|---|
| Stikprøve: blandt de 1000 mest frekvente (ikke i den gamle liste) | 16 af 16 | 16 af 16 | 16 af 16 | 16 af 16 | 16 af 16 | 16 af 16 |
| Stikprøve: mindst 100 forekomster | 16 af 16 | 16 af 16 | 16 af 16 | 16 af 16 | 16 af 16 | 0 af 16 |
| Stikprøve: 20-99 forekomster | 16 af 16 | 16 af 16 | 16 af 16 | 16 af 16 | 0 af 16 | 0 af 16 |
| Stikprøve: 5-19 forekomster | 16 af 16 | 16 af 16 | 16 af 16 | 2 af 16 | 2 af 16 | 2 af 16 |
| Stikprøve: 1-4 forekomster | 16 af 16 | 16 af 16 | 0 af 16 | 0 af 16 | 0 af 16 | 0 af 16 |
| Stikprøve: registreret, men 0 forekomster | 16 af 16 | 0 af 16 | 0 af 16 | 0 af 16 | 0 af 16 | 0 af 16 |
| **Opdigtede navne, ikke på listen** | **0 af 16** | 0 af 16 | 0 af 16 | 0 af 16 | 0 af 16 | 0 af 16 |
| Håndskrevne svære tilfælde (dobbelt, genitiv, initial, versaler, sjældne) | 32 af 32 | 30 af 32 | 29 af 32 | 28 af 32 | 28 af 32 | 28 af 32 |
| Nyttige ord ødelagt i korpusset (3 af 126 ved alle tærskler, uændret fra 0.1.0) | 3 | 3 | 3 | 3 | 3 | 3 |

Før (0.1.0, ca. 400 navne): sjældne navne med småt **0 af 10**. Nu: 100 % i alle lag, når tærsklen er 0.

**Læs tabellen med forbehold.** Stikprøverne er trukket fra selve listen, så "16 af 16" i et lag, der er med, er næsten en tautologi: tabellen viser, *hvilke
lag en tærskel dækker*, ikke hvor stor en andel af Aulas navne der er i hvert lag. Det kræver en mærket prøve fra klientens egne data (lokalt).
Det egentlige hul er nederst: **navne, der ikke står på listen, fanges stadig ikke** (0 af 16) — fx navne med under 3 bærere, nyopfundne stavemåder og
stavefejl i sjældne navne. De 3 ødelagte ord i korpusset er "Bakkehuset", "Kantinen" og "Sankt Hans", som den strenge maskering tager (ikke listen).

**Overmaskering på tekst, vi ikke selv har skrevet.** Andelen af ord med *småt* begyndelsesbogstav, som listen maskerer, i 200.000 sætninger, der ikke blev
brugt til at bygge listen (Leipzig `dan_news_2020_100K` og `dan_wikipedia_2007_100K`; `scripts/bench_names.py`). Ord med småt er sjældent navne i skrevet dansk,
så hvert fund er næsten altid et ord, der ikke burde være væk (men en del er rigtige navne med småt, fx "phil", "jan", "oscar"):

| `min_count` | Navne i listen | Små ord maskeret pr. 10.000 | Hukommelse | Hyppigste |
|---|---|---|---|---|
| 0 | 132.764 | 5,6 | 15,5 MB | phil, line, jan, sars, mia, maximus, don, palle, aksel |
| 1 | 10.419 | 3,4 | 1,0 MB | phil, line, jan, sars, mia, maximus |
| 5 | 5.040 | 2,2 | 0,5 MB | |
| 20 | 2.812 | 1,4 | 0,3 MB | |
| 100 | 2.078 | 0,9 | 0,2 MB | |
| 0, + 1000 efternavne | 133.405 | 5,7 | 15,6 MB | |
| 0, + 5000 efternavne | 136.439 | 6,0 | 16,0 MB | |

Tallet er med Wikipedia 2007 (skrevet i en anden stil, med mange udenlandske ord) højere end med nyheder alene (ca. 2 pr. 10.000 ved `min_count=0`).
Ordlisten og undtagelseslisten er delvist tunet på netop de hyppigste fund, så tallet er optimistisk for andre tekster. Med 10.000 ord med småt
(ca. 30 sider) maskeres altså 6 forkerte ord ved standarden; i en typisk Aula-besked på 100 ord er det ca. 0,06 ord, dvs. ca. hver 18. besked får ét
ord for meget maskeret, og klientens `allowed`-liste retter det.

## Standard: `min_count=0` (alle registrerede navne)

- Målet er at fange sjældne navne; det er netop de sjældne navne (0 forekomster), som tærsklerne over 0 taber (0 af 16 i det lag). Et lækket navn er
  dyrere end et ord for meget maskeret, og motoren skal fejle lukket.
- Meromkostningen er lille: ca. 0,8 ms pr. tekst uanset tærskel, 15,5 MB og 250 ms ved opstart, og 2-4 ekstra forkerte ord pr. 10.000 mod `min_count=5`.
- Hvor nytten vejer tungere (lange tekster med mange udenlandske ord, tekniske tekster), er `min_count=5` et godt kompromis: stadig 5.000 navne og
  alle navne med mindst 5 forekomster, men ca. 60 % færre falske fund. `min_count=20` svarer til "almindelige navne" og taber de sjældne igen.

Tallene er vejledende: korpusset er skrevet og trukket af os, ikke af uafhængige, og lagene er afledt af listen selv.

## Sådan genskabes og kontrolleres det

```bash
python scripts/build_names.py --cache ~/navne-cache              # bygger data/*.txt
python scripts/extend_corpus_names.py                            # genskaber nl*-tekster i korpusset (fast frø)
PYTHONPATH=src python scripts/eval_thresholds.py                 # recall-tabellen
PYTHONPATH=src python scripts/bench_names.py SÆTNINGER.txt ...   # ydeevne og overmaskering (Leipzig-sætningsfiler, ikke i repoet)
python -m unittest discover tests
```
