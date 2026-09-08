# Tommy Booking Support — bronresearch (`tomm`)

> **Stand van zaken 08-09-2026: er is nog geen enkel bericht aangeleverd.** Dit rapport legt
> vast wat er vaststaat over de ontsluiting — het brontype, de route, de padvorm en de
> toegangsvoorwaarden — en laat alles wat de inhoud betreft expliciet open. Er is bewust géén
> schema opgesteld: dat kan pas op een echt bericht, nooit op een beschrijving.

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
wortel voor de scriptkant (`scripts/lib/bronze_target.py`). Bij een lakehouse-Bronze is
`{Bronze Files}` gelijk aan `{lakehouse}/Files`; bij een opslagaccount is het de container.

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
| `{environment}` | `UNKNOWN — needs confirmation`. Dit segment is in dit framework de vestiging, het park of het merk (vergelijk `EnvironmentColumnName`, met waarden als `VestigingId` of `Resort`) — niet dev/prd. Er moet minstens één waarde zijn; zie de valkuil hieronder |
| `{entity}` | `UNKNOWN — needs confirmation`. De berichtsoort. Hangt af van wat de leverancier stuurt en of dat één stroom is of meerdere |
| `incoming` | ligt vast — framework |

**Valkuil bij het kiezen van die twee woorden.** `all` is een gereserveerd woord in de
parameterparser (`parse_source_env_entity_parameter` behandelt `all` als "alle waarden uit de
config"). Een map die zo heet, is later niet meer los aan te spreken.

**Tweede valkuil, en deze faalt stil.** `PossibleEnvironments` moet gevuld zijn. Is die lijst
leeg, dan levert de parser een lege omgevingslijst op, wordt er geen enkele verwerkingsmap
gebouwd, en meldt de run niets: er is dan simpelweg niets te doen. Een bron met een lege
omgevingslijst verwerkt dus nooit iets, zonder foutmelding.

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
doorlopen om erbij te komen, en ziet de buurmappen niet.

> **Gedocumenteerd, niet geverifieerd.** Bovenstaande komt uit Microsoft Learn (*OneLake security
> roles, permissions, and scopes*, geraadpleegd 08-09-2026) en is in geen tenant nagemeten. Er
> bestaat in dit platform **geen script en geen procedure** om zo'n rol in te richten: het is een
> handmatige beheerhandeling, en dat blijft het tot iemand hem automatiseert.

### Wat er verder nodig is

| Voorwaarde | Waarom, en wat het raakt |
|---|---|
| Een Entra-identiteit voor de leverancier in de tenant van de klant | Een app-registratie (dienstidentiteit) of een gastaccount. Zonder identiteit is er niets om recht aan te geven |
| Tenantinstelling *Users can access data stored in OneLake with apps external to Fabric* | Vereist voor toegang tot OneLake buiten Fabric om. Wordt makkelijk over het hoofd gezien |
| Bij een **gastaccount**: de externe-samenwerkingsinstelling op *Guest users have the same access as members (most inclusive)* | Voorwaarde voor het toekennen van een OneLake-beveiligingsrol aan een gast. Dit is een **tenantbrede** instelling, en dus een beveiligingsbeslissing die verder reikt dan deze ene map — een dienstidentiteit vermijdt hem |

### Secrets

Zolang de leverancier zelf schrijft, bewaart het platform **geen enkel credential van hem**: hij
authenticeert met zijn eigen identiteit bij Entra. Er is dus vandaag geen secretnaam nodig.

Verandert de route naar een brievenbus met een tussenstap, dan komt er wel een credential in
beeld en volgt de naam de conventie `{source}-{type}` — nooit een waarde in dit rapport, en
nooit in een gesprek.

## Formaat en codering

`UNKNOWN — needs confirmation` op alle punten: formaat, codering, scheidingsteken, kopregel,
bestandsnaamgeving.

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

`UNKNOWN` — er is nog geen bericht aangeleverd.

Er is bewust geen schema afgeleid uit productbeschrijvingen of publieke documentatie. Een schema
dat als gemeten leest terwijl het geraden is, is schadelijker dan geen schema: de config-builder
bouwt erop verder en een ontbrekende of verkeerd benoemde kolom faalt niet, die blijft leeg.

## Sleutel en watermark

`UNKNOWN` — beide vragen (welke velden een bericht uniek maken, en waaraan je ziet dat een
boeking is gewijzigd) zijn pas op echte berichten te beantwoorden, en horen bovendien bij de
telling die op Bronze wordt gedaan.

Wat nu al vaststaat: de verwerking voegt zelf een `FileName`-kolom toe met het volledige pad van
het bronbestand. Dat geeft altijd een terugvalvolgorde voor ontdubbeling, ook wanneer de bron
zelf geen wijzigingsmoment meestuurt.

## Volume en leveringspatroon

`UNKNOWN — needs confirmation`: frequentie, delta of volledige set, aantal bestanden per
levering, bestandsgrootte, en of alle bestanden verwerkt moeten worden of alleen het laatste.

Er is niets om op te schatten: er is nog geen levering geweest.

## Aansluiting op de general-notebooks

| Punt | Oordeel |
|---|---|
| `push` wordt herkend en de ingestie wordt overgeslagen | werkt |
| Verplaatsen van `incoming/` naar `processing/`, met telcontrole | werkt |
| Archivering na verwerking, ook op een lakehouse | werkt |
| Lezen van de aangeleverde bestanden | **alleen JSON** — zie *Formaat en codering* |
| Afleiden van de omgevingskolom bij een lakehouse-Bronze | **gat** — zie hieronder |

### Gat: `EnvironmentColumnName` klopt niet bij een Bronze-lakehouse

| Feature Needed | Reason | Affected Notebook | Example/Workaround | User Story ID |
|---|---|---|---|---|
| De omgevingswaarde afleiden op een manier die voor beide Bronze-vormen klopt | Het pad heeft bij een lakehouse één segment meer dan bij een opslagaccount | `notebook_ProcessToSilver_Generic_Child.py` (regel 191-196) | Zie hieronder | nog aan te vragen |

De omgevingskolom wordt gevuld met het **vijfde** padsegment van de bestandsnaam:
`element_at(split(col('FileName'), '/'), 5)`. Dat klopt voor een opslagaccount
(`abfss://container@account.../{source}/{env}/…` → segment 5 is de omgeving), maar niet voor een
lakehouse: daar staat er nog een item-segment tussen
(`abfss://workspace@onelake.../{lakehouse}/Files/{source}/{env}/…`), waardoor segment 5 het woord
`Files` is.

**Gevolg:** elke bron van een klant met Bronze in een lakehouse die `EnvironmentColumnName`
gebruikt, krijgt stil de waarde `Files` in die kolom. Geen foutmelding, geen lege waarde — een
verkeerde waarde.

Vastgesteld uit de code en uit de padopbouw in `scripts/lib/bronze_target.py`; niet waargenomen
in een draaiende run. Het raakt deze bron zodra er per vestiging of park wordt aangeleverd en die
code als kolom mee moet.

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

**2. Persoonsgegevens.** Boekingsberichten bevatten vrijwel zeker gastgegevens (naam, adres,
contactgegevens). Drie gevolgen: het eerste voorbeeldbericht hoort niet in een chat of in dit
rapport terecht te komen, het schrijfrecht op de map hoort zo smal mogelijk te zijn, en een
voorbeeld in een later rapport is geredigeerd — veldnamen blijven, waarden gaan eruit.

**3. Een adres bij een leverancier is duur om te wijzigen.** Het adres wijst naar de omgeving die
er vandaag is. Komt er later een productieomgeving bij, dan verandert het adres en moet de
leverancier het opnieuw instellen.

**4. Twee van de segmenten in het adres liggen nog niet vast.** Zolang `{environment}` en
`{entity}` niet gekozen zijn, is er geen volledig adres om door te geven.

## Open vragen / UNKNOWNs

Aan de leverancier:

1. Zetten jullie bestanden neer, of stuurt jullie systeem per boeking een bericht naar een
   webadres dat wij opgeven? *(beslist welke route haalbaar is)*
2. Als het bestanden zijn: kunnen jullie schrijven naar een Microsoft-omgeving waarvoor u zich
   met een Microsoft-identiteit aanmeldt — of alleen naar SFTP, FTP of een deellink?
   *(OneLake kent alleen het eerste)*
3. Kan de inhoud als **JSON** worden aangeleverd? *(alles daarbuiten vraagt bouwwerk)*
4. Welke berichtsoorten stuurt u — alleen boekingen, of ook wijzigingen, annuleringen,
   gastgegevens? *(bepaalt het laatste padsegment)*
5. Levert u per vestiging of park apart aan, of alles in één stroom? *(bepaalt het
   omgevingssegment)*
6. Hoe vaak wordt er geleverd, en is dat steeds de volledige set of alleen wat is gewijzigd?
7. Hoe heten de bestanden, en welke codering hebben ze?
8. Wie is de contactpersoon voor deze koppeling?

Aan onze kant:

9. Welke woorden komen in `{environment}` en `{entity}` te staan?
10. Wie richt de Entra-identiteit en het mapgebonden schrijfrecht in, en wanneer? Er is geen
    script voor; het is een handmatige beheerhandeling.
11. Wordt het een dienstidentiteit of een gastaccount? Een gast vraagt een tenantbrede
    instelling; een dienstidentiteit niet.

**Klaar om verder te gaan is deze bron pas na twee dingen:** een antwoord op vraag 1 tot en met 3,
en één echt aangeleverd bericht. Voor dat bericht er is, wordt er geen schema opgesteld.
