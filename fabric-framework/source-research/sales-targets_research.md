# Verkoopdoelen per verkoper — bronresearch (`sales-targets`)

> **Stand van zaken 14-09-2026.** Er is één bestand, het is volledig gelezen, en het staat nog
> nergens in een Fabric-omgeving: het ligt in de demodata van deze codebase. Alles wat hieronder
> over formaat, kolommen en sleutel staat, is op dát bestand gemeten — niet op een levering. Het
> ontvangstadres, de omvang van een levering, het ritme, wie aanlevert en de naamgeving zijn op
> 14-09-2026 door de opdrachtgever vastgesteld; die vijf staan hieronder als besluit en niet meer
> als open vraag. Vastgesteld is niet gemeten: er is nog geen levering om ze aan af te lezen.

> **Het bestand is een repetitie, en dat is een eigenschap van de meting.** Het is gemaakt bij een
> demo-brondatabase; later komt er een echt bestand dat er naar verwachting hetzelfde uitziet.
> "Naar verwachting" is geen meting: zolang dat echte bestand er niet is, beschrijft het
> kolomschema hieronder één bestand en niet de bron. Risico 2 werkt uit wat dat betekent.

## TypeSource

- **Vastgesteld:** `push`
- **Door intake afgeleid:** bestandsbron, met de hand neergezet — hetzelfde, en `push` is in dit
  framework de vorm waarin een bestandslevering binnenkomt.

`push` betekent wat `01_source_config.template.md` erover zegt: de data wordt bij ons neergezet in
plaats van opgehaald, en het framework draait geen Bronze-ingestie. `SourceDetails` is `None`.

**Er is hier wél een sectie 2, en die is niet leeg.** Dat is voor een aangeleverde bron het enige
wat erin staat, en het is precies wat deze bron nodig heeft:

| Veld | Waarde voor deze bron | Waarom het niet weggelaten kan worden |
|---|---|---|
| `TypeIngestion` | `file` | markeert de regel als levering in plaats van ophaalinstructie |
| `BronzeFormat` | `csv` | de kolom staat in de database op `NOT NULL default 'json'`; blijft die default staan, dan opent de Silver-verwerking dit CSV-bestand met de JSON-lezer |
| `FormatOptions` | mag `null` — zie *Formaat en codering* | draagt scheidingsteken en codering wanneer die van de standaard afwijken |
| `WatermarkType` | `null` | de levering draagt geen wijzigingsmoment — zie *Sleutel en watermark* |

De referentie is `02c_entity_ingestion_config_file.template.md`. Alle ophaalbegrippen
(`strategy`, `url_path`, `extra_*`, `output_*`, `batch_size`) blijven `null`.

## Overzicht

Een maandelijks omzet- en orderdoel per verkoper: één regel per verkoper per maand. Het soort
gegeven dat nooit in een ERP staat maar in een spreadsheet van een verkoopmanager, en dat pas
waarde krijgt naast de gerealiseerde verkoop.

De richting ligt vast: **het bestand wordt bij ons neergezet, wij halen niets op.** Er is geen
API, geen database en geen map elders die wij mogen benaderen.

## Wat er is gemeten, en waarop

| Meting | Waarde |
|---|---|
| Bestand | `demo-sources/wide-world-importers/sales-targets-2026.csv` in deze codebase |
| Omvang | 5.602 bytes |
| Regels | 121, inclusief kopregel — dus 120 gegevensregels |
| Gelezen | **volledig**, alle 120 regels; dit is geen steekproef |
| Gemeten op | 14-09-2026 |

Te reproduceren met:

```bash
python scripts/source_file_probe.py \
  --path demo-sources/wide-world-importers/sales-targets-2026.csv \
  --key SalespersonId,PeriodStart
```

Regeleinde, byte order mark en aanhalingstekens staan niet in die uitvoer; die drie komen uit een
byte-inspectie van het hele bestand en staan hieronder apart gemarkeerd.

> **Let op bij het herhalen van die aanroep.** De standaardredactie sloeg hier niets over het
> hoofd omdat ze niets zag: geen enkele kolomnaam kwam voor op de lijst met persoonsgegevens, dus
> de namen in `Salesperson` werden voluit afgedrukt. Ze zijn hier met de hand weggelaten. Wie de
> uitvoer in een document overneemt, doet dat ook — of draait de aanroep met `--shape-only`, die
> in het geheel geen waarden afdrukt (ook niet voor de kolommen waar ze nuttig zijn).

**Wat deze meting wel en niet bewijst:**

| Wel | Niet |
|---|---|
| Hoe dít bestand gelezen moet worden: scheidingsteken, codering, kopregel, kolommen, typen | Dat een volgende levering dezelfde vorm heeft |
| Dat de kandidaatsleutel over alle 120 regels uniek is — een telling, geen schatting | Dat de sleutel uniek blijft over meerdere leveringen heen |
| Dat het bestand geen lege waarden, geen aanhalingstekens en geen afwijkende regels bevat | Dat de aanleveraar dat volhoudt |

Een schemavergelijking over meerdere bestanden is **niet** gedaan en kan niet: er is één bestand
van deze soort.

## Leveringstype en route

### Leveringstype

Eén CSV-bestand, met de hand neergezet, en bij elke levering **vervangen** in plaats van aangevuld
— zie *Volume en leveringspatroon*, waar dat besluit staat. Er staat geen ophaalstap
tussen, en er is geen tussenopslag: de enige plek waar het bestand kan landen is de ontvangstmap in
Bronze (zie hieronder waarom er geen alternatief is).

### Route: inlezen (Bronze → Silver)

**Stap 1 van de skill is expliciet beantwoord, ook al is de uitkomst de gewone.** De drie routes
sluiten elkaar per entity uit:

| Route | Oordeel | Waarom |
|---|---|---|
| **Mirror** | valt af | Bij een bestandslevering komt een mirror alleen in beeld voor een SharePoint-lijst. Dit is een bestand, geen lijst |
| **Shortcut** | valt af | Een shortcut verschijnt rechtstreeks als Silver-tabel: geen typering, geen sleutelcontrole, geen ontdubbeling, geen versheidsbewaking. Een CSV draagt bovendien geen typen — datum en bedrag zouden als tekst in Silver landen. En de vorm ligt niet vast: een met de hand bijgehouden overzicht is per definitie niet geconformeerd. Er is daarnaast geen opslaglocatie om naartoe te wijzen: het bestand wordt in onze eigen Bronze neergezet |
| **Inlezen** | **gekozen** | De data moet getypeerd, gecontroleerd en onderhouden worden voordat hij bevraagbaar is. Dat is de definitie van inlezen |

Dat inlezen begint bij `incoming/` en niet bij een ingestienotebook: de bron is `push`, dus de
eerste stap die het framework zelf draait is de verwerking naar Silver.

### Waarom er geen brievenbus elders is

Overwogen en afgevallen: het bestand in een opslagaccount of een documentbibliotheek van de klant
laten landen en het daar ophalen. Het transport van zo'n brievenbus naar Bronze zit **niet** in dit
framework — de drie framework-pijplijnen zijn API/SOAP-ingestie, SQL-ingestie en de
Silver/Gold-keten. Er is geen generieke bestandskopie. Die route is dus geen configuratiekwestie
maar een los te bouwen en te onderhouden onderdeel.

## Het ontvangstadres

### De padvorm ligt vast in het framework

```
{Bronze Files}/{source}/{environment}/{entity}/incoming/
```

Dat is geen conventie maar code: `move_files_to_processing` bouwt exact dit pad
(`notebook_Functions_Silver.py`, regel 119-121).

### Wat vastligt, en wat op 14-09-2026 is gekozen

| Segment | Status |
|---|---|
| `{Bronze Files}` | ligt vast — volgt uit het klantprofiel |
| `{source}` | ligt vast — `sales-targets` |
| `{environment}` | **`default`** — gekozen 14-09-2026. Eén vast woord, in elke omgeving hetzelfde, zodat wie aanlevert bij een promotie naar productie niets aan zijn instelling hoeft te veranderen. Er wordt niet per vestiging of per aanleveraar gescheiden |
| `{entity}` | **`sales_target`** — gekozen 14-09-2026. Eén map, want één soort bestand; snake_case, Engels, enkelvoud, zoals de conventie voor entitynamen vraagt |
| `incoming` | ligt vast — framework |

Daarmee is het adres volledig:

```
{Bronze Files}/sales-targets/default/sales_target/incoming/
```

**Wat dat vaste woord wel en niet doet.** Het houdt het deel van het adres ná de wortel in elke
omgeving gelijk. De wortel zelf — `{Bronze Files}` — is de opslag van één werkruimte en hoort dus
bij de omgeving; dat verschil neemt een vast padsegment niet weg.

**Waarom dit eerst een vraag was en geen afleiding.** Elk segment wordt een deel van het adres waar
iemand zijn bestand naartoe brengt. Een afgeleide of een werknaam die eenmaal in een listing staat,
leest na een paar weken als een afspraak — hij is concreet, hij bestaat, en er staan bestanden in.
Daarom is de keuze opgehaald vóór het aanmaken van de map, niet erna.

**`all` kan geen mapnaam zijn.** Dat woord is in de parameterverwerking gereserveerd voor "alle
waarden uit de config"; een map die zo heet is later niet los aan te spreken. Het aanmaakcommando
weigert die naam — en verder geen enkele, dus `default` gaat er wel door.

### De map aanmaken — wat er wel en niet is geregeld

```bash
python scripts/bronze_stage.py --profile {profile} --source sales-targets \
  --action prepare --env default --entity sales_target [--dry-run]
```

Het maakt **alleen** `incoming/` aan, leest het pad terug voordat het het adres afdrukt, en
verandert niets wanneer het pad al bestaat. `--env` en `--entity` zijn verplicht en worden nooit
afgeleid: ze worden een segment van het adres.

**Wat het uitdrukkelijk níet doet: rechten toekennen.** De map aanmaken opent hem voor niemand. Of
er een recht nodig is, hangt aan wie het bestand straks neerzet — en dat is op 14-09-2026
vastgesteld: **iemand die al toegang heeft tot de werkruimte.** Daarmee valt de tweede regel weg:

| Wie levert aan | Wat er nodig is |
|---|---|
| **Iemand die al toegang heeft tot de werkruimte** — zo is het besloten | niets extra's — de map aanmaken volstaat |
| Een partij van buiten | *voor deze bron niet van toepassing.* Zou het er ooit een worden: een Entra-identiteit plus een OneLake-beveiligingsrol op de bronmap, en dat is **handmatig beheerwerk waarvoor geen script bestaat** |

De volgorde is niet omkeerbaar: **eerst de map, dan het recht** — een recht kan alleen worden
toegekend op een map die al bestaat. Bij deze bron is er geen recht toe te kennen, dus het aanmaken
van de map is de hele inrichting.

### Testmateriaal neerzetten

`bronze_stage.py --action land` zet bestanden uit een lokale map in `incoming/`, zoals een
aanleveraar dat zou doen. Drie eigenschappen die er hier toe doen:

| Eigenschap | Waarom het telt |
|---|---|
| **Alleen DEV** | Productie hoort zijn data van de aanleveraar te krijgen; met de hand geland materiaal is daar later niet van te onderscheiden |
| Alleen naar `incoming/`, nooit naar `processing/` | Het volgt dezelfde weg als een echte levering, dus de verwerking is er eerlijk mee te beproeven |
| Weigert wanneer `incoming/` al gevuld is, tenzij `--yes` | Het framework leest alles wat er staat; twee keer landen levert elke regel twee keer op |

**Aan een bestand in Bronze is niet te zien dat wij het daar hebben gezet.** Dit rapport is de plek
waar die herkomst staat vastgelegd.

### Levenscyclus van een bestand

```
incoming/  ->  processing/{tijdstempel}/  ->  archive/{jaar}/{maand}/{tijdstempel}/
```

De verwerking verplaatst zelf uit `incoming/` en telt vóór en na de verplaatsing; wijken die
aantallen af, dan faalt de run in plaats van stil data te verliezen. **Wie aanlevert schrijft
uitsluitend in `incoming/`** — de twee andere mappen zijn van het framework.

## Formaat en codering

| Eigenschap | Waarde | Hoe vastgesteld |
|---|---|---|
| Formaat | `csv`, plat — geen geneste structuren | probe |
| Scheidingsteken | `,` (komma) | probe, via de sniffer |
| Kopregel | ja, één | probe, via de sniffer |
| Velden per regel | `{7: 121}` — 7 velden op **elke** regel, kopregel inbegrepen | probe |
| Codering | `utf-8-sig`, schoon gedecodeerd | probe |
| — byte order mark | **geen**, ondanks die codecnaam: `utf-8-sig` leest een bestand zonder BOM net zo goed | byte-inspectie |
| — tekenbereik | zuiver ASCII: 0 bytes boven 127 in het hele bestand, dus ook geldig UTF-8 | byte-inspectie |
| Regeleinde | CRLF (`\r\n`), op alle 121 regels, ook de laatste: 121 × CRLF, 0 losse LF | byte-inspectie |
| Aanhalingstekens | geen, nergens in het bestand — 0 voorkomens van `"` | byte-inspectie |
| Lege waarden | geen, in geen enkele kolom | probe |

### Hoe de lezer hiermee moet worden ingesteld

De Silver-verwerking kiest zijn lezer op `BronzeFormat` en geeft `FormatOptions` rechtstreeks aan
Spark door (`notebook_ProcessToSilver_Generic_Child.py`, regel 182-212):

| Instelling | Waarde voor deze bron | Toelichting |
|---|---|---|
| `BronzeFormat` | `csv` | **de enige instelling die echt moet.** Blijft de default `json` staan, dan leest de JSON-lezer een CSV en levert een lege of nul-gevulde tabel op — zonder foutmelding |
| `FormatOptions` | mag `null` | Het gemeten bestand valt op elk punt samen met de standaarden: komma, UTF-8, kopregel. Expliciet vastleggen mag: `{"sep": ",", "encoding": "UTF-8"}` is equivalent |
| `header` | staat vast op `true` in de notebook | zonder kopregel is er niets om kolommen op naam te koppelen |
| `enforceSchema` | staat vast op `false` in de notebook | kolommen worden gekoppeld op **kopnaam** in plaats van op positie. Zie risico 1 voor de keerzijde |
| `pathGlobFilter` | standaard `*.csv` bij csv | het gemeten bestand heeft die extensie; een levering met `.txt` vraagt een eigen waarde |
| Regeleinde | niets in te stellen | de CSV-lezer verwerkt `\r`, `\n` en `\r\n` zonder opgave zolang `lineSep` niet is gezet — gedocumenteerd gedrag, niet in een run nagemeten |

## Kolomschema

Zeven kolommen, in deze volgorde, overgenomen uit de probe. Het schema wordt bij het lezen
**opgelegd** (sectie 3) en op kopnaam gekoppeld; een kolom die in de kopregel ontbreekt levert
`null` op in plaats van te verdwijnen.

| # | Kolomnaam | dtype | Spark-type | Nullable | Verschillende waarden | Voorbeeldwaarden |
|---|---|---|---|---|---|---|
| 1 | `PeriodStart` | str | `StringType -> DateType` | Nee | 12 | `2026-01-01`, `2026-02-01`, `2026-03-01` |
| 2 | `Year` | int64 | `LongType` | Nee | 1 | `2026` |
| 3 | `Month` | int64 | `LongType` | Nee | 12 | `1`, `2`, `3`, `4`, `5` |
| 4 | `SalespersonId` | int64 | `LongType` | Nee | 10 | `2`, `3`, `6`, `7`, `8` |
| 5 | `Salesperson` | str | `StringType` | Nee | 10 | REDACTED — persoonsnamen |
| 6 | `RevenueTarget` | int64 | `LongType` | Nee | 86 | `458000`, `500000`, `556000` |
| 7 | `OrderTarget` | int64 | `LongType` | Nee | 11 | `160`, `170`, `190` |

**De namen in kolom 5 zijn uit dit rapport weggelaten en niet uit de data.** Bronze houdt de
levering zoals hij binnenkomt; dit rapport staat in twee git-repo's en blijft daar. De
standaardredactie van de probe kwam hier niet in actie — zie de noot bij *Wat er is gemeten*.

**`PeriodStart` staat er met twee typen, en dat is geen slordigheid.** Een CSV draagt geen typen,
dus de kolom komt als tekst binnen; `DateType` is het doel. Of dat doel bij het lezen wordt
opgelegd of pas in sectie 4 wordt bereikt, is een keuze voor de bouwstap. Wat ervoor pleit het bij
het lezen te doen: de waarnotatie `yyyy-MM-dd` is exact de standaard `dateFormat` van de
CSV-lezer — gedocumenteerd gedrag, niet in een run nagemeten.

**Waargenomen waardenbereik** (over alle 120 regels, uit een byte- en kolominspectie; de
definitieve telling doet config-builder op Bronze):

| Kolom | Bereik | Vorm |
|---|---|---|
| `PeriodStart` | `2026-01-01` t/m `2026-12-01` | altijd 10 tekens, altijd de 1e van de maand |
| `Year` | 2026 | 4 cijfers |
| `Month` | 1 t/m 12 | 1-2 cijfers |
| `SalespersonId` | 2 t/m 20, niet aaneengesloten | 1-2 cijfers, geen voorloopnullen |
| `Salesperson` | — | 9-18 tekens, twee woorden (voornaam + achternaam), alleen letters en één spatie |
| `RevenueTarget` | 440.000 t/m 707.000 | 6 cijfers, geen scheidingsteken, geen decimalen, niet negatief |
| `OrderTarget` | 150 t/m 250 | 3 cijfers, geen decimalen |

### Drie eigenschappen die de bouwstap moet kennen

1. **`Year` en `Month` zijn afleidbaar uit `PeriodStart`** en komen er in dit bestand op alle 120
   regels mee overeen. Ze zijn dus redundant, niet tegenstrijdig. Of ze meegaan naar Silver of daar
   uit de datum worden afgeleid, is een keuze voor sectie 4.
2. **`Salesperson` hangt volledig aan `SalespersonId`** in dit bestand: elke id heeft precies één
   naam en elke naam precies één id. De naam is beschrijvend; de koppeling loopt over het id.
3. **Elke verkoper heeft precies 12 regels, één per maand.** 10 verkopers × 12 maanden = 120
   regels. Er zijn geen gaten en geen dubbele maanden.

### Wat de verwerking zelf toevoegt

- **`FileName`** — het volledige pad van het bronbestand, door de verwerking toegevoegd. Dat is de
  enige herkomstinformatie die een regel draagt, en de terugvalvolgorde bij ontdubbeling.
- **Een omgevingskolom is hier niet nodig.** `EnvironmentColumnName` leidt die af uit een segment
  van het pad; met `default` als vaste waarde levert dat een kolom op die op elke regel `default`
  zegt. Laat hem `null`.

## Sleutel en watermark

**Sleutel: `SalespersonId` + `PeriodStart` — door de probe geverifieerd als uniek.**

| Kandidaat | Dubbelen over alle 120 regels |
|---|---|
| `SalespersonId` + `PeriodStart` | **0** — `unique` volgens de probe |
| `SalespersonId` + `Year` + `Month` | **0** — gelijkwaardig, want de maandonderdelen zijn afleidbaar uit de datum |
| `PeriodStart` alleen | 108 |
| `SalespersonId` alleen | 110 |

Dit is een telling over de volledige inhoud van het bestand, geen steekproef. Wat hij **niet**
dekt: uniciteit over meerdere leveringen heen. Dat is met besluit 2 van 14-09-2026 geen
mogelijkheid meer maar een zekerheid — elke levering bevat de volledige set opnieuw, dus na twee
leveringen staat dezelfde sleutel twee keer in Bronze en moet de ontdubbeling in sectie 5 hem
opvangen.

**Watermark: geen.** Er is geen kolom die meebeweegt met een wijziging — geen `Modified`, geen
versie, geen tijdstempel. `WatermarkType` blijft dus `null`, en dat is voor een levering de normale
uitkomst: een bestand is verwerkt zodra het naar `processing/` is verplaatst en daarna
gearchiveerd. Die bestandslevenscyclus ís het watermark.

**Gevolg voor ontdubbeling.** Komt dezelfde maand in twee leveringen voor, dan is er in de data
niets dat zegt welke de nieuwste is. `FileName` neemt die rol hier niet over: de naam is bij elke
levering dezelfde (besluit 5), dus hij onderscheidt de leveringen niet. Wat overblijft is de
bestandslevenscyclus zelf — elke levering wordt in zijn eigen `processing/{tijdstempel}` verwerkt en
daarna gearchiveerd, dus het moment van landen is af te lezen aan waar het bestand staat en niet aan
hoe het heet. Het moment van opstellen blijft onbekend.

## Volume en leveringspatroon

| Punt | Waarde |
|---|---|
| Aantal bestanden gezien | 1 |
| Omvang per bestand | 5,6 KB / 120 regels |
| Volumeverwachting | verwaarloosbaar — ook tien jaar aan leveringen blijft onder een megabyte |
| Bestandsnaam | **een vaste naam zonder jaar** — gekozen 14-09-2026; elke levering vervangt de vorige. Het gemeten bestand heet nog `sales-targets-2026.csv`; welk woord de vaste naam wordt, is niet vastgelegd en is ook niet nodig — de lezer filtert op `*.csv` en niet op een naam |
| Frequentie | **geen vast ritme** — er wordt geleverd wanneer de doelen worden bijgesteld |
| Delta of volledige set | **de volledige set opnieuw**, bij elke levering |
| Alle bestanden verwerken of alleen het laatste | volgt uit het bovenstaande: er staat per run precies één bestand. De levenscyclus haalt elke verwerkte levering uit `incoming/`, dus "alles verwerken" en "alleen het laatste verwerken" vallen hier samen |

Het framework leest **alles** wat in `incoming/` staat, en met deze antwoorden is dat ook de
bedoelde uitkomst: er staat in de regel één bestand, dat is de volledige set, en na verwerking is de
map leeg. Twee gevolgen die niet vanzelf opvallen:

- **Er is geen versheidsverwachting om op te bewaken.** Zonder vast ritme is een map die al weken
  leeg is niet te onderscheiden van een gemiste levering. Een alarm op uitblijven valt hier dus niet
  aan een ritme te hangen.
- **Twee leveringen vóór één verwerking worden er één.** Zie risico 8.

## Relatie tot de verkoopdata

De begeleidende documentatie bij de demodata beschrijft `SalespersonId` als de sleutel die aansluit
op de verkoper in de verkoopdata van de bijbehorende brondatabase, en `Salesperson` als de naam
zoals die daar staat — opgenomen zodat een afwijking zichtbaar is.

> **Gedocumenteerd, niet nagemeten.** Deze aansluiting is niet tegen de brondatabase gecontroleerd;
> dat is een vergelijking tussen twee gelande datasets en hoort bij de laag die ze naast elkaar
> zet. Het staat hier omdat het de reden is dat kolom 4 een id draagt en niet alleen een naam.

## Aansluiting op de general-notebooks

| Punt | Oordeel |
|---|---|
| `push` wordt herkend en de Bronze-ingestie wordt overgeslagen | werkt — `notebook_Ingestion_Generic_Parent.py`, regel 116-119 |
| CSV lezen in de verwerking naar Silver | **werkt** — `BronzeFormat: csv`, `notebook_ProcessToSilver_Generic_Child.py`, regel 182-212 |
| Kolommen koppelen op kopnaam in plaats van op positie | werkt — `enforceSchema=false` staat vast in de notebook |
| Alleen `*.csv` uit de map lezen | werkt — standaard `pathGlobFilter` bij csv |
| `yyyy-MM-dd` rechtstreeks als datumtype lezen | werkt volgens de standaard `dateFormat` van de CSV-lezer; gedocumenteerd, niet in een run nagemeten |
| Herkomstkolom `FileName` | werkt — de verwerking voegt hem zelf toe |
| Ontvangstmap aanmaken, met terugleescontrole | werkt — `bronze_stage.py --action prepare` |
| Bestanden neerzetten zoals een aanleveraar | werkt, **uitsluitend op DEV** — `bronze_stage.py --action land` |
| Een bestand ophalen uit een brievenbus elders en naar Bronze kopiëren | **bestaat niet** — geen generieke bestandskopie in de framework-pijplijnen |
| Schrijfrecht toekennen aan een partij van buiten | **geen script** — handmatige beheerhandeling. *Voor deze bron niet van toepassing: er levert geen partij van buiten aan* |

## Risico's

**1. Een gewijzigde kopregel levert stille nulls op.** Kolommen worden op naam gekoppeld en de lezer
staat in de standaard tolerante modus. Hernoemt iemand `RevenueTarget` naar `Revenue`, dan verdwijnt
er niets en faalt er niets — de kolom komt binnen als `null` over de hele linie. Dat is de keerzijde
van `enforceSchema=false`, en hij is bewust gekozen: koppelen op positie is erger, want dan schuift
een ingevoegde kolom élke waarde één plek op. Voor een bestand dat met de hand wordt bijgehouden is
dit het meest waarschijnlijke defect, en het valt pas op wanneer iemand een rapport wantrouwt.

**2. Het gemeten bestand is een repetitie.** Het is gemaakt bij de demodata, niet geleverd. Het
kolomschema, de sleutel en de typen hierboven beschrijven dit ene bestand. Ziet het echte bestand er
straks anders uit, dan zijn de secties 3 tot en met 5 mis — en ze falen niet luid, want een
onbekende kolom wordt niet gelezen en een ontbrekende kolom wordt `null`.

**3. De default van `BronzeFormat` is `json`.** Hij staat er altijd, want de kolom is `NOT NULL`. Bij
een aangeleverde bron is dat de ene default die je niet moet laten staan: de JSON-lezer op een CSV
geeft geen fout, maar een lege of nul-gevulde tabel.

**4. Bedragen zijn in dit bestand gehele getallen.** Zes cijfers, geen decimaalteken, geen
duizendtalscheiding, en de probe typeert de kolom als `LongType`. Een volgende levering die
`458.000` of `458000,50` schrijft, past daar niet in en komt binnen als `null` — opnieuw zonder
fout. De typekeuze voor kolom 6 is dus een beslissing met een gevolg, geen formaliteit.

**5. Persoonsgegevens.** `Salesperson` bevat namen. Bronze houdt de levering zoals hij binnenkomt,
dus iedereen die die map inspecteert werkt met persoonsgegevens. **De standaardredactie van de
inspectiegereedschappen ving deze kolom niet af** — de lijst matcht op kolomnaam en `Salesperson`
staat er niet op. Reken er bij deze bron dus niet op; redigeer met de hand of draai met
`--shape-only`.

**6. Twee bronnen voor dezelfde maand.** `PeriodStart` enerzijds en `Year`/`Month` anderzijds zeggen
hetzelfde. In dit bestand komen ze op elke regel overeen; in een volgend bestand kan dat uiteenlopen
zonder dat iets dat opmerkt. Wie beide kolommen naar Silver meeneemt, neemt die mogelijkheid mee.

**7. Een adres is duur om te wijzigen.** Het adres staat nu vast en wordt doorgegeven aan degene die
levert; elke wijziging eraan kost daarna een tweede ronde langs die persoon. Het vaste woord
`default` is juist gekozen om die ronde bij een promotie naar productie te vermijden — het deel ná
de wortel blijft dan gelijk. De wortel hoort bij de werkruimte en valt met een padkeuze niet vast te
zetten, dus die ronde is verkleind en niet weggenomen.

**8. Eén vaste bestandsnaam plus geen vast ritme: een levering kan er stil één worden.** Elke
levering heet hetzelfde, dus een tweede bestand op datzelfde adres vervangt het eerste — zo werkt
opslag; dat is hier niet nagemeten. Normaal is dat onschadelijk, want de verwerking haalt het
bestand uit `incoming/` en laat de map leeg achter. Maar wordt er twee keer geleverd vóórdat er is
verwerkt — en zonder vast ritme is dat niet te voorzien — dan verdwijnt de eerste levering zonder
foutmelding en zonder spoor in het archief. Omdat elke levering de volledige set bevat, blijft het
verlies beperkt tot regels die alléén in de overschreven versie stonden; die zijn achteraf niet
terug te halen.

## De vijf vragen — beantwoord op 14-09-2026

Alle vijf lagen bij de opdrachtgever en niet bij een leverancier: hij bepaalt zelf hoe hij
aanlevert. Op 14-09-2026 heeft hij ze alle vijf beantwoord. Hieronder staat per vraag het antwoord
en wat eruit volgt; in de secties hierboven is elk antwoord al op zijn eigen plek verwerkt.

| # | Vraag | Antwoord | Wat eruit volgt |
|---|---|---|---|
| 1 | Op welk adres komt het bestand te staan — welke waarde krijgt het omgevingssegment, en hoe heet de map voor de bestandssoort? | Omgevingssegment `default`, map `sales_target`. `default` is één vast woord in elke omgeving, gekozen zodat wie aanlevert bij een promotie naar productie niets aan zijn instelling hoeft te veranderen | Het adres is volledig: `{Bronze Files}/sales-targets/default/sales_target/incoming/`. De ontvangstmap kan worden aangemaakt — zie *Het ontvangstadres* |
| 2 | Wat bevat een volgende levering — de volledige set opnieuw, alleen de gewijzigde maanden, of een nieuw jaar naast het vorige? | **De volledige set opnieuw** | Een levering vervangt, hij vult niet aan. Na twee leveringen staat dezelfde sleutel twee keer in Bronze, dus sectie 5 moet ontdubbelen — zie *Sleutel en watermark* |
| 3 | Hoe vaak wordt er geleverd? | **Geen vast ritme** — er wordt geleverd wanneer de doelen worden bijgesteld | Er is geen versheidsverwachting om op te bewaken, en een uitblijvende levering is niet te onderscheiden van een periode zonder bijstelling — zie *Volume en leveringspatroon* en risico 8 |
| 4 | Wie zet het bestand neer — iemand die al toegang heeft tot de werkruimte, of een partij van buiten? | **Iemand die al toegang heeft tot de werkruimte** | Geen aparte identiteit, geen OneLake-rol, geen handmatige rechtentoekenning. Het aanmaken van de ontvangstmap is de hele inrichting — zie *De map aanmaken* |
| 5 | Is `sales-targets-{jaar}.csv` de bedoelde naamgeving? | **Nee — een vaste naam zonder jaar**; elke levering vervangt de vorige | De lezer filtert op `*.csv` en niet op een naam, dus de configuratie verandert er niet door. `FileName` onderscheidt hierdoor geen leveringen meer, en twee leveringen vóór één verwerking worden er één — zie risico 8 |

**Wat hierna nog niet vaststaat, is geen van deze vijf.** Twee dingen blijven open, en ze zijn van
een andere orde:

- **Het letterlijke woord van de vaste bestandsnaam.** Dat is met opzet geen blokkade: het filter van
  de lezer is `*.csv` en geen naam, dus niets in de configuratie hangt eraan. Alleen wanneer de
  extensie ooit afwijkt, wordt het een keuze — zie *Hoe de lezer hiermee moet worden ingesteld*.
- **Er is nog geen echte levering.** Risico 2 blijft daarmee onverminderd staan: alles over formaat,
  kolommen en sleutel is op het repetitiebestand gemeten, en de vijf antwoorden hierboven zijn
  afspraken en geen metingen.

---

*Bronresearch uitgevoerd 14-09-2026 en diezelfde dag bijgewerkt met de antwoorden van de
opdrachtgever op de vijf openstaande vragen. Het bestand is volledig gelezen; het formaat, het
kolomschema en de sleutel zijn gemeten. Het ontvangstadres, de omvang van een levering, het ritme,
wie aanlevert en de naamgeving zijn vastgesteld — vastgesteld, niet gemeten, want er is nog geen
levering.*
