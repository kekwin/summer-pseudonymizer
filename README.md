# summer-pseudonymizer

Dansk pseudonymisering af tekst, så den kan vises for en AI (eller en anden tredjepart) uden at andre mennesker kan genkendes.
Navne bliver til faste tokens (`Barn-4`, `Pædagog-1`), og CPR, telefon, e-mail, adresser og links fjernes. Hver tekst kontrolleres til
sidst af en **lækagevagt**, der tilbageholder hele teksten, hvis noget af det, der skulle være væk, stadig står der. Fejl lukker.

Kernen har **ingen afhængigheder** (kun Python 3.11+). [Presidio](https://microsoft.github.io/presidio/) og spaCy er et valgfrit ekstra lag.
Motoren kender ikke noget om bestemte tjenester: en *klient* fortæller, hvem der er hvem (fra strukturerede felter), og hvilke navne
der skal bevares. Første klient er [summer-aula](https://github.com/kekwin/summer-aula).

> **Offentligt repo, ingen hemmeligheder.** Her ligger kun kode, danske ordlister og et syntetisk korpus med opdigtede navne. Rigtige data,
> token-lagre (de indeholder rigtige navne) og modeller trænet på rigtige data hører aldrig hjemme her; en test (`tests/test_no_secrets.py`)
> holder øje med det.
>
> **Licens:** [MIT](LICENSE). **Ingen garanti:** anonymisering bliver aldrig 100 %. Værktøjet nedbringer risikoen, men kan overse navne og
> identificerende omskrivninger; brug det ikke som eneste beskyttelse af følsomme data.

## Eksempel

```python
from pseudonymizer import Pseudonymizer, TokenStore

store = TokenStore("store.json")                      # filen indeholder rigtige navne: aldrig i git
store.add_protected(["Mikkel", "Noah"])                # navne, der bevares (egen familie)
store.token("Forælder", "p:123", ["Pernille Lindholm"])   # kendt fra et struktureret felt
store.token("Barn", "c:emma|rævene", ["Emma"])

p = Pseudonymizer(store)
c = p.clean("Hej Mikkel. Pernilles mor ringede på 12 34 56 78 om Emma L. og mormor Birgit.")
print(c.text)   # Hej Mikkel. Forælder-1's mor ringede på [TELEFON] om Barn-1 og mormor Person-?.
print(c.ok)     # True: vagten fandt intet tilbage
```

## Lagene (rækkefølge)

1. **Rens:** CPR, telefon, e-mail, links, @-håndtag, adresser, postnumre, kontonumre og lange tal -> `[CPR]`, `[TELEFON]`, ... Datoer og
   klokkeslæt bevares. HTML -> tekst, Unicode-normalisering, usynlige tegn fjernes.
2. **Kendte navne** fra token-lageret: hele navne, fornavne, efternavne, bindestregsnavne, dansk genitiv (`Emmas`), initial (`Emma L.`),
   **uanset store og små bogstaver**, kun hele ord. Flertydigt (to børn hedder Emma) giver `Barn-?`, aldrig et gæt.
3. **Stavefejl:** et stort ord, der kun er én tastefejl fra et kendt navn, maskeres som navnet.
4. **Udløsere:** "mormor Birgit", "onkel Jens", "vikar Karen" -> navnet maskeres.
5. **Flaggede ord** (klientens egen liste).
6. **Valgfrie lag** (Presidio/NER): ukendte personnavne.
7. **Danske fornavne** (indbygget liste på ca. 133.000 navne fra Danmarks Statistik, også med småt og først i en sætning): "ring til oline" -> `Person-?`.
   Slås op i et sæt på hele ord (genitiv, apostrof, initial, dobbeltnavne); navne, der også er almindelige ord ("bo", "per", "hans", "maj"), er filtreret
   fra. Hvor sjældne navne der er med, styres af `Pseudonymizer(..., min_count=N)` (standard 0 = alle; 5 = kun de mere almindelige), og `surname_rank=N`
   tager de N mest frekvente efternavne med. Se [docs/NAVNELISTE.md](docs/NAVNELISTE.md) for kilder, licens (CC BY 4.0) og målinger.
8. **Streng maskering** (valgfri): danske navneord skrives med småt, så et stort ord midt i en sætning er næsten altid et navn eller sted
   og maskeres, medmindre klienten har tilladt det. Niveau 2 tager også ord først i en sætning.
9. **Lækagevagt:** står noget tilbage, tilbageholdes hele teksten.

Dertil `find_topics()`: brede ordlister for følsomme emner (sygdom, medicin, adfærd, familie, økonomi). Klienten afgør, hvad der må frigives.

## Evaluering

```bash
python -m pseudonymizer corpus/da_synthetic.json            # kerne
python -m pseudonymizer corpus/da_synthetic.json --presidio # med Presidio (kræver [presidio] og en dansk spaCy-model)
```

Korpusset (`corpus/da_synthetic.json`, 207 opdigtede tekster) måler recall pr. type og **overmaskering** (nyttig tekst, der blev ødelagt).
Tallene er vejledende (lille, syntetisk korpus), men testene bruger dem som regressionsport, så motoren ikke bliver dårligere.
Se [docs/NAVNELISTE.md](docs/NAVNELISTE.md) for målinger pr. tærskel og [docs/PRESIDIO.md](docs/PRESIDIO.md) for Presidio. **Kendt svaghed: navne, der ikke står på
listen** (under 3 bærere, nye stavemåder, stavefejl i sjældne navne).

## Kør testene

```bash
python -m unittest discover tests
```

## Videre

[docs/DESIGN.md](docs/DESIGN.md) (hvordan en klient bruger motoren) · [docs/NAVNELISTE.md](docs/NAVNELISTE.md) · [docs/PRESIDIO.md](docs/PRESIDIO.md) · [docs/ROADMAP.md](docs/ROADMAP.md)
(inkl. træning på en stationær maskine, og hvad der aldrig må ligge i dette repo).
