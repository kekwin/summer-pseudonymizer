"""Almindelige danske ord, der kan stå med stort i begyndelsen af en sætning uden at være et navn.

Bruges kun af den strenge navnemaskering (mask_unknown_caps) i tråde med følsomt indhold. Står et stort ord, der ikke
er her, midt i en sætning (eller først og ukendt), regnes det for et muligt navn og maskeres. Danske navneord skrives
med småt, så store bogstaver midt i en sætning er næsten altid navne, steder eller institutioner.
"""

WEEKDAYS_MONTHS = frozenset("""mandag tirsdag onsdag torsdag fredag lørdag søndag januar februar marts april maj juni juli
august september oktober november december""".split())

STARTERS = frozenset("""
hej hejsa kære tak mange det der de dem den denne dette disse dig du er en et ej efter før fra for forhåbentlig godt god
glad glæder ja jeg i ikke ingen intet hun han hendes hans her hvis hvad hvor hvornår hvem hvorfor hvordan hvert hver
ligesom lige lidt men mit min mine må mvh med nej nu når og om på pga samt se sig skal som så til ud uden under vi vil
ved vores var ville vær vh venlig venlige hilsen hilsner rigtig super selvfølgelig desværre altså alle alt andet andre
bare bedring behøver bliver blev burde da dag dagen dejligt derfor derfra dog endnu enten fordi forældre forældrene gerne
hold husk igen imorgen imorges igår idag jo kan kommer kom kunne lad læs nogle noget også okay ok op over passer sidste
selv slet snart stadig sådan tage tilbage tillykke tusind uge uh vigtigt virker værsgo lægen lægerne pædagogerne børnene
børn barnet personalet stuen huset vuggestuen børnehaven skolen klassen madpakke regntøj skiftetøj obs info påmindelse
reminder knus kram glædelig godmorgen godaften godnat hende ham hos mens mod nogen omkring siden sammen stor store små
dejlig dejlige fint fine flot flotte fælles først efterfølgende gør gøre gik gå går hav have havde helt hvilke hvilken
jeres jer ja kl klokken lørdag mere mest mindre måske næste nok nye ny nyt oplever ring send skriv spørg sig tager
tænker tænk udover vedlagt vælg vær venter viser vores mormor morfar farmor farfar bedstemor bedstefar oldemor oldefar onkel tante søster
bror veninde ven kammerat klassekammerat vikar nabo dagplejer mor far fru hr

kæmpe stort store lille små gode godt dårlig dårligt bedre bedst værre værst hurtig hurtigt langsomt sent tidligt
tidlig aldrig altid ofte sjældent nogensinde allerede stadigvæk faktisk egentlig bestemt sikkert nok måske
muligvis helt næsten ganske temmelig meget mere mindre lidt rigtigt forkert korrekt ellers ellers ligeledes
ligeså desuden derudover dermed derfor altså hvorfor derefter bagefter først siden imens medens mens indtil
inden efter før ovenpå nedenunder indenfor udenfor ude inde hjemme hjem ned op ind ud frem tilbage rundt
vedrørende angående ifølge på grund trods selvom uanset medmindre såfremt såfremt desværre heldigvis
forhåbentlig selvfølgelig naturligvis helt klart tak mange tak tusind tak mange hilsner kærlig kærlige
venlig venlige hilsen hilsner knus kram vh mvh bh hh
hun han de vi jeg du i den det der dem os jer hende ham sig mig dig vores jeres deres hendes hans dens dets min mit mine
din dit dine sin sit sine ens nogen noget nogle ingen intet ingenting alle alt alting hver hvert enhver hvilken hvilket
hvilke hvem hvad hvor hvordan hvornår hvorfor
er var har havde bliver blev kan kunne skal skulle vil ville må måtte bør burde gør gjorde får fik går gik kommer kom
tager tog giver gav ser så siger sagde ved vidste tror troede synes syntes mener mente tænker tænkte
ligger lå står stod sidder sad hører hørte kender kendte
barnet børnene børn drengen drengene pigen pigerne baby babyen mor far mormor morfar farmor farfar
stuen stue huset vuggestuen børnehaven skolen klassen sfo fritids fritidshjemmet institutionen
dag dagen morgen morgenen aften aftenen nat natten uge ugen weekend weekenden måned måneden år året
mandag tirsdag onsdag torsdag fredag lørdag søndag
madpakke madplan frokost morgenmad aftensmad middag snack mælk vand frugt
tur turen udflugt arrangement fest festen møde mødet samtale samtalen
lægen doktor sygeplejerske sundhedsplejersken medicin feber syg syge sygdom
bedring god bedring rigtig god bedring
tillykke velkommen farvel hej hejsa goddag godmorgen godaften godnat
også både enten hverken eller men og for så
""".split())

# Ord, der må stå med stort midt i en sætning uden at blive maskeret
ALWAYS_OK = frozenset("""aula danmark facebook messenger google youtube instagram pædagog lærer forældre forældrene børnene
matematik dansk engelsk idræt historie kristendom natur teknologi biologi fysik kemi geografi samfundsfag musik billedkunst
håndværk madkundskab tysk fransk svømning sløjd hjemkundskab understøttende undervisning fællessamling
tivoli legoland bakken københavn aarhus århus odense aalborg esbjerg roskilde jylland fyn sjælland bornholm europa sverige
norge tyskland england island grønland færøerne kastrup amager frederiksberg nordsjælland dsb mitid nemid mobilepay""".split())
