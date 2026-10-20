# Design: hvordan en klient bruger motoren

## Rollefordeling

| Motoren (dette repo) | Klienten (fx summer-aula) |
|---|---|
| Rens af CPR, telefon, adresse, links m.m. | Ved hvilke felter i dens datakilde der er navne, og hvem der er hvem |
| Token-lager: samme person, samme token, aldrig genbrug | Fodrer lageret med kendte personer (`store.token(prefix, nøgle, navne)`) |
| Navnegenkendelse (kendte, almindelige fornavne, stavefejl), udløsere, ukendte store ord | Vælger niveauet (`strict` 0, 1 eller 2) pr. tekst |
| Lækagevagt | Beslutter, hvad der sker, når vagten udløses (typisk: tilbehold hele teksten) |
| Emneliste (`find_topics`) | Afgør, hvilke emner der må frigives, og til hvem |
| Evalueringsværktøj og korpus | Egne tests, og sin egen mærkede prøve (lokalt) |

Motoren skriver aldrig noget, klienten ikke har bedt om, og den kender hverken netværk, filsystem (ud over token-lageret) eller en AI.

## Token-lageret

`TokenStore(path)` er en JSON-fil (atomisk skrivning). Den indeholder **rigtige navne**, så den er rådata. Indhold:

- `entries`: token -> præfiks, navne og nøgler. `keys`: nøgle -> token. Nøglen er klientens stabile id (`p:123`), så samme person får samme
  token, også ved stavefejl eller kælenavn. Findes ingen nøgle, matches på fuldt navn.
- `protected`: navne, der aldrig maskeres (egen familie). Beskyttede navne indgår hverken i navnegenkendelsen eller i vagten.
- `meta`: fri plads til klientens egen tilstand (fx egne profil-id'er).
- Et token genbruges aldrig. En ødelagt fil eller en forkert version stopper programmet (fejl lukker).

Præfikser er bogstaver (`Barn`, `Forælder`, `Pædagog`, `Lærer`, `Ansat`, `Person` er standard). `Person-?` og `Barn-?` betyder "ukendt eller
flertydig". Præfikser, der kan bruges om samme person (en ansat, der først ses som `Ansat` og senere som `Pædagog`), grupperes i `groups`.

## Niveauer for streng maskering

- `strict=0`: kun rens, kendte navne, stavefejl og udløsere.
- `strict=1` (standard): også ukendte store ord midt i en sætning (næsten altid navne eller steder).
- `strict=2`: også først i en sætning, medmindre ordet er et almindeligt dansk åbningsord (`lexicon.STARTERS`). Overmaskerer mere; bruges, hvor
  en fejl er dyr (fx en tekst om helbred, der kan nævne andres børn).

`allowed=` er klientens liste over ord, der ikke er navne (steder, institutioner, stuer). Den vokser typisk af brugerens egen "tillad"-knap.

## Lag (NER/Presidio)

Et lag er et objekt med `name` og `find_spans(text) -> [(start, slut, mærke)]`. Motoren erstatter spændene med `Person-?`, men springer
tokens, pladsholdere og beskyttede navne over. `PresidioLayer` er et sådant lag. Egne lag (en lokal sprogmodel, DaCy) kan tilføjes på samme måde.

## Sporing

`pseudonymizer.trace = []` før et kald giver bagefter en liste `(token, original, lag)` over alt, der blev maskeret, og hvorfor. En lokal
visning kan bruge den til at lade brugeren se og rette (flag og tillad). Sæt den aldrig på en server, der logger.

## Lækagevagten

`Pseudonymizer.leaks(text)` bør også køres på hele svaret, lige før det forlader klienten (ikke kun på de enkelte tekster). Den finder
tilbageværende identifikatorer, kendte navne, `udløser + stort ord` og flaggede ord. En klient bør hellere tilbageholde for meget end for lidt.

## Hvad motoren ikke kan

- Identificerende omskrivninger ("drengen med nøddeallergien i 2.B") kan ingen mekanisk metode udelukke; emnelisten og klientens regler dækker dem.
- **Sjældne, ukendte navne med småt** fanges hverken af kernen eller af Presidio (se PRESIDIO.md). Kendte navne og almindelige fornavne fanges
  uanset store/små bogstaver. Resten dækkes af klientens flagning, strengere regler og emnelisten.
- Ukendte navne først i en sætning fanges af navnelisten, NER-laget eller niveau 2.
- Billeder, lyd og filer behandles ikke. Klienten skal selv udelukke dem.
