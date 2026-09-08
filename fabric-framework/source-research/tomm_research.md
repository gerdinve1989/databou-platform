# Tommy Booking Support — bronresearch (`tomm`)

> **Stand van zaken 08-09-2026: de leverancier heeft nog geen enkel bericht aangeleverd.**
> Bronze is intussen niet leeg — er staat materiaal in de ontvangstmap, maar dat hebben wij er
> zelf neergezet om te kunnen testen. Zie *Wat er in Bronze staat*. Dit rapport legt vast wat er
> vaststaat over de ontsluiting — het brontype, de route, het adrespatroon en de
> toegangsvoorwaarden — en laat alles wat de inhoud betreft expliciet open. Er is bewust géén
> schema opgesteld: dat kan pas op een echt bericht van de leverancier, nooit op een beschrijving
> en ook niet op materiaal dat wijzelf hebben geplaatst.

> **Twee namen in dit rapport zijn van ons en niet van de leverancier.** `tbs` als
> vestigingsaanduiding en `booking` als naam van de berichtsoort zijn door ons gekozen. Tommy
> Booking Support heeft geen van beide bevestigd — niet de namen, en niet dat er een berichtsoort
> bestaat die hiermee overeenkomt. Ze staan overal in dit rapport gemarkeerd; lees ze nergens als
> afspraak.

## TypeSource

- **Vastgesteld:** `push`
- **Door intake afgeleid:** bestandsbron; gecorrigeerd naar `push`, wat in dit framework de
  vorm is waarin een bestandslevering van een leverancier binnenkomt.

`push` betekent hier precies wat `01_source_config.template.md` erover zegt: de data wordt bij
ons neergezet in plaats van opgehaald, een stap stroomopwaarts (een Logic App, een Data
Factory-pijplijn, een webhook of de leverancier zelf) schrijft hem in OneLake, en het framework
draait geen Bronze-ingestie. `SourceDetails` is `None`.

**Twee gevolgen voor de keten, en ze zijn allebei structureel:**

| Gevolg | Waar het uit blijkt |
|---|---|
| Er bestaat **geen sectie 2** (`entity_ingestion_config`) voor dit brontype | `01_source_config.template.md` → *TypeSource*; `notebook_Functions_General.py` regel 453 |
| Het ingestienotebook slaat de bron over in plaats van hem op te halen | `notebook_Ingestion_Generic_Parent.py` regel 116-119; `notebook_Ingestion_Generic_Api.py` regel 105 |

De normale researchoplevering is sectie 1 plus sectie 2. Hier vervalt de tweede helft: wat
overblijft is sectie 1, en het adres waarop de levering wordt verwacht.

## Overzicht

Tommy Booking Support is een Nederlands boekings- en reserveringssysteem voor recreatiebedrijven
(campings, vakantieparken, jachthavens). Wat er wordt aangeleverd zijn **boekingsberichten**.

De richting ligt vast en is de kern van dit dossier: **de leverancier levert, wij halen niets
op.** Er wordt dus niet tegen een API van de leverancier aangeklopt; er wordt een plek
aangewezen waar hij mag neerzetten.

Wat er inhoudelijk in een bericht zit — velden, sleutel, granulariteit, of één bericht één
boeking is of een set — is `UNKNOWN — needs confirmation`.

## Wat er in Bronze staat — en waar het vandaan komt

**Dit is de sectie die de rest van het rapport in perspectief zet.** Wie de ontvangstmap opent,
ziet bestanden staan en zou daaruit kunnen afleiden dat de koppeling loopt. Dat is niet zo.

| Meting | Waarde |
|---|---|
| Locatie | de ontvangstmap `{Bronze Files}/tomm/tbs/booking/incoming/` op de DEV-werkruimte |
| Aantal bestanden | 231 |
| Totale omvang | 987,1 KB |
| Laatste bestand | 08-09-2026, 19:28 |
| Gemeten met | `bronze_inspect.py --list-only`, op 08-09-2026 |

**Niets daarvan komt van de leverancier.** De gebruiker heeft het materiaal zelf aangeleverd en
het is met `bronze_stage.py --action land` in de ontvangstmap gezet — de handeling die het script
beschrijft als "bestanden neerzetten zoals een leverancier dat zou doen, zodat er iets te testen
valt vóórdat de koppeling leeft". Die actie werkt uitsluitend op DEV, precies om de reden die hier
speelt: met de hand geland materiaal is later niet meer te onderscheiden van een echte levering.

**Het zijn de originelen, niet geanonimiseerd.** Dat is een bewuste keuze van de gebruiker: Bronze
hoort de echte levering te houden, en een geanonimiseerde variant in Bronze zou een levering tonen
die zo nooit is binnengekomen. Het gevolg staat onder *Risico's* → *Persoonsgegevens*: het gaat om
echte boekingsdata met echte persoonsgegevens, en iedereen die deze map inspecteert werkt met
persoonsgegevens.

**Wat deze bestanden wel en niet bewijzen:**

| Wel | Niet |
|---|---|
| Dat het adrespatroon werkt: de map bestaat, er kan in geschreven worden, en de listing leest terug | Dat de leverancier daar kán schrijven — het schrijfrecht is nog niet toegekend en de identiteitsvorm is nog niet gekozen |
| Dat er materiaal is om de verwerking naar Silver op te beproeven | Dat de vorm van dat materiaal de vorm is die de leverancier straks stuurt |
| Dat de mapnaam `booking` technisch bruikbaar is | Dat `booking` een berichtsoort van de leverancier is, of dat hij die zo noemt |

Formaat, sleutel, watermerk, volume en leveringspatroon blijven daarom `UNKNOWN — needs
confirmation`. Ze zijn af te lezen aan het gelande materiaal, maar dat materiaal is van ons, en
een eigenschap ervan is geen eigenschap van de bron.

> **Over de betrouwbaarheid van deze meting.** `bronze_inspect.py` is op 08-09-2026 gerepareerd:
> op een Bronze-lakehouse gaf de listing de héle lakehouse terug in plaats van de opgevraagde
> bron, waardoor een inventarisatie van de ene bron de bestanden van de andere meetelde — met een
> totaal dat er kloppend uitzag. Metingen met dat script van vóór die reparatie zijn op dit punt
> onbruikbaar. De meting hierboven is erna gedaan.

## Leveringstype en route

### Leveringstype

Bestanden, in een map die wij aanwijzen. De leverancier schrijft zelf; er staat geen ophaalstap
tussen.

### Route: inlezen (Bronze → Silver)

**Stap 1 van de skill is expliciet beantwoord, ook al is de uitkomst de gewone.** De drie routes
sluiten elkaar per entity uit, en twee vallen af:

| Route | Oordeel | Waarom |
|---|---|---|
| **Mirror** | valt af | Bij een bestandslevering komt een mirror alleen in beeld voor een SharePoint-lijst. Hier is het geen lijst |
| **Shortcut** | valt af | Een shortcut verschijnt rechtstreeks als Silver-tabel: geen sleutelcontrole, geen dedup, geen SCD, geen versheidsbewaking. Een leveranciersexport haalt de lat van "geconformeerd" per definitie niet — die is voorbehouden aan de Silver- of Gold-output van een ander item op dit framework. Bij twijfel lees je in, en hier is de twijfel niet eens klein: de vorm van de levering ligt nog niet vast |
| **Inlezen** | **gekozen** | Er moet iets met de data gebeuren voordat hij bruikbaar is (typen, ontdubbelen, historie, versheidsbewaking), en de vorm ligt niet vast. Dat is de definitie van inlezen |

Dat inlezen begint bij `incoming/` en niet bij een ingestienotebook: de bron is `push`, dus de
eerste stap die het framework zelf draait, is de verwerking naar Silver.

### Waar de levering landt

De levering gaat **rechtstreeks in het Bronze-lakehouse van de klant op OneLake**. Er is geen
tweede opslagplek: bij een klant met `bronze_storage.target = lakehouse` bestaat er geen
opslagaccount waar een bestand eerst zou kunnen landen.

Twee alternatieven zijn overwogen en afgevallen; ze staan hier omdat ze terugkomen zodra de
leverancier niet kan wat hierboven wordt verondersteld:

| Alternatief | Wat het kost |
|---|---|
| **Een aparte brievenbus** (opslagaccount of documentbibliotheek van de klant), waar wij het uit ophalen | De brievenbus bestaat niet vanzelf, en het transport van brievenbus naar Bronze zit **niet** in dit framework: de drie framework-pijplijnen zijn API/SOAP-ingestie, SQL-ingestie en de Silver/Gold-keten. Er is geen generieke bestandskopie. Het wordt dus een los te bouwen en te onderhouden onderdeel |
| **Een ontvangstpunt dat berichten aanneemt** (een webadres in plaats van een map) | Vereist een ontvanger die elk bericht als bestand wegschrijft. Die bestaat vandaag niet in dit platform. Zie *Risico's* — de publieke documentatie van de leverancier wijst juist die kant op |

## Het ontvangstadres

### De padvorm ligt vast in het framework

```
{Bronze Files}/{source}/{environment}/{entity}/incoming/
```

Dat is geen conventie maar code: `move_files_to_processing` bouwt exact dit pad
(`notebook_Functions_Silver.py`, regel 119-121) en `resolve_bronze_target` bevestigt dezelfde
wortel voor de scriptkant (`scripts/lib/bronze_target.py`).

### Het gekozen adrespatroon

```
{Bronze Files}/tomm/tbs/{berichtsoort}/incoming/
```

- `tomm` — de bron. Ligt vast.
- `tbs` — de vestigingsaanduiding. **Door ons gekozen, niet bevestigd door de leverancier.** Eén
  vaste waarde: er wordt niet per park of locatie gescheiden. Wie meerdere vestigingen heeft,
  herkent ze straks aan een veld in de data en niet aan een map.
- `{berichtsoort}` — **één map per soort bericht.** Dít is de scheiding die is gekozen. Het
  patroon is van ons; welke soorten er zijn, is aan de leverancier.
- `incoming` — van het framework. Ligt vast.

**Welke berichtsoorten er zijn, is `UNKNOWN — needs confirmation`.** Het patroon staat vast, de
lijst niet. Het is de leverancier die bepaalt welke soorten hij stuurt en of hij ze gescheiden
aanlevert; vraag 4 hieronder stelt die vraag en is onbeantwoord.

### `booking` is een werknaam van ons

**Er bestaat inmiddels één map onder dit patroon, en die heet `booking`.** Die naam is door ons
gekozen om het gelande testmateriaal ergens neer te kunnen zetten — zie *Wat er in Bronze staat*.
Wat er niet achter zit:

| Wat het níet is | Toelichting |
|---|---|
| Een door de leverancier bevestigde berichtsoort | Tommy heeft niet gezegd dat hij zoiets stuurt, en al helemaal niet dat hij het zo noemt |
| Een adres dat aan de leverancier is doorgegeven | Er is nog niets doorgegeven; het schrijfrecht bestaat ook nog niet |
| Een vertaling van een bekende leveranciersterm | Er is geen leveranciersterm om uit te vertalen — vraag 4 is onbeantwoord |

**Waarom dit met zoveel nadruk staat.** Een mapnaam die eenmaal in een listing staat, leest na een
paar weken als een afspraak: hij is concreet, hij bestaat, en er staan bestanden in. Het verschil
tussen "wij hebben deze map gemaakt" en "hier levert de leverancier op" is dan niet meer aan de
data af te lezen. Zolang vraag 4 openstaat, is `booking` een werknaam en niets meer.

### Hoe een soort aan zijn mapnaam komt

**De mapnaam wordt genormaliseerd naar de naamgevingsconventie van de klant** — Engels,
enkelvoud, kleine letters — in plaats van de benaming van de leverancier letterlijk over te
nemen. Dat houdt de mapstructuur in lijn met de Silver-tabellen die er straks uit volgen, en
voorkomt dat het jargon van een leverancier de indeling bepaalt.

**Het nadeel hoort erbij en verdwijnt niet door de keuze:** bij elk adres dat wordt doorgegeven
moet erbij staan wélke soort van de leverancier het is, anders stelt hij de verkeerde map in. En
een vertaalfout landt in een adres dat al is doorgegeven — terugdraaien betekent dan een tweede
ronde langs de leverancier.

Daarom blijft de vraag hoe de leverancier zijn soorten zélf noemt onverminderd nodig: niet meer
om over te nemen, maar om te kunnen vertalen en om elk adres aan de juiste soort te kunnen
koppelen. `booking` is niet het resultaat van die vertaalslag — er was niets om uit te vertalen.

### Valkuilen bij de mapnaam van een soort

**`all` kan geen mapnaam zijn.** Dat woord is in de parameterverwerking gereserveerd voor "alle
waarden uit de config" (`parse_source_env_entity_parameter`). Een map die zo heet, is later niet
meer los aan te spreken. Het aanmaakcommando hieronder weigert die naam ook.

**Een lege omgevingslijst verwerkt stil niets.** `PossibleEnvironments` moet gevuld zijn; is die
lijst leeg, dan levert de parser een lege omgevingslijst op, wordt er geen enkele
verwerkingsmap gebouwd, en meldt de run niets. Met de keuze hierboven bevat die lijst precies
één waarde, en daarmee is deze valkuil ontweken — maar alleen zolang die waarde er ook echt in
komt te staan.

### De map aanmaken — wat er wel en niet is geregeld

De ontvangstmap wordt aangemaakt met één commando; verzin er geen eigen weg naartoe:

```bash
python scripts/bronze_stage.py --profile {profile} --source {source} \
  --action prepare --env {env} --entity {entity} [--dry-run]
```

Wat het doet, gemeten in `do_prepare`:

| Gedrag | Betekenis voor deze bron |
|---|---|
| Maakt **alleen** `incoming/` aan (met de bovenliggende niveaus) | `processing/` en `archive/` blijven weg tot de verwerking ze zelf schrijft; vooruit aanmaken zou een stap tonen die nooit heeft plaatsgevonden |
| `--env` en `--entity` zijn **verplicht**, worden nooit afgeleid of standaard ingevuld | Ze worden een segment van het adres dat de leverancier instelt; een gok hoort daar niet |
| Weigert `all` als waarde voor beide | De valkuil hierboven is afgevangen op het moment dat de map nog niet bestaat, in plaats van later, wanneer hij al bij een leverancier ligt |
| Leest het pad terug en weigert een adres af te drukken als `incoming` niet in de listing staat | Een geslaagde aanmaakaanroep en een map die er echt staat zijn twee verschillende beweringen — alleen de tweede is een adres waard |
| Drukt het volledige adres af | Dat afgedrukte adres is wat de leverancier krijgt; het hoeft niet met de hand te worden samengesteld |
| Werkt voor beide Bronze-vormen en verandert niets wanneer het pad al bestaat | Herhalen is ongevaarlijk |
| `--dry-run` toont de niveaus en schrijft niets | Te draaien vóór de goedkeuring die bij een schrijfactie hoort |

**Wat het uitdrukkelijk níet doet:** rechten toekennen. Het script zegt het zelf aan het eind van
een geslaagde run — de map aanmaken opent hem voor niemand. Het schrijfrecht op `tomm/tbs/`
blijft beheerwerk waarvoor **geen script bestaat**; zie *Toegang en authenticatie*.

De volgorde is daarmee vastgelegd en niet omkeerbaar: eerst de map, dan het recht. Recht kan
alleen worden toegekend op een map die al bestaat.

### Testmateriaal neerzetten — een andere handeling dan een levering

Naast `prepare` kent hetzelfde script `--action land`: dat zet bestanden uit een lokale map in
`incoming/`, zoals een leverancier zou doen. Dat is de handeling waarmee het huidige materiaal in
Bronze is beland. Drie eigenschappen die er in dit dossier toe doen:

| Eigenschap | Waarom het hier telt |
|---|---|
| **Alleen DEV** | Productie hoort zijn data van de leverancier te krijgen; met de hand geland materiaal is daar later niet van te onderscheiden |
| Alleen naar `incoming/`, nooit naar `processing/` | Het volgt dezelfde weg als een echte levering, dus de verwerking is er eerlijk mee te beproeven |
| Weigert wanneer `incoming/` al gevuld is, tenzij `--yes` | Het framework leest alles wat er staat; twee keer landen levert elke record twee keer op |

**Wat het script niet kan, en dit rapport dus wel moet doen:** vastleggen dat de bestanden er
door ons zijn gezet. Aan het materiaal in Bronze is dat niet te zien.

### Levenscyclus van een bestand

```
incoming/  ->  processing/{tijdstempel}/  ->  archive/{jaar}/{maand}/{tijdstempel}/
```

De verwerking verplaatst zelf uit `incoming/` en telt vóór en na de verplaatsing het aantal
bestanden; wijken die af, dan faalt de run in plaats van stil data te verliezen. Na verwerking
archiveert `archive_processed_files` in-place onder `archive/` (lakehouse) of naar een aparte
archiefcontainer (opslagaccount).

**De leverancier schrijft uitsluitend in `incoming/`.** De twee andere mappen zijn van het
framework; wie daarin schrijft, loopt tegen een lopende verwerking aan.

### Wat vastligt en wat nog open is

| Segment | Status |
|---|---|
| `{Bronze Files}` | ligt vast — volgt uit het klantprofiel |
| `{source}` | ligt vast — `tomm` |
| `{environment}` | **door ons gekozen: `tbs`**, één vaste vestigingsaanduiding. Niet bevestigd door de leverancier |
| `{entity}` | patroon ligt vast (één map per berichtsoort, genormaliseerd genoemd). De enige bestaande map heet `booking` en is **een werknaam van ons**; **de lijst soorten is `UNKNOWN — needs confirmation`** |
| `incoming` | ligt vast — framework |

## Toegang en authenticatie

**Dit is het scharnierpunt van de hele ontsluiting**, want het bepaalt of de leverancier het
adres hierboven überhaupt kan gebruiken.

### Wat OneLake accepteert

OneLake authenticeert **uitsluitend met Microsoft Entra ID-tokens** in de `Storage`-audience.
Er is geen accountsleutel, geen SAS-link, geen anonieme upload, en geen SFTP of FTP. Een partij
die niet met een Entra-identiteit kan aanmelden, kan niet rechtstreeks in OneLake schrijven —
hoe de map ook is ingericht. (Microsoft Learn, *How do I connect to OneLake?*, geraadpleegd
08-09-2026.)

Wat wél werkt: elk hulpmiddel dat met de ADLS- of Blob-API overweg kan, mits het het
OneLake-endpoint accepteert. De afbeelding is: accountnaam is altijd `onelake`, de container is
de workspace, en het pad begint bij het item.

### Hoe smal het schrijfrecht kan

Schrijfrecht hoeft **niet** de hele workspace te zijn. Een OneLake-beveiligingsrol met de
`ReadWrite`-permissie kan op één map worden gezet, voor iemand die op de workspace verder alleen
Viewer is; `ReadWrite` op een map geldt voor die map en alles eronder, en maakt uploaden,
hernoemen en verwijderen mogelijk via notebooks, de OneLake file explorer of de OneLake-API's.
Wie Admin, Member of Contributor is, heeft al schrijfrecht en heeft er niets aan.

Broerlekkage bestaat niet: wie recht heeft op een submap mag de bovenliggende mappen alleen
doorlopen om erbij te komen, en ziet de buurmappen niet. Dat is bruikbaar bij de gekozen
indeling: het recht kan op `tomm/tbs/` staan, waarmee elke nieuwe berichtsoort eronder vanzelf
meekomt zonder dat er iets buiten deze bron open gaat.

> **Gedocumenteerd, niet geverifieerd.** Bovenstaande komt uit Microsoft Learn (*OneLake security
> roles, permissions, and scopes*, geraadpleegd 08-09-2026) en is in geen tenant nagemeten. Er
> bestaat in dit platform **geen script en geen procedure** om zo'n rol in te richten: het is een
> handmatige beheerhandeling, en dat blijft het tot iemand hem automatiseert. Het aanmaken van de
> map is inmiddels wél geautomatiseerd — zie *De map aanmaken* — maar dat is de andere helft.

**Er is vandaag geen schrijfrecht toegekend.** Dat de map bestaat en gevuld is, zegt daar niets
over: wij hebben hem gevuld met onze eigen identiteit. Voor de leverancier is er nog geen
identiteit, geen rol en geen adres dat is doorgegeven.

### De identiteitsvorm — een uitgestelde keuze

**Status: uitgesteld, in afwachting van het antwoord van de leverancier.** Dit is geen gat in het
onderzoek en geen vergeten beslissing: de keuze is bewust naar achteren geschoven omdat het
antwoord van de leverancier hem grotendeels maakt. Wat zij ondersteunen, bepaalt wat er
overblijft.

| Optie | Wat het kost, en hoe ver het reikt |
|---|---|
| **A — een dienstidentiteit** (app-registratie in de tenant van de klant) | Het schrijfrecht blijft bij `tomm/tbs/` en gaat geen millimeter verder. Geen tenantbrede instelling. Past bij een koppeling waarin een systeem levert en geen mens |
| **B — een gastaccount** voor een persoon bij de leverancier | Werkt ook wanneer er met de hand wordt geüpload. Maar het toekennen van een OneLake-beveiligingsrol aan een gast vereist dat de externe-samenwerkingsinstelling op *Guest users have the same access as members (most inclusive)* staat — **tenantbreed**, en dus een beslissing die alle gasten in de hele tenant raakt, niet alleen deze map |
| **C — wachten** tot de leverancier heeft geantwoord | De huidige stand |

**Dit verschil is de reden dat de vraag aan de leverancier zwaarder weegt dan hij oogt.** A en B
kosten niet hetzelfde: de ene blijft binnen deze bron, de andere zet een tenantbrede knop om.
Wie het antwoord van de leverancier leest, hoort dat verschil op dát moment te zien — niet pas
wanneer een beheerder de instelling openzet. Daarom is vraag 2 hieronder geformuleerd als "welke
identiteitsvormen ondersteunt uw systeem" en niet als "kunt u naar een Microsoft-omgeving
schrijven": alleen de eerste vorm van de vraag levert een antwoord op dat de keuze werkelijk
maakt in plaats van hem terug te leggen.

### Wat er verder nodig is

Ongeacht welke identiteitsvorm het wordt:

| Voorwaarde | Waarom, en wat het raakt |
|---|---|
| Een Entra-identiteit voor de leverancier in de tenant van de klant | Zonder identiteit is er niets om recht aan te geven. Welke vorm: zie hierboven |
| Tenantinstelling *Users can access data stored in OneLake with apps external to Fabric* | Vereist voor toegang tot OneLake buiten Fabric om. Wordt makkelijk over het hoofd gezien |
| De map moet bestaan vóór het recht wordt toegekend | Zie *De map aanmaken* |

### Secrets

Zolang de leverancier zelf schrijft, bewaart het platform **geen enkel credential van hem**: hij
authenticeert met zijn eigen identiteit bij Entra. Er is dus vandaag geen secretnaam nodig.

Verandert de route naar een brievenbus met een tussenstap, dan komt er wel een credential in
beeld en volgt de naam de conventie `{source}-{type}` — nooit een waarde in dit rapport, en
nooit in een gesprek.

## Formaat en codering

`UNKNOWN — needs confirmation` op alle punten: formaat, codering, scheidingsteken, kopregel,
bestandsnaamgeving. Het gelande materiaal heeft natuurlijk een formaat, maar dat is het formaat
dat wíj hebben neergezet — het zegt niets over wat de leverancier stuurt. Vraag 3 hieronder is
onbeantwoord.

**Eén randvoorwaarde is echter geen open vraag maar een gemeten feit, en hij beslist mee:**

> De generieke verwerking naar Silver leest **uitsluitend JSON**:
> `spark.read.option('multiline','true').schema(schema).json(input_paths.split(','))`
> — `notebook_ProcessToSilver_Generic_Child.py`, regel 183-187.

Er is geen pad voor CSV, Excel, XML of Parquet. Levert de bron iets anders aan, dan is dat geen
configkwestie maar een frameworkuitbreiding, of er moet stroomopwaarts worden omgezet — en die
omzetstap bestaat hier evenmin. **Dit is de eerste vraag die aan de leverancier beantwoord moet
worden**, want het antwoord bepaalt of de gekozen route zonder bouwwerk haalbaar is.

Het schema wordt bovendien **expliciet** meegegeven aan de lezer; het wordt niet afgeleid. Een
veld dat niet in het schema staat, komt niet mee — stil. Dat maakt een echt voorbeeldbericht
geen luxe maar de voorwaarde om te beginnen.

## Kolomschema

`UNKNOWN` — de leverancier heeft nog geen bericht aangeleverd.

Er is bewust geen schema afgeleid uit productbeschrijvingen of publieke documentatie. Een schema
dat als gemeten leest terwijl het geraden is, is schadelijker dan geen schema: de config-builder
bouwt erop verder en een ontbrekende of verkeerd benoemde kolom faalt niet, die blijft leeg.

**Er ligt wel materiaal om een schema uit te tellen, en het is niet van de leverancier.** De 231
bestanden in `booking/incoming/` zijn te lezen en te tellen, en de config-builder doet dat ook —
dat is zijn werk voor de secties 3 tot en met 5. Wat daaruit komt beschrijft dan de vorm van
**ons testmateriaal**. Zolang de leverancier niets heeft geleverd, is dat een aanname over hem en
geen meting van hem; komt zijn eerste echte bericht er anders uit te zien, dan zijn die secties
mis en moeten ze opnieuw.

### Eén map is niet hetzelfde als één Silver-tabel

Het is verleidelijk om "één map per berichtsoort" te lezen als "één Silver-tabel per
berichtsoort". Dat volgt er niet uit:

> De verwerking leidt uit één Bronze-entity meerdere Silver-entities af. De Silver-lijst is
> `[entity_to_process] + de rijen waarvan `ParentEntity` gelijk is aan die entity` — de ouder
> eerst, daarna zijn kinderen. (`notebook_ProcessToSilver_Generic_Child.py`, regel 137-146;
> `05_entity_process_config.template.md` → *Parent / expanded children*.)

Een array in het bericht kan dus in sectie 4 worden uitgeklapt naar een eigen Silver-tabel, met
sectie 5 die het kind aan zijn ouder koppelt. **Gevolg voor het adres:** het aantal mappen hoeft
niet gelijk te zijn aan het aantal Silver-tabellen. Levert de leverancier alles in één stroom,
dan is dat werkbaar — de scheiding wordt dan in sectie 4 en 5 gemaakt in plaats van in het pad.
Dat neemt de scherpte van risico 2 hieronder weg, maar beantwoordt vraag 4 niet: welke soorten er
zijn, blijft aan de leverancier.

## Sleutel en watermark

`UNKNOWN` — beide vragen (welke velden een bericht uniek maken, en waaraan je ziet dat een
boeking is gewijzigd) zijn pas op echte berichten van de leverancier te beantwoorden, en horen
bovendien bij de telling die op Bronze wordt gedaan.

Wat nu al vaststaat: de verwerking voegt zelf een `FileName`-kolom toe met het volledige pad van
het bronbestand. Dat geeft altijd een terugvalvolgorde voor ontdubbeling, ook wanneer de bron
zelf geen wijzigingsmoment meestuurt.

## Volume en leveringspatroon

`UNKNOWN — needs confirmation`: frequentie, delta of volledige set, aantal bestanden per
levering, bestandsgrootte, en of alle bestanden verwerkt moeten worden of alleen het laatste.

**De 231 bestanden in Bronze zijn hier geen antwoord op.** Ze zijn in één handeling door ons
neergezet; het tijdstempel van 19:28 is het moment waarop wíj landden, geen leveringsmoment. Er
is nog geen levering geweest, dus er is nog niets om een patroon uit af te lezen.

## Aansluiting op de general-notebooks

| Punt | Oordeel |
|---|---|
| `push` wordt herkend en de ingestie wordt overgeslagen | werkt |
| Aanmaken van de ontvangstmap, met terugleescontrole | werkt — `bronze_stage.py --action prepare` |
| Testmateriaal neerzetten in `incoming/`, alleen op DEV | werkt — `bronze_stage.py --action land` |
| Verplaatsen van `incoming/` naar `processing/`, met telcontrole | werkt |
| Archivering na verwerking, ook op een lakehouse | werkt |
| Meerdere Silver-tabellen uit één Bronze-map | werkt — ouder-kindrelatie in sectie 5 |
| Lezen van de aangeleverde bestanden | **alleen JSON** — zie *Formaat en codering* |
| Toekennen van schrijfrecht aan een externe partij | **geen script** — handmatige beheerhandeling |
| Afleiden van de omgevingskolom bij een lakehouse-Bronze | **gerepareerd in de broncode; niet vastgesteld of die versie draait** — zie hieronder |

### `EnvironmentColumnName` bij een Bronze-lakehouse — gat, en de reparatie

**Wat het gat was.** De omgevingskolom werd gevuld met het **vijfde** padsegment van de
bestandsnaam: `element_at(split(col('FileName'), '/'), 5)`. Dat klopt voor een opslagaccount
(`abfss://container@account.../{source}/{env}/…` → segment 5 is de omgeving), maar niet voor een
lakehouse: daar staat er nog een item-segment tussen
(`abfss://workspace@onelake.../{lakehouse}/Files/{source}/{env}/…`), waardoor segment 5 het woord
`Files` is. Gevolg: stil de waarde `Files` in die kolom. Geen foutmelding, geen lege waarde — een
verkeerde waarde.

**Wat er is veranderd.** De broncode telt inmiddels vanaf het eind:
`element_at(split(col('FileName'), '/'), -5)`, met de onderbouwing in de code ernaast — de staart
onder de bronmap ligt vast (`{source}/{env}/{entity}/processing/{tijdstempel}/{bestand}`), het
voorvoegsel erboven niet. (`notebook_ProcessToSilver_Generic_Child.py`, regel 191-203.)

**Wat er níet is vastgesteld:** of de DEV-werkruimte die versie van het notebook draait. De
reparatie staat in de broncode van het framework; welke versie er in de werkruimte is
gedeployed, is niet gemeten. Zolang dat niet is nagegaan, is `Files` in die kolom een uitkomst
die je nog kunt tegenkomen — en het valt alleen op als je ernaar kijkt.

Voor deze bron is de scherpte er iets af nu er één vaste vestigingsaanduiding is: er valt niets te
onderscheiden, dus die kolom is hier waarschijnlijk niet nodig. Het punt blijft staan voor de
klant die hem wél nodig heeft.

## Risico's

**1. Het geleverde mechanisme kan een bericht zijn in plaats van een bestand.** De publieke
documentatie van de leverancier beschrijft als koppelvorm een **HTTP POST per reservering** naar
een URL die de afnemer zelf opgeeft, met JSON in de body en een vaste header waarmee de ontvanger
kan vaststellen dat de aanroep echt van hen komt; daarnaast wordt een GET genoemd om
reserveringen op te halen. De bronpagina's van het supportportaal gaven HTTP 403 en konden niet
worden geopend — dit komt dus uit zoekresultaten en is **niet bevestigd door de leverancier**.

Klopt het, dan levert de bron geen bestanden in een map en is er een ontvanger nodig die elk
bericht wegschrijft naar `incoming/`. Die ontvanger bestaat niet in dit platform. Dit is de
belangrijkste openstaande vraag; de rest van de ontsluiting hangt eraan.

**2. De leverancier scheidt zijn berichten misschien niet.** Het adrespatroon gaat uit van één
map per soort. Levert de bron alles in één stroom, dan is er één soort en dus één map. Dat werkt:
de scheiding kan in sectie 4 en 5 worden gemaakt in plaats van in het pad — zie *Eén map is niet
hetzelfde als één Silver-tabel*. Wat dan wél verandert, is dat de vorm van de berichten die
scheiding moet dragen, en dat blijkt pas uit het antwoord op vraag 4.

**3. De identiteitsvorm kan een tenantbrede instelling meebrengen.** Ondersteunt de leverancier
alleen een gebruikersaanmelding, dan komt optie B in beeld en daarmee een instelling die alle
gasten in de tenant raakt. Dat is geen detail van deze koppeling maar een beslissing van de
beheerder van de tenant, en hij hoort genomen te worden op het moment dat het antwoord binnenkomt
— niet stilzwijgend wanneer iemand het recht probeert toe te kennen en merkt dat het niet lukt.

**4. De vertaalslag in de mapnaam.** Omdat de mapnaam wordt genormaliseerd en niet overgenomen,
staat er in het adres een ander woord dan de leverancier zelf gebruikt. Bij elk adres hoort dus
de mededeling welke soort het is, en een vertaalfout zit in een adres dat al is doorgegeven. Voor
`booking` geldt bovendien het omgekeerde probleem: die naam is niet vertaald maar verzonnen, en
er is nog geen leveranciersterm waaraan hij gekoppeld kan worden.

**5. Persoonsgegevens.** Boekingsberichten bevatten gastgegevens (naam, adres, contactgegevens,
geboortedatum). **Dat is hier geen verwachting meer maar een gemeten feit:** het materiaal dat in
Bronze staat, staat er als origineel — bewust, want Bronze hoort de echte levering te houden.

Vier gevolgen:

| Gevolg | Wat het betekent |
|---|---|
| Wie deze map inspecteert, werkt met persoonsgegevens | De inspectiescripts maskeren standaard; `--no-redact` bestaat en zet dat uit. Dat is een bewuste handeling en hoort dat te blijven |
| Een voorbeeld in een rapport is altijd geredigeerd | Veldnamen blijven, waarden gaan eruit — vóór het rapport wordt weggeschreven, nooit erna |
| Het schrijfrecht op de map hoort zo smal mogelijk te zijn | Zie *Hoe smal het schrijfrecht kan* |
| Ruw materiaal hoort niet in een gesprek | Ook niet "even ter illustratie" |

**Twee gaten in die maskering zijn op 08-09-2026 gedicht, met tests** (`scripts/lib/pii_redact.py`,
`scripts/tests/test_pii_redact.py`). Ze zijn allebei op deze bron gevonden:

| Gat | Waarom het bestond | Wat er nu gebeurt |
|---|---|---|
| `birthday` en `verjaardag` werden niet als persoonsgegeven herkend | De tokenizer splitst een aaneengeschreven woord niet, dus `birth` ving `BirthDate` en `dateOfBirth` wél en `birthday` niet. In een steekproef op het gelande materiaal stonden 527 geboortedatums onafgeschermd | Beide woorden staan er als heel woord bij |
| Vrije tekst in een maatwerkveld-container bleef staan | Het waardeveld binnen zo'n container heeft geen herkenbare naam, dus een deny-list op veldnamen kan er niets mee | Binnen zo'n container geldt de omgekeerde regel: elke **tekst** is persoonlijk tot het tegendeel blijkt. Getallen en ja/nee blijven staan — die dragen de structuur |

**Wat dit niet doet:** het maskeert wat er uit een inspectiescript komt, niet wat er in Bronze
staat. Daar staan de originelen, en dat is de bedoeling.

**6. Een adres bij een leverancier is duur om te wijzigen.** Het adres wijst naar de omgeving die
er vandaag is. Komt er later een productieomgeving bij, dan verandert het adres en moet de
leverancier het opnieuw instellen. Met één adres per berichtsoort geldt dat bovendien per soort.

**7. Het gelande materiaal kan voor een levering worden aangezien.** Er staan 231 bestanden in een
ontvangstmap met een tijdstempel van vanavond. Aan de data is niet te zien dat wij ze daar hebben
gezet, en `--action land` laat geen spoor achter dat dat onderscheid draagt. Wie deze map over
een paar weken tegenkomt zonder dit rapport, ziet een lopende koppeling. Dat is precies wat dit
rapport moet voorkomen, en het is de reden dat de herkomst hierboven een eigen sectie heeft.

## Open vragen / UNKNOWNs

> **Status op 08-09-2026: er is op geen van de vragen aan de leverancier een antwoord ontvangen.**
> Ze zijn hieronder ongewijzigd blijven staan. Vraag 1 tot en met 4 zijn degene waar deze bron op
> wacht; dat het gelande materiaal er is, verandert daar niets aan — het komt niet van de
> leverancier en beantwoordt dus geen enkele van deze vragen.

Aan de leverancier — **alle onbeantwoord**:

1. **[onbeantwoord]** Zetten jullie bestanden neer, of stuurt jullie systeem per boeking een
   bericht naar een webadres dat wij opgeven? *(beslist welke route haalbaar is)*
2. **[onbeantwoord]** **Met welke identiteitsvormen kan uw systeem zich aanmelden bij een
   Microsoft-omgeving?** Een eigen app-registratie of dienstidentiteit met een clientgeheim of
   certificaat, een gebruikersaccount dat interactief aanmeldt, of een gastaccount in onze
   omgeving? En kunt u alleen naar SFTP, FTP of een deellink schrijven? *(OneLake kent uitsluitend
   Entra ID; dit antwoord maakt bovendien de uitgestelde identiteitskeuze — zie hieronder)*

   > **Waarom deze vraag zwaarder weegt dan hij oogt.** Een dienstidentiteit houdt het
   > schrijfrecht bij `tomm/tbs/`. Een gastaccount vereist daarnáást een **tenantbrede**
   > instelling die alle gasten in de hele tenant raakt. Die twee kosten dus niet hetzelfde, en
   > dat verschil hoort zichtbaar te zijn op het moment dat dit antwoord wordt gelezen. Zie
   > *De identiteitsvorm — een uitgestelde keuze*.

3. **[onbeantwoord]** Kan de inhoud als **JSON** worden aangeleverd? *(alles daarbuiten vraagt
   bouwwerk)*
4. **[onbeantwoord]** **Welke berichtsoorten stuurt u, en levert u ze gescheiden aan?** Boekingen,
   wijzigingen, annuleringen, gastgegevens — en hoe noemt u ze zelf? *(dit is het enige dat het
   adres nog mist: elke soort wordt een map, en hun eigen benaming is nodig om te kunnen
   vertalen. Zolang deze vraag openstaat, is `booking` een werknaam van ons)*
5. **[onbeantwoord]** Levert u per vestiging of park apart aan, of alles in één stroom? *(niet meer
   bepalend voor het pad — dat kent één vaste vestigingsaanduiding, ook die door ons gekozen —
   maar wel voor de vraag of één map per soort volstaat)*
6. **[onbeantwoord]** Hoe vaak wordt er geleverd, en is dat steeds de volledige set of alleen wat
   is gewijzigd?
7. **[onbeantwoord]** Hoe heten de bestanden, en welke codering hebben ze?
8. **[onbeantwoord]** Wie is de contactpersoon voor deze koppeling?

Aan onze kant:

9. Welke genormaliseerde mapnaam krijgt elke bevestigde soort? *(mechanisch zodra de lijst uit
   vraag 4 er is: Engels, enkelvoud, kleine letters; `all` valt af)*
10. Blijft de bestaande map `booking` heten wanneer vraag 4 is beantwoord, of wordt hij hernoemd?
    Hernoemen is goedkoop zolang het adres nog niet aan de leverancier is doorgegeven, en duur
    daarna.
11. Wie richt de Entra-identiteit en het schrijfrecht op `tomm/tbs/` in, en wanneer? Er is geen
    script voor; het is een handmatige beheerhandeling, en hij komt ná het aanmaken van de map.
12. Dienstidentiteit of gastaccount? **Uitgesteld tot het antwoord op vraag 2** — de opties en hun
    kosten staan onder *De identiteitsvorm — een uitgestelde keuze*.
13. Draait de DEV-werkruimte de versie van het verwerkingsnotebook waarin de omgevingskolom is
    gerepareerd? Niet vastgesteld; zie *`EnvironmentColumnName` bij een Bronze-lakehouse*.

**Klaar om verder te gaan is deze bron pas na twee dingen:** een antwoord op vraag 1 tot en met 4,
en één echt aangeleverd bericht **van de leverancier**. Geen van beide is er.

**Het gelande testmateriaal telt hier niet voor mee.** Het is bruikbaar om de verwerking te
beproeven en om er secties 3 tot en met 5 op te tellen, en dat is ook wat ermee gebeurt — maar
wat daaruit komt beschrijft ons eigen materiaal. Wordt dat als vastgesteld gelezen, dan staat er
een schema in de config dat de leverancier nooit heeft bevestigd, op een adres dat hij nooit heeft
gekregen, onder een soortnaam die hij nooit heeft genoemd.
