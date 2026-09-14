# Verkoopdoelen per verkoper — bronresearch (`sales-targets`)

> **Stand van zaken 14-09-2026.** Er is één bestand, het is volledig gelezen, en het staat nog
> nergens in een Fabric-omgeving: het ligt in de demodata van deze codebase. Alles wat hieronder
> over formaat, kolommen en sleutel staat, is op dát bestand gemeten — niet op een levering. Wat
> nog niet vaststaat is het ontvangstadres, het leveringsritme en of een volgende levering de
> vorige vervangt of aanvult; die staan als open vraag.

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
| Gemeten op | 14-09-2026, met `pandas.read_csv(sep=None, engine="python")`, `csv.reader` en een byte-inspectie van het hele bestand |

**Wat deze meting wel en niet bewijst:**

| Wel | Niet |
|---|---|
| Hoe dít bestand gelezen moet worden: scheidingsteken, codering, kopregel, kolommen, typen | Dat een volgende levering dezelfde vorm heeft |
| Dat de kandidaatsleutel over alle 120 regels uniek is — een telling, geen schatting | Dat de sleutel uniek blijft over meerdere leveringen heen |
| Dat het bestand geen lege waarden, geen aanhalingstekens en geen afwijkende regels bevat | Dat de aanleveraar dat volhoudt |

## Leveringstype en route

### Leveringstype

Eén CSV-bestand, met de hand neergezet, periodiek vervangen of aangevuld. Er staat geen ophaalstap
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

### Wat vastligt en wat nog gekozen moet worden

| Segment | Status |
|---|---|
| `{Bronze Files}` | ligt vast — volgt uit het klantprofiel |
| `{source}` | ligt vast — `sales-targets` |
| `{environment}` | **`UNKNOWN — needs confirmation`.** Eén vaste waarde volstaat: er wordt niet per vestiging of per aanleveraar gescheiden. Welke waarde dat is, is een keuze |
| `{entity}` | **`UNKNOWN — needs confirmation`.** Eén map, want één soort bestand. De naam is een keuze; de conventie voor entitynamen is snake_case, Engels, enkelvoud |
| `incoming` | ligt vast — framework |

**Waarom dit niet wordt ingevuld.** Elk segment wordt een deel van het adres waar iemand zijn
bestand naartoe brengt. Een afgeleide of een werknaam die eenmaal in een listing staat, leest na een
paar weken als een afspraak — hij is concreet, hij bestaat, en er staan bestanden in. De keuze hoort
vóór het aanmaken gemaakt te worden, niet erna.

**`all` kan geen mapnaam zijn.** Dat woord is in de parameterverwerking gereserveerd voor "alle
waarden uit de config"; een map die zo heet is later niet los aan te spreken. Het aanmaakcommando
weigert die naam.

### De map aanmaken — wat er wel en niet is geregeld

```bash
python scripts/bronze_stage.py --profile {profile} --source sales-targets \
  --action prepare --env {env} --entity {entity} [--dry-run]
```

Het maakt **alleen** `incoming/` aan, leest het pad terug voordat het het adres afdrukt, en
verandert niets wanneer het pad al bestaat. `--env` en `--entity` zijn verplicht en worden nooit
afgeleid: ze worden een segment van het adres.

**Wat het uitdrukkelijk níet doet: rechten toekennen.** De map aanmaken opent hem voor niemand. Of
er een recht nodig is, hangt aan wie het bestand straks neerzet:

| Wie levert aan | Wat er nodig is |
|---|---|
| Iemand die al toegang heeft tot de werkruimte | niets extra's — de map aanmaken volstaat |
| Een partij van buiten | een Entra-identiteit plus een OneLake-beveiligingsrol op de bronmap. **Handmatig beheerwerk waarvoor geen script bestaat** |

De volgorde is niet omkeerbaar: **eerst de map, dan het recht** — een recht kan alleen worden
toegekend op een map die al bestaat.

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

Alles hieronder is gemeten op het hele bestand, niet op de eerste regels.

| Eigenschap | Waarde | Hoe vastgesteld |
|---|---|---|
| Formaat | CSV, plat — geen geneste structuren | volledige parse |
| Scheidingsteken | `,` (komma) | 726 komma's over 121 regels = exact 6 per regel; `csv.Sniffer` bevestigt de komma |
| Codering | zuiver ASCII — dus ook geldig UTF-8 | 0 bytes boven 127 in het hele bestand |
| Byte order mark | geen | eerste bytes gecontroleerd |
| Regeleinde | CRLF (`\r\n`), op alle 121 regels, ook de laatste | byte-telling: 121 × CRLF, 0 losse LF |
| Kopregel | ja, één, met de kolomnamen | eerste regel |
| Aanhalingstekens | geen, nergens in het bestand | 0 voorkomens van `"` |
| Velden per regel | 7 op **elke** regel, kopregel inbegrepen | verdeling van veldaantallen: `{7: 121}` |
| Lege waarden | geen, in geen enkele kolom | telling per kolom |
| Overtollige spaties | geen, in geen enkele waarde | vergelijking met de getrimde waarde |

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

Zeven kolommen, in deze volgorde. Het schema wordt bij het lezen **opgelegd** (sectie 3) en op
kopnaam gekoppeld; een kolom die in de kopregel ontbreekt levert `null` op in plaats van te
verdwijnen.

| # | Kolomnaam | Waargenomen vorm | Spark-type | Nullable | Voorbeeldwaarden |
|---|---|---|---|---|---|
| 1 | `PeriodStart` | `yyyy-MM-dd`, altijd 10 tekens, altijd de 1e van de maand | `DateType` | Nee | `2026-01-01`, `2026-12-01` |
| 2 | `Year` | 4 cijfers | `IntegerType` | Nee | `2026` |
| 3 | `Month` | 1-2 cijfers, 1 t/m 12 | `IntegerType` | Nee | `1`, `12` |
| 4 | `SalespersonId` | 1-2 cijfers, geen voorloopnullen | `IntegerType` | Nee | `2`, `20` |
| 5 | `Salesperson` | tekst, 9-18 tekens, twee woorden (voornaam + achternaam), alleen letters en één spatie | `StringType` | Nee | REDACTED — persoonsnamen |
| 6 | `RevenueTarget` | 6 cijfers, geen scheidingsteken, geen decimalen, geen negatieve waarden | `IntegerType` (zie risico 5) | Nee | `458000`, `707000` |
| 7 | `OrderTarget` | 3 cijfers, geen decimalen | `IntegerType` | Nee | `160`, `250` |

**De namen in kolom 5 zijn uit dit rapport weggelaten en niet uit de data.** Bronze houdt de
levering zoals hij binnenkomt; dit rapport staat in twee git-repo's en blijft daar.

**Waargenomen waardenbereik** (over alle 120 regels — beschrijvend, de definitieve telling doet
config-builder op Bronze):

| Kolom | Bereik | Aantal verschillende waarden |
|---|---|---|
| `PeriodStart` | `2026-01-01` t/m `2026-12-01` | 12 |
| `Year` | 2026 | 1 |
| `Month` | 1 t/m 12 | 12 |
| `SalespersonId` | 2 t/m 20, niet aaneengesloten | 10 |
| `RevenueTarget` | 440.000 t/m 707.000 | 86 |
| `OrderTarget` | 150 t/m 250 | 11 |

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
  van het pad; met één vaste omgevingsaanduiding levert dat een kolom op met overal dezelfde
  waarde. Laat hem `null`.

## Sleutel en watermark

**Sleutel: `SalespersonId` + `PeriodStart`.**

| Kandidaat | Dubbelen over alle 120 regels |
|---|---|
| `SalespersonId` + `PeriodStart` | **0** |
| `SalespersonId` + `Year` + `Month` | **0** — gelijkwaardig, want de maandonderdelen zijn afleidbaar uit de datum |
| `PeriodStart` alleen | 108 |
| `SalespersonId` alleen | 110 |

Dit is een telling over de volledige inhoud van het bestand, geen steekproef. Wat hij **niet**
dekt: uniciteit over meerdere leveringen heen. Levert een volgend bestand dezelfde maanden opnieuw,
dan staat dezelfde sleutel twee keer in Bronze en moet de ontdubbeling in sectie 5 hem opvangen.

**Watermark: geen.** Er is geen kolom die meebeweegt met een wijziging — geen `Modified`, geen
versie, geen tijdstempel. `WatermarkType` blijft dus `null`, en dat is voor een levering de normale
uitkomst: een bestand is verwerkt zodra het naar `processing/` is verplaatst en daarna
gearchiveerd. Die bestandslevenscyclus ís het watermark.

**Gevolg voor ontdubbeling:** komt dezelfde maand in twee leveringen voor, dan is er in de data
niets dat zegt welke de nieuwste is. De enige ordening die overblijft is `FileName` — en dus het
moment van landen, niet het moment van opstellen.

## Volume en leveringspatroon

| Punt | Waarde |
|---|---|
| Aantal bestanden gezien | 1 |
| Omvang per bestand | 5,6 KB / 120 regels |
| Volumeverwachting | verwaarloosbaar — ook tien jaar aan leveringen blijft onder een megabyte |
| Bestandsnaam | `sales-targets-2026.csv`. Of `sales-targets-{jaar}.csv` het patroon is, is `UNKNOWN`: er is één bestand gezien, en één voorbeeld is geen patroon |
| Frequentie | `UNKNOWN — needs confirmation` |
| Delta of volledige set | `UNKNOWN — needs confirmation` |
| Alle bestanden verwerken of alleen het laatste | `UNKNOWN — needs confirmation` |

Het framework leest **alles** wat in `incoming/` staat. Zolang de drie vragen hierboven openstaan,
is niet vast te stellen of dat de bedoelde uitkomst is.

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
| Schrijfrecht toekennen aan een partij van buiten | **geen script** — handmatige beheerhandeling |

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
duizendtalscheiding. Een volgende levering die `458.000` of `458000,50` schrijft, past niet in een
geheel getal en komt binnen als `null` — opnieuw zonder fout. De typekeuze voor kolom 6 is dus een
beslissing met een gevolg, geen formaliteit.

**5. Persoonsgegevens.** `Salesperson` bevat namen. Bronze houdt de levering zoals hij binnenkomt,
dus iedereen die die map inspecteert werkt met persoonsgegevens. De inspectiescripts maskeren
standaard; die maskering uitzetten hoort een bewuste handeling te blijven. In dit rapport zijn de
waarden weggelaten vóór het werd weggeschreven.

**6. Twee bronnen voor dezelfde maand.** `PeriodStart` enerzijds en `Year`/`Month` anderzijds zeggen
hetzelfde. In dit bestand komen ze op elke regel overeen; in een volgend bestand kan dat uiteenlopen
zonder dat iets dat opmerkt. Wie beide kolommen naar Silver meeneemt, neemt die mogelijkheid mee.

**7. Een adres is duur om te wijzigen.** Zodra het ontvangstadres is doorgegeven aan degene die
levert, kost elke wijziging eraan een tweede ronde langs die persoon. Komt er later een
productieomgeving bij, dan verandert het adres en moet het opnieuw worden ingesteld.

## Open vragen / UNKNOWNs

Alle vijf liggen bij de opdrachtgever, niet bij een leverancier — hij bepaalt zelf hoe hij aanlevert.

1. **[onbeantwoord]** Op welk adres komt het bestand te staan? Concreet: welke waarde krijgt het
   omgevingssegment, en hoe heet de map voor de bestandssoort? *(beide worden een segment van het
   adres; er is er precies één van elk nodig)*
2. **[onbeantwoord]** Wat bevat een volgende levering — de volledige set opnieuw, alleen de
   gewijzigde maanden, of een nieuw jaar naast het vorige? *(bepaalt of een levering vervangt of
   aanvult, en daarmee de ontdubbeling)*
3. **[onbeantwoord]** Hoe vaak wordt er geleverd? *(bepaalt de versheidsverwachting en of alle
   bestanden of alleen het laatste verwerkt moeten worden)*
4. **[onbeantwoord]** Wie zet het bestand neer — iemand die al toegang heeft tot de werkruimte, of
   een partij van buiten? *(alleen in het tweede geval is er een identiteit en een schrijfrecht
   nodig, en dat is handmatig beheerwerk)*
5. **[onbeantwoord]** Is `sales-targets-{jaar}.csv` de bedoelde naamgeving? *(alleen van belang
   wanneer de extensie ooit afwijkt; `*.csv` is het standaardfilter)*

---

*Bronresearch uitgevoerd 14-09-2026. Het bestand is volledig gelezen; het formaat, het
kolomschema en de sleutel zijn gemeten. Het ontvangstadres en het leveringspatroon zijn dat niet.*
