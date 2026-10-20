"""Almindelige danske fornavne (små bogstaver). Bruges som et billigt net for ukendte navne, også når de er skrevet med småt eller
står først i en sætning. Listen er skrevet efter hukommelsen af udbredte navne og er hverken fuldstændig eller en kilde til noget som helst:
den er et heuristisk net. Navne, der også er almindelige danske ord, er med vilje udeladt (se AMBIGUOUS).
"""

FEMALE = """
emma ida freja ella alma sofia sophia clara klara karla olivia agnes lærke mathilde josefine josephine laura marie anna sara sarah
nanna cecilie caroline johanne frida rosa vera naja emilie amalie ellen signe astrid alberte filippa liva selma luna nora anne
mette lene susanne camilla charlotte louise maria pernille katrine line helle tina hanne dorte lone karen birgit gitte pia trine
rikke malene mie stine julie kirsten inge lisbeth jette annette anita bente marianne ingeborg mille sofie tine christina kathrine
kristine maja gry ditte nete randi lis birte hanna henriette ulla vibeke lotte lisa linda mona sanne bodil ingrid grete grethe
helene else eva eve winnie yvonne jytte berit berit connie conny tanja tania sabrina natasja natascha nicoline nicole rebekka
stephanie sidsel sine sofia thea theresa trine tove ulrikke vivi vita zara maiken marlene malou louisa liv lea lina lisbet
lise lærke mai mathea merete mikkeline mira nikoline oda pernille ragnhild rigmor ronja rosa sabina simone sonja stella
tilde viola viktoria victoria wilma yasmin ylva
""".split()

MALE = """
william noah oscar oliver lucas lukas carl viktor victor alfred malthe emil valdemar frederik magnus elias mikkel mads rasmus
jesper anders peter henrik thomas michael martin lars søren jens morten kasper jakob jacob christian daniel simon tobias
nikolaj jonas mathias andreas casper kristian niels ole jørgen johan johannes jonathan jeppe jacob benjamin sebastian
alexander aksel axel anton aske aslak asger bastian bjarke bertil brian carsten claus dennis dan flemming frank frands
gustav gunnar hans-jørgen henning holger ib ivan jan jesper joachim john jørn karl kenneth kevin kim klaus knud kurt
lasse leif lennart lorenz marcus marius mark mathis max morten nick nicklas nicolai nikolai olav otto palle patrick
paul poul preben rene rené rolf rune rasmus sam samuel sigurd steen stefan steffen svend tim thor thorvald tommy
troels uffe ulrik valdemar vagn verner vilhelm villads vincent walter wilhelm åge aage
alfred august bo
""".split()

# Navne, der også er almindelige danske ord, og som derfor ikke må bruges som net (ellers ødelægges almindelig tekst).
# De findes stadig som kendte navne, hvis klienten kender personen.
AMBIGUOUS = frozenset("bo per hans rune august bent dan mark rose sol tom maj ask bjørn liv rene".split())

COMMON_FIRST_NAMES = frozenset(n for n in set(FEMALE) | set(MALE) if len(n) >= 3 and n not in AMBIGUOUS and "-" not in n)
