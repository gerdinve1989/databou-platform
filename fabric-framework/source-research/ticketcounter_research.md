# Ticketcounter API-onderzoek

researched_at: 2026-07-17
checked_at: 2026-08-28
checked_by: research agent (research-source-change-check v1.1, samengevoegd met het bestaande rapport)
source_type: api
overall_verdict: UNKNOWN — v1 is CURRENT, v2 kon niet live worden afgetast (authenticatie geweigerd)

Onderzoek naar **TC.Tickets.API**. Er draaien twee generaties naast elkaar: een **legacy v1**
`Statistics`-API op `api.ticketcounter.net`, waarop de bestaande connector produceert, en de
**v2**-API op `apiv2.ticketcounter.eu`. Dit rapport documenteert beide en de delta die een
migratie v1 naar v2 moet afdekken.

## Inhoudsopgave

| Sectie | Omschrijving |
|---------|-------------|
| [Aanleiding en oordeel](#aanleiding-en-oordeel) | De leveranciersmelding, het JA/NEE/JA-MITS en de mitsen |
| [Change-check 2026-08-28](#change-check-2026-08-28) | Wat er per dimensie is afgetast en wat eruit kwam |
| [Twee kopieen van dit rapport](#twee-kopieen-van-dit-rapport) | Divergentie tussen clientrepo en platformregister |
| [TypeSource](#typesource) | Bevestigd bronprotocol |
| [Overzicht](#overzicht) | Wat v1 en v2 zijn en hoe ze zijn onderzocht |
| [Huidige versie per entiteit](#huidige-versie-per-entiteit-gemeten) | De v1-baseline, live gemeten |
| [Discount Name](#discount-name--de-leveranciersmelding) | Exacte veldnaam, type, nullability, vulgraad |
| [Delta v1 en v2 voor sold-tickets](#delta-v1-en-v2-voor-sold-tickets) | Zes onderwerpen, elk breaking of niet-breaking |
| [Authenticatie](#authenticatie) | OAuth2, secret-namen, token-endpoints, gemeten uitkomsten |
| [Verbinding](#verbinding) | BaseUrl, rate-limit-vertraging, headers |
| [Uitfasering van v1](#uitfasering-van-v1) | Wat er wel en niet over te vinden is |
| [Gemengd draaien](#gemengd-draaien-een-entiteit-op-v2-de-rest-op-v1) | Kan een entiteit vooruit? |
| [Entiteitenoverzicht](#entiteitenoverzicht) | Endpoints binnen en buiten scope |
| [Contract van de request body](#ticketcounter-v2--contract-van-de-request-body) | Filters, offset/limit en de datumbereik-enum |
| [Paginering en ingestie per entiteit](#paginering-en-ingestie-per-entiteit) | Strategie en configuratiewaarden per entiteit |
| [Rate limits](#rate-limits) | Gemeten voor v1, ongedocumenteerd voor v2 |
| [Velden en voorbeeld-JSON per entiteit](#velden-en-voorbeeld-json-per-entiteit) | Links naar veldencatalogi |
| [Belangrijkste datakenmerken per entiteit](#belangrijkste-datakenmerken-per-entiteit) | Sleutels, watermarks, volumes |
| [Impact van de migratie v1 naar v2](#ticketcounter--impact-van-de-migratie-v1-naar-v2) | Wat breekt en wat blijft |
| [Migratieplan](#migratieplan) | Genummerde stappen plus terugvalpad |
| [Benodigde uitbreidingen aan general-notebooks](#benodigde-uitbreidingen-aan-general-notebooks) | Gevonden hiaten in het framework |
| [Openstaande vragen / UNKNOWNs](#openstaande-vragen--unknowns) | Alles wat niet is geverifieerd |
| [Vragen aan de leverancier](#vragen-aan-de-leverancier) | Wat alleen de leverancier kan beantwoorden |
| [Verzamel-endpoints v2 (dimensies en referentie)](#verzamel-endpoints-v2--dimensie--en-referentiebronnen) | De 21 endpoints die een verzameling teruggeven, buiten de 5 Statistics-feiten |

## Aanleiding en oordeel

**De melding van de leverancier:** *"Discount Name is toegevoegd aan de response van het
sold-tickets endpoint. Dit is alleen toegevoegd aan de API V2. De aanpassing is inmiddels
doorgevoerd."*

**De vraag:** kunnen we over naar API v2?

### Oordeel: JA-MITS

De melding klopt en is verifieerbaar in het gepubliceerde contract. v2 is voor `sold-tickets`
inhoudelijk een superset van v1 op twee velden na. Maar de overstap is **geen
configuratiewijziging**: hij vraagt nieuwe inloggegevens, een uitbreiding van het
ingestieframework en een herschrijving van schema en transformaties. Zolang die drie niet zijn
geregeld, is het antwoord op *"kunnen we nu over?"* nee.

| # | Mits | Status | Wie lost het op |
|---|---|---|---|
| 1 | Nieuwe v2-clientinloggegevens per omgeving (grant `client_credentials`) | **Blokkade — gemeten `invalid_client`** | Leverancier levert; de klant voert ze in via het portalformulier |
| 2 | Framework kan een REST-`POST` met JSON-filterbody sturen | **Blokkade — bestaat niet** | User story op `general-notebooks` |
| 3 | OAuth2-`Scope` is configureerbaar | **Blokkade indien v2 de scope verplicht stelt — onbevestigd** | Kolom in het configuratieschema plus de generator |
| 4 | `03_schema.py` en `04_transforms.py` herschrijven (PascalCase naar camelCase) | Werk, geen blokkade | config-builder |
| 5 | Besluit over de twee velden die v2 niet meer levert | Besluit, geen blokkade | Gegevenseigenaar |

**Bijvangst die het besluit kleurt:** v1 dwingt een **harde afkoeltijd van 120 seconden per
endpoint** af (gemeten, HTTP 409). v2 documenteert geen enkele rate limit. Als dat klopt, is de
winst van de migratie niet het ene kortingsveld maar de doorlooptijd van elke herlading. Dat is
niet te bevestigen zonder werkende v2-inloggegevens.

## Change-check 2026-08-28

Alle vijf v1-endpoints zijn live afgetast; het v2-contract is opnieuw opgehaald en vergeleken met
het rapport van 2026-07-17. v2 zelf kon niet worden aangeroepen.

| Dimensie | Oordeel | Detail |
|---|---|---|
| v1 — authenticatie | `UNCHANGED` | `POST https://api.ticketcounter.net/token`, grant `refresh_token`, token verkregen |
| v1 — verbinding | `UNCHANGED` | Alle vijf gedocumenteerde `url_path`-waarden geven HTTP 200 |
| v1 — velden, alle vijf entiteiten | `UNCHANGED` | Recordsleutels en veldenlijsten komen overeen met de configuratie |
| v1 — paginering | `UNCHANGED` | `offset`/`limit` in de query-string; `ResultCount` = rijen op deze pagina (gemeten) |
| v1 — rate limits | `UNCHANGED` maar **nu gemeten** | HTTP 409 `"You may only perform this action every 120 seconds."` — per endpoint, niet per token |
| v2 — contract `sold-tickets` | `FIELD_ADDED` | `discountName` erbij; 71 naar 72 velden; niets verdwenen |
| v2 — contract `sold-subscriptions` | `FIELD_ADDED` | `discountName` erbij; 46 naar 47 velden; niets verdwenen |
| v2 — contract `baskets` / `scans` / `cancellations` | `UNCHANGED` | Identiek aan het contract van 2026-07-17 |
| v2 — authenticatie | `UNKNOWN` | HTTP 400 `invalid_client` op test en productie, met en zonder scope, beide omgevingen |
| v2 — voorbeeldresponse, vulgraad, `resultCount`-semantiek, rate limits | `UNKNOWN` | Geblokkeerd door de authenticatie |

**Totaaloordeel: `UNKNOWN`.** De bron waarop vandaag wordt geproduceerd (v1) is `CURRENT`; de
doelversie (v2) is op het contract `REVIEW` — uitsluitend toevoegende wijzigingen — maar live
`UNKNOWN`. Volgens de ernstvolgorde `STALE > UNKNOWN > REVIEW > CURRENT` wint `UNKNOWN`. Dat
betekent escaleren naar de gebruiker, niet doorstromen naar een configuratiestap.

## Twee kopieen van dit rapport

Dit rapport bestond op **een** van de twee plekken, en dat is zelf een bevinding:

| Waar | Stand voor deze run |
|---|---|
| Clientrepo (`client-outputs/ticketcounter_research.md`) | **Aanwezig**, bijgewerkt 2026-07-17T15:25:37Z |
| Platformrepo (`fabric-framework/source-research/ticketcounter_research.md`) | **Afwezig** — `--action get --from platform` geeft `NOT_FOUND` |
| Catalogusrij `source_research` | **Afwezig** — `--action list` toont alleen `dip`, `hubspot` en `shopify` |

De clientkopie was dus de enige die bestond en is als uitgangspunt genomen; er is niets
overschreven. Waar deze run een eerdere bevinding tegenspreekt, staat dat in de tekst met de datum
erbij. Waar een bevinding uit 2026-07-17 deze run niet opnieuw kon worden gecontroleerd — alles
wat een werkend v2-token vraagt — blijft die staan, gemarkeerd als **ongeverifieerd**.

Een eerdere bevinding is door deze run **achterhaald** en hier gecorrigeerd: het rapport van
2026-07-17 stelde dat de `POST`-tak in de API-client onbereikbare dode code was. Dat klopt niet
meer; zie [Benodigde uitbreidingen aan general-notebooks](#benodigde-uitbreidingen-aan-general-notebooks).

## TypeSource

- **Bevestigd:** `api` (REST/JSON over HTTPS), voor beide generaties.
- **Door intake afgeleid:** `api` — hetzelfde, geen correctie nodig.

## Overzicht

### v1 — de generatie waarop vandaag wordt geproduceerd

- **Host:** `https://api.ticketcounter.net`
- **Vorm:** `GET` met query-string-parameters; respons JSON met PascalCase-velden.
- **Documentatie: geen.** `/swagger/v1/swagger.json`, `/swagger/index.html` en `/help` geven alle
  drie HTTP 404; de hostwortel redirect naar de marketingsite. Er is dus geen publiek contract,
  geen changelog en geen statuspagina voor deze generatie.
- **Bewijsbasis:** dit hoofdstuk is **live gemeten** op 2026-08-28 — alle vijf endpoints
  aangeroepen, responses vastgelegd.

### v2 — de doelgeneratie

- **Titel:** `TC.Tickets.API`, versie `v2` (OpenAPI 3.0.4).
- **De spec is openbaar, geen login vereist:**
  - test: `https://apiv2test.ticketcounter.eu/swagger/v2/swagger.json`
  - prod: `https://apiv2.ticketcounter.eu/swagger/v2/swagger.json`
- **Omvang:** 148 paden, 352 schemadefinities, verdeeld over 30 taggroepen. Alleen de vijf
  `Statistics`-endpoints vallen binnen de scope.
- **Bewijsbasis: volledig afgeleid van het gepubliceerde OpenAPI-contract**, opnieuw opgehaald op
  2026-08-28. Er is nog steeds **geen live call** gedaan — de inloggegevens worden geweigerd. Elk
  type hieronder is een door het contract gedeclareerd type, geen waargenomen type.
- **Grootste structurele wijziging ten opzichte van v1:** de Statistics-endpoints zijn **POST met
  een JSON-body**, waar v1 GET met query-string-parameters gebruikt.

> **Pas op met het woord "v1" bij deze leverancier.** De Swagger-UI op de v2-host publiceert twee
> specs naast elkaar: `TC.Tickets.API V1` (`/swagger/v1/swagger.json`) en `TC.Tickets.API V2`. Die
> "V1" is **niet** de legacy Statistics-API. Hij telt 14 paden — `Basket/{basketKey}/changetimeslot`,
> `Heartbeat`, `OfflineModule/*`, `Partner/depots`, `Reservation/*`, `ShopTranslation` — en **geen
> enkel** `Statistics`-pad. De legacy Statistics-API op `api.ticketcounter.net` is een aparte,
> ongedocumenteerde dienst. Dat onderscheid bepaalt hoe je een uitfaseringsmededeling van de
> leverancier moet lezen: "v1 gaat uit" kan over twee verschillende dingen gaan.

## Huidige versie per entiteit (gemeten)

De vijf entiteiten die vandaag draaien, met het geconfigureerde `url_path` en wat de bron er op
2026-08-28 daadwerkelijk op teruggaf. Venster `fromDate=2026-08-01`, `toDate=2026-08-07`
(`ticket_scans`: `toDate=2026-08-03`), `offset=0`, `limit=2`. Alle vijf: HTTP 200.

| Entiteit | `url_path` (v1, in gebruik) | Recordsleutel gemeten | Velden per record | v2-tegenhanger |
|---|---|---|---|---|
| `sold_tickets` | `api/v1/statistics/soldtickets/nl-NL` | `SoldTicketsInfo` | 65 | `POST api/v2/Statistics/sold-tickets` → `soldTickets` |
| `baskets` | `api/v1/statistics/baskets` | `Baskets` | 15 | `POST api/v2/Statistics/baskets` → `baskets` |
| `ticket_scans` | `api/v1/statistics/ticketScans/nl-NL` | `TicketScanInfo` | 44 | `POST api/v2/Statistics/scans` → `scans` |
| `sold_subscriptions` | `api/v1/statistics/soldsubscriptions/nl-NL` | `SoldSubscriptionsInfo` | 42 | `POST api/v2/Statistics/sold-subscriptions` → `soldSubscriptions` |
| `cancellations` | `api/v1/statistics/cancellations/nl-NL` | `Cancellations` | 9 | `POST api/v2/Statistics/cancellations` → `cancellations` |

De recordsleutel verschilt per entiteit en volgt geen patroon: twee entiteiten dragen het
achtervoegsel `Info` (`SoldTicketsInfo`, `SoldSubscriptionsInfo`), een het enkelvoud daarvan
(`TicketScanInfo`), en twee het kale meervoud (`Baskets`, `Cancellations`). Wie ze in v2 uit de
oude configuratie overneemt, zit er op alle vijf naast — daar zijn ze allemaal camelCase-meervoud.

**Responsomhulsel v1, identiek voor alle vijf:** `Offset`, `ResultCount`, `Succeeded`,
`ErrorMessage`, `IsRedirect`, `RedirectUrl`, `DisplayError`. Er is **geen** `ErrorCode`; v2 voegt
dat veld toe.

**Paginering v1, gemeten op `sold_tickets`:**

| Aanroep | `ResultCount` | `Offset` in de respons | Rijen |
|---|---|---|---|
| `offset=0&limit=3` | 3 | 3 | 3 |
| `offset=0&limit=2` | 2 | 2 | 2 |
| `offset=2&limit=2` | 2 | 4 | 2, met andere `TicketCode`-waarden dan de eerste pagina |

`ResultCount` telt dus de rijen **op deze pagina**, niet het totaal — precies wat de offset-lus van
het framework verwacht, want die stopt zodra `ResultCount < PageSize`. `Offset` in de respons is de
*volgende* offset. Voor v2 is deze semantiek **niet gedocumenteerd** en niet te meten; zie
[Openstaande vragen](#openstaande-vragen--unknowns).

## Discount Name — de leveranciersmelding

**De melding klopt.** Het veld staat in het gepubliceerde v2-contract en bestaat niet in v1.

| Eigenschap | Waarde | Bewijs |
|---|---|---|
| Exacte veldnaam | `discountName` | contract, letterlijk |
| JSON-type | `string` | `{"type": "string"}` |
| Nullability | **nullable** | `"nullable": true` |
| Omschrijving in het contract | `Name of the discount which was used, if any` | contract |
| Aanwezig op | `TC.Common.Models.Statistics.SoldTicketsInfo` **en** `TC.Common.Models.Statistics.SoldSubscriptionsInfo` | contract |
| Aanwezig in v1 | **Nee** — v1 kent geen enkel kortingsveld, ook `DiscountCode` niet | live gemeten |
| Gemeten vulgraad | **NIET GEMETEN — zie hieronder** | — |

**Opgevraagde URL:** `https://apiv2.ticketcounter.eu/swagger/v2/swagger.json`, opgehaald op
2026-08-28, HTTP 200, 759 479 bytes. De testhost
`https://apiv2test.ticketcounter.eu/swagger/v2/swagger.json` geeft dezelfde inhoud (759 487 bytes),
dus test en productie dragen hetzelfde contract.

**Vergelijking met het rapport van 2026-07-17.** Dat rapport legde 71 velden vast voor
`SoldTicketsInfo` en 46 voor `SoldSubscriptionsInfo`. Het contract van vandaag telt er 72 en 47.
Het verschil is op beide entiteiten **precies een veld, en dat veld is `discountName`**. Er is
niets verdwenen en er is niets van type veranderd. `baskets`, `scans` en `cancellations` zijn
veld-voor-veld identiek aan 2026-07-17. Dat maakt de leveranciersmelding niet alleen plausibel maar
verifieerbaar: de wijziging is precies wat is aangekondigd, niet meer en niet minder.

> **De vulgraad is niet gemeten, en dat is een gat in dit rapport.** Een vulgraad vraagt een echte
> respons over een concreet datumvenster, en elke tokenaanvraag op v2 wordt geweigerd; zie
> [Authenticatie](#authenticatie). Er is **niets geschat en niets verzonnen**. Wat het contract wel
> zegt — `nullable: true`, "if any" — maakt aannemelijk dat het veld alleen gevuld is op regels met
> een korting, dus een lage vulgraad is te verwachten en zegt op zichzelf niets over de juistheid
> van het veld. Zodra er v2-inloggegevens zijn, is dit een enkele call:
> `POST /api/v2/Statistics/sold-tickets` met body
> `{"fromDate":"2026-08-01T00:00:00Z","toDate":"2026-08-07T23:59:59Z","excludeContactInfo":true,"limit":1000,"offset":0}`,
> en daarna tellen hoeveel van de teruggegeven rijen een niet-lege `discountName` hebben.

**Let op de businesswaarde.** `discountName` is een *naam*, geen sleutel. Het contract levert
daarnaast `discountCode`, ook alleen in v2. De referentiebronnen erachter zijn
`GET /api/v2/DiscountReasons` en de `Discounts`-endpoints. Het contract kent bovendien een enum
`DiscountVersionEnum` met de waarden `V1 (legacy)`, `V2` en `Both`. Dat gaat over twee generaties
**kortingscodes in het product**, niet over API-versies — een naamsgelijkenis die in gesprekken met
de leverancier makkelijk verwarring geeft.

## Delta v1 en v2 voor sold-tickets

Zes onderwerpen, elk met een uitspraak en een label. "Breaking" betekent hier: de bestaande
configuratie of code produceert na de overstap een ander resultaat of een fout, en moet dus worden
aangepast.

| # | Onderwerp | v1 (gemeten 2026-08-28) | v2 (contract 2026-08-28) | Label |
|---|---|---|---|---|
| 1 | **Veldnamen en -typen** | 65 velden, PascalCase | 72 velden, camelCase | **BREAKING** |
| 2 | **Wrapper-key** | `SoldTicketsInfo`; omhulsel `Offset`, `ResultCount`, `Succeeded`, `ErrorMessage`, `IsRedirect`, `RedirectUrl`, `DisplayError` | `soldTickets`; omhulsel `offset`, `resultCount`, `succeeded`, `errorMessage`, `isRedirect`, `redirectUrl`, `displayError` plus **`errorCode`** | **BREAKING** |
| 3 | **Paginering** | `offset` en `limit` als query-parameters; `ResultCount` = rijen op deze pagina | `offset` en `limit` **in de JSON-body**; `resultCount` in het omhulsel; `limit` maximaal 100 000, standaard 1000 | **BREAKING** |
| 4 | **Datumfilterparameters** | `fromDate` / `toDate` als query-parameters, formaat `%Y-%m-%d` | `fromDate` / `toDate` **in de body**, formaat `date-time`; erbij: `modifiedFrom` / `modifiedTo` en `dateRangeType` | **BREAKING** |
| 5 | **Authenticatie** | `POST https://api.ticketcounter.net/token`, grant `refresh_token`, geen scope, drie secrets | `POST https://apiv2.ticketcounter.eu/connect/token`, grant `client_credentials`, scope `TC.Tickets.API`, twee secrets | **BREAKING** |
| 6 | **Rate limits** | **Harde afkoeltijd van 120 s per endpoint**, afgedwongen met HTTP 409 | Niets gedocumenteerd; geen `429` gedeclareerd op enig Statistics-endpoint | **NIET-BREAKING** |

### 1. Veldnamen en -typen — BREAKING

Van de 63 velden die beide generaties delen is er **geen enkele** met dezelfde spelling: v1 is
PascalCase (`TicketCode`, `SaleDate`), v2 is camelCase (`ticketCode`, `saleDate`). Elke verwijzing
in `03_schema.py` en `04_transforms.py` breekt.

**Twee velden verdwijnen.** v2 heeft er geen equivalent voor, ook niet onder een andere naam:

| v1-veld | v2 | Gevolg |
|---|---|---|
| `BuyingPrice` | bestaat niet | Inkoopprijs per plaats vervalt |
| `CountryName` | alleen `countryCode` | Landnaam wordt landcode; wie de naam wil, decodeert zelf |

**Negen velden komen erbij:** `capacityNames`, `countryCode`, `creationDate`, `discountCode`,
`discountName`, `eventName`, `modificationDate`, `performerName`, `priceTypeName`.

`creationDate` en `modificationDate` zijn daarvan de belangrijkste. v1 draagt **geen enkel
wijzigingsveld**, waardoor incrementeel laden nu volledig op het aanvraagvenster leunt. Met
`modificationDate` in de payload en `modifiedFrom` / `modifiedTo` als filter wordt echte
change-data capture mogelijk. Dat is een grotere verbetering dan het kortingsveld waar de melding
over gaat.

**Typen.** Het contract declareert `saleDate`, `validFrom`, `validTo`, `cancelDate`,
`confirmedDate`, `capacityDate`, `creationDate` en `modificationDate` als `string` met formaat
`date-time`. v1 levert diezelfde velden ook als JSON-string. Op de draad is dat dus geen
typewijziging; de declaratie is alleen preciezer geworden. `nrOfSeats` is in beide een integer;
`price`, `totalPrice` en `originalPrice` zijn in beide een getal. **Niet nagemeten:** of v2
dezelfde tekstuele datumopmaak gebruikt als v1, met of zonder tijdzone-achtervoegsel. Dat bepaalt
of een `cast("timestamp")` in de transformatie ongewijzigd kan blijven, en is pas op een echte
respons te zien.

### 2. Wrapper-key — BREAKING

`Output.RecordKey` gaat van `SoldTicketsInfo` naar `soldTickets`, en `Pagination.ResultCountKey`
van `ResultCount` naar `resultCount`. Beide zijn configuratiewaarden, dus de reparatie is klein.
Maar zonder die wijziging vindt de extractor geen records en geen paginateller, en meldt de run
"0 rijen" in plaats van een fout. Dat is precies het soort stille afwijking waarvoor deze delta
bestaat. `errorCode` is nieuw in het omhulsel en zuiver additief: het framework leest het niet.

### 3. Paginering — BREAKING

Het *model* verandert niet: offset-paginering met een paginagrootte, met datumchunking eromheen.
`strategy: chunk_offset`, `OffsetParam: offset`, `PageSizeParam: limit`, `PageSize: 10000` en
`LoopChunks.ChunkSize: 30` kunnen alle vijf blijven staan. Wat verandert is het *transport*: de
parameters moeten in de JSON-body in plaats van in de query-string, en dat kan het framework niet.
De v2-grens van 100 000 rijen per call ligt ruim boven de gebruikte 10 000.

**Risico dat pas op een echte respons zichtbaar wordt.** Het contract geeft `resultCount` geen
omschrijving. De offset-lus stopt zodra `resultCount < PageSize`. Is `resultCount` in v2 het
*totaal aantal gevonden rijen* in plaats van *het aantal op deze pagina*, dan stopt die lus nooit
op tijd en loopt hij door tot de laatste pagina leeg is — of, erger, tot hij dezelfde pagina blijft
herhalen. In v1 is het gemeten en is het de paginatelling. Dat is een sterke aanwijzing voor v2,
geen bewijs.

### 4. Datumfilterparameters — BREAKING

`fromDate` en `toDate` blijven bestaan en houden hun betekenis als vensterbegrenzing, maar
verhuizen naar de body en gaan van `%Y-%m-%d` naar `date-time`. De overlap van 2 dagen en de chunks
van 30 dagen kunnen ongewijzigd blijven.

Nieuw is `dateRangeType`, een integer-enum: `0 = ConfirmationDate` (**standaard**),
`1 = CreationDate`, `2 = VisitDate`. **Onbekend en belangrijk:** op welke datum `fromDate` en
`toDate` in v1 filteren. Is dat niet de bevestigingsdatum, dan levert hetzelfde venster in v2 een
andere rijenset op zonder dat er iets faalt. Dit moet bij de leverancier worden nagevraagd of met
een vergelijkende telling worden vastgesteld voordat er op v2 wordt geproduceerd.

Ook nieuw: `modifiedFrom` en `modifiedTo`. Die maken incrementele verversing op wijzigingsdatum
mogelijk in plaats van een venster op de verkoopdatum. Een verbetering, maar wel een die de
betekenis van het watermerk verandert en dus een bewuste keuze vraagt.

### 5. Authenticatie — BREAKING

Zie [Authenticatie](#authenticatie) voor de gemeten uitkomsten. Alles verandert: host,
token-endpoint, grant-type, het aantal benodigde secrets, en er komt een scope bij. De huidige
inloggegevens worden door v2 geweigerd.

### 6. Rate limits — NIET-BREAKING

v1 dwingt een afkoeltijd af die in geen enkele documentatie staat en die deze run bij toeval heeft
gevonden. Een tweede aanroep op hetzelfde endpoint binnen 120 seconden geeft:

```
HTTP 409
"You may only perform this action every 120 seconds."
```

Een aanroep op een **ander** endpoint direct daarna geeft gewoon HTTP 200. De afkoeltijd geldt dus
**per endpoint**, niet per token en niet per client. Dat verklaart de `rate_limit_delay` van 125 in
de bestaande configuratie: dat zijn seconden, met vijf seconden marge.

v2 documenteert niets. De spec bevat geen woord over rate limits, throttling of quota, en op geen
enkel Statistics-endpoint is een `429` gedeclareerd. `429 Too Many Requests` komt in de hele spec
een keer voor, op `POST /api/v2/WaitingRoom/claim`. De enige harde grens is een body-grens en geen
rate limit: `limit` maximaal 100 000 rijen per call.

Dit is als **niet-breaking** gelabeld omdat de bestaande instelling van 125 seconden op v2 blijft
werken; hij is alleen waarschijnlijk veel te conservatief. Wie hem verlaagt zonder te meten, ruilt
een trage run in voor een onvoorspelbare. De generieke client herhaalt een `429` al met de
`Retry-After`-header en een `409` met lineaire backoff, dus een ongedocumenteerde limiet leidt tot
vertraging in plaats van uitval.

## Uitfasering van v1

**Onbekend — de leverancier moet worden bevraagd.** Dit is wat er is gezocht en wat het opleverde:

| Waar gezocht | Uitkomst |
|---|---|
| v2-spec, alle 148 paden en 352 schemadefinities | Geen enkel `Statistics`-pad of `Statistics`-schema is `deprecated`. De twaalf `deprecated`-vlaggen die er staan, zitten op ongerelateerde velden: annuleringsvelden, `availablePriceKeys` en een betaalmethodeveld |
| v2-spec op `sunset`, `deprecat`, `obsolete`, `legacy` | Geen sunset-datum. `legacy` komt twee keer voor en gaat over kortingscode- en uitnodigingscodeversies in het product, niet over de API |
| `api.ticketcounter.net`: swagger, `/help`, hostwortel | HTTP 404, HTTP 404, redirect naar de marketingsite. Geen publiek contract en geen changelog |
| Publieke ontwikkelaarsportalen (`docs.`, `developer.`, `support.`, `helpdesk.ticketcounter.eu`) | Bestaan niet; DNS lost niet op |
| Websearch op uitfaseringsbeleid en release notes | Niets van deze leverancier gevonden |

**Conclusie: onbekend — leverancier bevraagd op 2026-08-28**, via de vraag in
[Vragen aan de leverancier](#vragen-aan-de-leverancier). Dat is de datum waarop de vraag is
opgesteld; het stellen ervan ligt bij de opdrachtgever, want dit onderzoek voert geen
leverancierscorrespondentie.

Zolang die datum ontbreekt is er **geen deadline** en dus ook geen dwang om te migreren. Dat
verandert het karakter van het besluit: het is een verbeteringsbesluit, geen continuiteitsbesluit.
Zodra de leverancier wel een datum noemt, kantelt dat en wordt de doorlooptijd van de drie
blokkades het kritieke pad.

## Gemengd draaien: een entiteit op v2, de rest op v1

**Nee, niet binnen een bronconfiguratie.** De reden is de tokenflow, en die is gedeeld.

Het configuratieschema legt de verbindings- en authenticatiegegevens vast op **bronniveau**, niet op
entiteitsniveau. De tabel `source_connection_configs` heeft een rij per bronconfiguratie en draagt
`base_url`, `auth_method`, `auth_grant_type`, `auth_token_endpoint`, de drie secret-templates,
`key_vault_url` en `rate_limit_delay`. De tabel `source_entity_ingestion_configs` heeft daarentegen
**geen enkele** auth- of base-url-kolom: hij kent alleen `url_path`, `strategy`, de watermerkvelden,
de recordsleutel en `strategy_details`.

Alle vijf entiteiten delen daarom noodgedwongen:

- een host,
- een token-endpoint en een grant-type,
- een set Key Vault-secrets,
- een `rate_limit_delay`.

`sold_tickets` op `client_credentials` tegen de v2-host zetten terwijl de andere vier op
`refresh_token` tegen de v1-host blijven, kan dus niet: er is maar een plek waar het grant-type
staat, en die geldt voor de hele bron.

**Nuance, want de notebook kan meer dan het schema.** De API-client kent wel een per-entiteit
override van de base-URL (`Details.EntityBaseUrl`, gebruikt in `get_entity()`). Er is alleen geen
kolom in het configuratieschema die hem vult, en hij lost het echte probleem niet op: een andere
host is nog geen ander token.

**Wat wel kan, met open ogen:** een **tweede bron-slug** aanmaken met een eigen
`source_connection_configs`-rij die op v2 wijst, en daar alleen `sold_tickets` in hangen. Dat is
technisch houdbaar, maar het is een nieuwe bron en geen gedeeltelijke overstap. De prijs:

- een tweede Bronze-landingsmap en een tweede watermerkreeks voor dezelfde entiteit,
- een eigen paar `03_schema.py` / `04_transforms.py`,
- een eigen plek in de pipeline en het schema,
- en de verplichting om de entiteit uit de oude bronconfiguratie te halen, anders schrijven twee
  configuraties naar dezelfde Silver-tabel.

Omdat de drie blokkades — inloggegevens, POST-body, scope — sowieso voor **elke** v2-entiteit
gelden, levert die tweedeling geen tijdwinst op. Ze is alleen zinvol als je het risico van de
eerste v2-productierun wilt beperken tot een entiteit. Dat is een verdedigbare keuze, maar het is
een extra bron beheren, niet een knop omzetten.

## Authenticatie

### v1 (in productie, werkt)

- **Patroon:** OAuth2 met grant `refresh_token`
- **AuthScheme / Method:** `bearer` / `oauth2`
- **Token-endpoint:** `https://api.ticketcounter.net/token`
- **Scope:** geen
- **Secret-namen in de Key Vault** (alleen namen; waarden worden nooit gelezen):
  - `ticketcounter-{environment}-client-id`
  - `ticketcounter-{environment}-client-secret`
  - `ticketcounter-{environment}-refresh-token`
- **Gemeten 2026-08-28:** tokenaanvraag geslaagd, toegang tot alle vijf endpoints.

### v2 (doel, wordt geweigerd)

- **Patroon:** OAuth2 met grant `client_credentials`
- **Token-endpoint:**
  - prod: `https://apiv2.ticketcounter.eu/connect/token`
  - test: `https://apiv2test.ticketcounter.eu/connect/token`
- **Scope:** `TC.Tickets.API`
- **Secret-namen:** dezelfde `client-id` en `client-secret` conventie; het
  `refresh-token`-secret **vervalt**.
- **Aangeboden grants:** de discovery (`/.well-known/openid-configuration`, publiek, opgehaald
  2026-08-28) noemt `authorization_code`, `client_credentials`, `refresh_token`, `implicit`,
  `password`, `urn:ietf:params:oauth:grant-type:device_code`, `stc_delegation`,
  `tcproxy_delegation` en `api_key`. De ondersteunde scopes zijn `TC.Tickets.API` en
  `offline_access`. Test en productie geven exact dezelfde discovery.
- **Security geldt globaal:** de spec declareert op topniveau `security: [{oauth2: [], bearer: []}]`
  en de Statistics-operaties declareren geen override per operatie, dus het bearer-token geldt voor
  alle vijf.

### Gemeten: welke combinaties zijn geprobeerd

Alle aanvragen op 2026-08-28, met de bestaande secrets uit de Key Vault.

| Token-endpoint | Grant | Scope | Uitkomst |
|---|---|---|---|
| `https://apiv2.ticketcounter.eu/connect/token` | `client_credentials` | `TC.Tickets.API` | **HTTP 400 `{"error":"invalid_client"}`** |
| `https://apiv2.ticketcounter.eu/connect/token` | `client_credentials` | *geen* | **HTTP 400 `invalid_client`** |
| `https://apiv2.ticketcounter.eu/connect/token` | `client_credentials` | `offline_access` | **HTTP 400 `invalid_client`** |
| `https://apiv2.ticketcounter.eu/connect/token` | `refresh_token` (met het v1-refresh-token) | `TC.Tickets.API` | **HTTP 400 `invalid_client`** |
| `https://apiv2test.ticketcounter.eu/connect/token` | `client_credentials` | `TC.Tickets.API` | **HTTP 400 `invalid_client`** |
| `https://api.ticketcounter.net/token` (controle) | `refresh_token` | *geen* | **HTTP 200, token verkregen** |

Bovendien: `GET https://api.ticketcounter.net/api/v2/statistics/soldtickets/nl-NL` geeft HTTP 404.
v2 leeft niet op de v1-host; er is geen sluiproute.

De controle-aanroep is de belangrijke: dezelfde secrets werken wel op v1. De waarden zijn dus
correct opgeslagen en leesbaar — ze zijn eenvoudigweg **niet als client geregistreerd bij de
v2-identiteitsserver**. `invalid_client` van een IdentityServer betekent precies dat: onbekende
client, of een secret dat niet bij die client hoort.

**Conclusie voor de inloggegevens:** v2 gebruikt **niet** dezelfde inloggegevens. Er zijn nieuwe
client-inloggegevens nodig, **per omgeving**, met scope `TC.Tickets.API`. De bestaande vault en de
bestaande naamconventie kunnen blijven; het `refresh-token`-secret vervalt. Omdat de credentials
wijzigen, is dit een **blokkade**: secretwaarden lopen via het invoerformulier van het portal, dat
ze browser-direct in de Key Vault van de klant schrijft, en nooit via een agent.

### Configuratiehiaat: de scope is niet in te stellen

De notebook ondersteunt `AuthDetails.OAuth2.Scope` en stuurt hem mee wanneer hij gevuld is. Maar er
is **geen kolom** in `source_connection_configs` die hem draagt, en de configuratiegenerator emitteert
`Scope` nergens: hij bouwt het `OAuth2`-blok uit `GrantType`, `TokenEndpoint`,
`ClientIdSecretTemplate`, `ClientSecretSecretTemplate` en eventueel `RefreshTokenSecretTemplate`, en
verder niets. De enige bestaande `client_credentials`-bron in dit landschap heeft geen scope nodig,
dus het is nooit opgevallen.

Gevolg: als v2 de scope **verplicht** stelt, kan er vandaag geen werkende v2-configuratie worden
gebouwd, ook niet met geldige inloggegevens. Of de scope werkelijk verplicht is, valt niet te testen
zolang `invalid_client` terugkomt — een IdentityServer die geen scope krijgt, geeft soms alsnog een
token met alle toegestane scopes. **UNKNOWN, en het risico is asymmetrisch:** het kost weinig om de
kolom toe te voegen en veel om er tijdens de eerste productierun achter te komen.

## Verbinding

- **BaseUrl:**
  - v1 (in gebruik): `https://api.ticketcounter.net`
  - v2 prod: `https://apiv2.ticketcounter.eu`
  - v2 test: `https://apiv2test.ticketcounter.eu`
  - De v2-spec declareert geen `servers`-blok; de base-URL's zijn overgenomen uit de gepubliceerde
    spec en de token-host.
- **RateLimitDelay:**
  - v1: `125` (seconden) — en dat is **noodzakelijk**, want de bron dwingt 120 seconden per endpoint
    af. Zie [Rate limits](#rate-limits).
  - v2: `0.5` seconden als voorzichtige startwaarde, **niet** afgeleid van een gedocumenteerde
    limiet, want die bestaat niet. Opnieuw beoordelen na de eerste live run.
- **Meerdere omgevingen per klant:** de bron levert per omgeving een eigen set inloggegevens; de
  omgevingsnaam wordt in de secret-namen ingevuld via `{environment}`. Aan de kant van de leverancier
  bestaat daarnaast een testomgeving (`apiv2test`) die voor validatie bruikbaar is zodra er
  inloggegevens zijn.
- **ApiHeaders:** voor v2 is `Content-Type: application/json` **verplicht**, omdat elke
  Statistics-call een JSON-request-body heeft. Geaccepteerde request-mediatypes per endpoint:
  `application/json`, `application/json-patch+json`, `text/json`, `application/*+json`. De
  succesrespons is in de spec gedeclareerd als `text/plain`, `application/json` en `text/json`, maar
  draagt in alle drie hetzelfde JSON-schema. **UNKNOWN** welke `Content-Type`-responseheader er
  werkelijk uitkomt; parseert de client hem als JSON, dan is dit een documentatiekwestie en geen
  blokkade.
- **Stabiliteit v1 (waarneming):** een van de zeven live aanroepen in deze run brak af met een
  afgebroken TLS-verbinding en slaagde bij herhaling wel. Eenmalig, dus geen patroon — maar het
  bevestigt dat de retry-logica van de generieke client hier nut heeft.

## Migratieplan

Genummerde stappen. De eerste drie zijn de blokkades; ze kunnen parallel lopen, maar geen van de
latere stappen kan zonder alle drie.

1. **Vraag v2-inloggegevens aan bij de leverancier**, per omgeving, met grant `client_credentials`
   en scope `TC.Tickets.API`. Vraag er meteen bij of de bestaande client kan worden uitgebreid naar
   v2 of dat het een nieuwe client wordt, en of `apiv2test` bruikbare data draagt voor validatie.
2. **Laat de klant de secrets invoeren via het portalformulier.** Twee secrets per omgeving:
   `ticketcounter-{environment}-client-id` en `ticketcounter-{environment}-client-secret`. Het
   bestaande `refresh-token`-secret blijft nog even staan; dat is het terugvalpad. Nooit via een
   agent, nooit via een chat.
3. **Open een user story op `general-notebooks`** voor een REST-`POST` met JSON-filterbody. Concreet:
   `StrategyDetails.Method='POST'` toestaan **zonder** GraphQL-blok, en de paginerings-, watermerk-
   en `ExtraParams`-waarden in de body binden in plaats van in de query-string. Vraag in dezelfde
   story om een `Scope`-kolom in het configuratieschema plus emissie in de generator, of open daar
   een tweede story voor. Zie [Benodigde uitbreidingen aan general-notebooks](#benodigde-uitbreidingen-aan-general-notebooks).
4. **Meet v2 zodra stap 2 rond is, nog voordat er iets wordt gebouwd.** Een call per entiteit met
   `limit=1000` over een venster waarvan de v1-telling bekend is. Leg vast: de echte
   voorbeeld-JSON, de `resultCount`-semantiek, de vulgraad van `discountName`, de datumopmaak, en
   het aantal rijen dat hetzelfde venster in v1 en v2 oplevert. Dat laatste is de test op
   `dateRangeType`.
5. **Werk de veldencatalogi in dit rapport bij** met de gemeten waarden en vervang elke
   "UNKNOWN — niet vastgelegd" door een echte sample, met `excludeContactInfo: true` aan de
   API-kant in plaats van achteraf redigeren.
6. **Laat de config-builder de v2-configuratie bouwen.** Wijzigt ten opzichte van vandaag:
   `base_url`, `auth_grant_type`, `auth_token_endpoint`, scope, het vervallen refresh-token-template,
   `url_path` per entiteit (let op de hoofdletter in `Statistics`), `output_record_key` per entiteit,
   `ResultCountKey`, en `rate_limit_delay`. Ongewijzigd: `strategy`, `PageSize`, `ChunkSize`,
   `batch_size`, watermerkformaat en -overlap.
7. **Herschrijf `03_schema.py` en `04_transforms.py`** naar camelCase. Neem in dezelfde slag een
   besluit over `InkoopPrijs` (bron `BuyingPrice` vervalt) en `Landnaam` (wordt `countryCode`), en
   neem `discountName`, `discountCode`, `priceTypeName`, `eventName`, `performerName`,
   `creationDate` en `modificationDate` op.
8. **Draai in DEV, en vergelijk op rijaantal en op som per dag** tegen de laatste v1-run over
   hetzelfde venster. Verschil in rijaantal wijst op `dateRangeType`; verschil in bedragen op een
   veldmapping.
9. **Verlaag `rate_limit_delay` stapsgewijs** en meet. Ga niet in een keer van 125 naar 0,5: verlaag,
   draai een volledige chunk, kijk of er 409 of 429 terugkomt.
10. **Promoveer naar PRD** volgens de normale promotiepoort, met de v1-configuratie nog intact.
11. **Faseer het refresh-token-secret uit** en werk het configuratiesjabloon bij dat deze bron als
    canoniek voorbeeld van het refresh-token-patroon noemt. Pas na een aantoonbaar stabiele periode
    op v2.

### Terugvalpad

Het terugvalpad is bewust goedkoop, en dat is de belangrijkste reden dat dit een JA-MITS kan zijn
in plaats van een NEE.

- **Tot stap 10:** er verandert niets aan de draaiende v1-connector. Stoppen kost het werk, niet de
  productie.
- **Na stap 10, bij een probleem in PRD:** zet de bronconfiguratie terug op de v1-waarden
  (`base_url`, `auth_grant_type`, `auth_token_endpoint`, `url_path`, `output_record_key`,
  `ResultCountKey`, `rate_limit_delay`) en herstel het vorige paar `03_schema.py` /
  `04_transforms.py`. Dat is een configuratieterugrol plus twee bestanden, geen datamigratie.
- **Wat het terugvalpad open houdt:** het `refresh-token`-secret **niet** verwijderen tot stap 11.
  Zonder dat secret is v1 niet meer bereikbaar en is er geen weg terug.
- **Wat er met de data gebeurt:** Silver laadt incrementeel met SCD-type 1 en houdt geen historie.
  Terugrollen betekent dus dat de v2-kolommen die v1 niet levert leeg blijven, niet dat er data
  verloren gaat. Reken er wel op dat de eerste v2-run de hele tabel als gewijzigd ziet: de
  hash over de niet-sleutelkolommen verandert zodra er kolommen bij komen of weggaan.

## Entiteitenoverzicht

| Entiteit | Endpointpad | Binnen scope | Bovenliggende entiteit | Toelichting |
|---|---|---|---|---|
| `baskets` | `POST /api/v2/Statistics/baskets` | Ja | — | Geneste arrays: payments, reservations, cancellations, partialCancellation, contact |
| `sold_tickets` | `POST /api/v2/Statistics/sold-tickets` | Ja | — | Breedste entiteit (72 velden sinds `discountName`) |
| `sold_subscriptions` | `POST /api/v2/Statistics/sold-subscriptions` | Ja | — | 47 velden sinds `discountName` |
| `ticket_scans` | `POST /api/v2/Statistics/scans` | Ja | — | 47 velden. **Geen modified*-filter** — zie hieronder |
| `cancellations` | `POST /api/v2/Statistics/cancellations` | Ja | — | 12 velden |
| *Alle overige tags* | `Reservations`, `Pos`, `Contacts`, `Payments`, `Webhooks`, … (nog 25) | Nee | — | Buiten scope — geen functionele vraag |

De vijf entiteiten binnen scope komen **1-op-1** overeen met de vijf entiteiten die al op v1 draaien
(`baskets`, `ticket_scans`, `sold_tickets`, `sold_subscriptions`, `cancellations` in
`client-configs/{env}/ticketcounter/03_schema.py`). De entiteitsnamen moeten ongewijzigd blijven.

**Omgevingen:** de bron levert per omgeving een eigen set inloggegevens; de omgevingsnaam wordt in de
secret-namen ingevuld via `{environment}`. Daarnaast bestaat er aan de kant van de leverancier een
testomgeving (`apiv2test`) die voor validatie bruikbaar is zodra er v2-inloggegevens zijn.

## Paginering en ingestie per entiteit

> De precieze POST-body die elk endpoint verwacht — filtervelden per entiteit, `offset`/`limit` en de
> enum-waarden van `StatisticsFilterDateRangeType` — is gedocumenteerd in
> [request-body-contract.md](#ticketcounter-v2--contract-van-de-request-body).

De paginering is **identiek voor alle vijf entiteiten**: numerieke `offset` + `limit` in de body, waarbij
`offset` en `resultCount` in de respons worden teruggegeven. De response-envelope heeft voor alle vijf
dezelfde vorm: `succeeded`, `errorMessage`, `isRedirect`, `redirectUrl`, `displayError`, `errorCode`,
`offset`, `resultCount`, plus één record-array.

**Strategie:** `chunk_offset` voor alle vijf — gelijk aan de strategie die v1 al gebruikt. Die geeft chunking
op datumbereik (de v1-connector chunkt 30 dagen per keer) met offset-paginering binnen elke chunk.
`offset` alleen zou alleen werken als de volledige historie in één datumvenster past.

### baskets / sold_tickets / sold_subscriptions / cancellations

- **Strategie:** `chunk_offset`
- **WatermarkType:** `date`
- **UrlPath:** `api/v2/Statistics/{baskets|sold-tickets|sold-subscriptions|cancellations}`
- **ExtraParams:** moeten mee in de **body**, niet in de query-string (hiaat in het framework)
- **Output.RecordKey / RecordType:** `baskets` / `soldTickets` / `soldSubscriptions` / `cancellations` — `keyed`
- **StrategyDetails:** `Pagination.OffsetParam: offset`, `PageSizeParam: limit`, `PageSize: 10000`,
  `ResultCountKey: resultCount`; `LoopChunks.ChunkType: days`, `ChunkSize: 30`
- **WatermarkDetails:** `ParamStart: modifiedFrom`, `ParamEnd: modifiedTo` (voorkeur — echte
  change-data capture), of `fromDate`/`toDate` + `dateRangeType` voor vensters op evenementdatum
- **Extraction.BatchSize / MaxTotalRecords:** `150000` / `None` (spiegelt v1)

### ticket_scans

- Zelfde als hierboven, **behalve**: `modifiedFrom`/`modifiedTo` en `dateRangeType` bestaan niet.
- **WatermarkDetails:** `ParamStart: fromDate`, `ParamEnd: toDate` — het venster filtert op **scandatum**,
  dus laat binnenkomende wijzigingen op een al ingelezen scan kunnen niet via het watermark worden
  gedetecteerd.
- **Output.RecordKey:** `scans`

## Rate limits

### v1 — gemeten, en strenger dan verwacht

Twee aanroepen op **hetzelfde** endpoint binnen 120 seconden geven:

```
HTTP 409
"You may only perform this action every 120 seconds."
```

Een aanroep op een **ander** endpoint direct na die 409 geeft HTTP 200. De afkoeltijd is dus
**per endpoint**, niet per token en niet per client. Dat is nergens gedocumenteerd en verklaart
waarom de bestaande configuratie een `rate_limit_delay` van 125 draagt: seconden, met marge.

Praktisch gevolg: een volledige herlading kost minimaal `aantal_chunks x aantal_pagina's x 120 s`
per entiteit. Vijf entiteiten kunnen wel parallel, want ze delen de afkoeltijd niet.

### v2 — niets gedocumenteerd

- De spec bevat geen tekst over rate limits, throttling of quota.
- Op geen enkel Statistics-endpoint is een `429` gedeclareerd. `429 Too Many Requests` komt in de
  hele spec een keer voor, op `POST /api/v2/WaitingRoom/claim`.
- De enige harde limiet is een **body-limiet**, geen rate limit: `limit` maximaal 100 000 rijen per
  call, standaard 1000.
- `RateLimitDelay: 0.5` is een veilige startwaarde, geen gemeten waarde. De generieke client
  herhaalt `429` al met de `Retry-After`-header en `409` met lineaire backoff, dus een
  ongedocumenteerde limiet leidt tot vertraging in plaats van uitval.

**Of v2 de afkoeltijd van 120 seconden loslaat, is niet vastgesteld** — dat vraagt een werkend
token. Het is wel de grootste potentiele winst van de migratie, groter dan het veld waar de
leveranciersmelding over gaat.

## Velden en voorbeeld-JSON per entiteit

Volledige typeoverzichten per veld zijn opgesplitst in catalogi per entiteit om de documentlimiet van 250 regels
te respecteren (`contributing/document-standards.md`):

| Entiteit | Veldencatalogus | Velden | Record key in respons |
|---|---|---|---|
| `baskets` | [fields-baskets.md](#ticketcounter-v2--veldencatalogus-baskets) | 16 (+4 sub-schema's) | `baskets` |
| `sold_tickets` | [fields-sold-tickets.md](#ticketcounter-v2--veldencatalogus-sold-tickets) | 72 | `soldTickets` |
| `sold_subscriptions` | [fields-sold-subscriptions.md](#ticketcounter-v2--veldencatalogus-sold-subscriptions) | 47 | `soldSubscriptions` |
| `ticket_scans` | [fields-scans.md](#ticketcounter-v2--veldencatalogus-scans) | 47 | `scans` |
| `cancellations` | [fields-cancellations.md](#ticketcounter-v2--veldencatalogus-cancellations) | 12 | `cancellations` |

**Voorbeeld-JSON voor v2: UNKNOWN voor alle vijf entiteiten — niet vastgelegd.** De bestaande inloggegevens
worden door v2 geweigerd (`invalid_client`, opnieuw bevestigd op 2026-08-28), dus er kon geen live call worden
gedaan. Er zijn geen voorbeelddata verzonnen. De voorbeelden moeten worden vastgelegd zodra er
v2-inloggegevens zijn afgegeven, **voordat** de config-builder de schema's definitief maakt.

**Voor v1 is dit sinds 2026-08-28 wel gemeten.** Alle vijf entiteiten zijn live bemonsterd; de veldenlijsten en
recordsleutels staan in [Huidige versie per entiteit](#huidige-versie-per-entiteit-gemeten) en de velddelta per
entiteit in [Velddelta per entiteit](#velddelta-per-entiteit). De samples zelf staan niet in dit rapport: ze
bevatten persoonsgegevens en v1 kent geen schakelaar aan de API-kant om die te onderdrukken.

`baskets` heeft sub-schema's nodig voor geneste structs (`PaymentInfo`, `BasketReservationInfo`,
`PartialCancelInfo`, `BasketContactInfo`) — gedocumenteerd in de bijbehorende catalogus.

## Belangrijkste datakenmerken per entiteit

| Entiteit | Natuurlijke PK | Laatst-gewijzigd-veld | Incrementeel ophalen? | Volledige periode opnieuw ophalen voor deletes? | Kandidaat voor partitionering |
|---|---|---|---|---|---|
| `baskets` | `basketKey` (uuid, niet-null) | **niet aanwezig in de payload** | Ja (`modifiedFrom`/`modifiedTo`) | Ja — annuleringen komen binnen als geneste arrays | `basketConfirmed` |
| `sold_tickets` | **UNKNOWN — geen enkele sleutel.** Kandidaten: `reservationKey` + `ticketCode` + `priceKey` | `modificationDate` | Ja | Ja — `cancelDate` wordt in place gezet | `saleDate` / `confirmedDate` |
| `sold_subscriptions` | `subscriptionKey` (uuid, niet-null) | `modificationDate` | Ja | Ja — `cancelDate` wordt in place gezet | `saleDate` |
| `ticket_scans` | `scanId` (int, niet-null) | **geen** | Deels — alleen op `scanDate` | Onwaarschijnlijk (scans zijn append-only) | `scanDate` |
| `cancellations` | `reservationKey` (+`ticketCode` bij meerdere plaatsen) | `modificationDate` | Ja | Nee — deze entiteit *is* de delete-feed | `cancelDate` |

- **Geeft de API updates op bestaande records terug?** Ja voor de vier entiteiten die `modifiedFrom` aanbieden —
  dat filter is alleen zinvol als records na aanmaak nog muteren.
- **Asymmetrie bij `baskets` (belangrijk):** de entiteit accepteert `modifiedFrom`/`modifiedTo`, maar `BasketInfo`
  bevat **geen** veld `modificationDate`. Je kunt dus wel filteren op wijziging, maar de wijzigingstimestamp niet
  opslaan, en geen max-kolom-watermark uit de payload berekenen. Het watermark moet worden afgeleid uit het
  request-venster (`_compute_new_marker_from_chunks`), wat de strategie `chunk_offset` al doet.
- **Datavolume:** **UNKNOWN** — niet meetbaar zonder inloggegevens. De v1-volumes zijn de beste indicatie
  (v1 gebruikt `BatchSize: 150000`, wat duidt op recordaantallen in de hoge zes cijfers voor baskets).

## Benodigde uitbreidingen aan general-notebooks

> **Deze sectie is op 2026-08-28 herzien.** Het rapport van 2026-07-17 stelde dat de `POST`-tak in
> `BaseAPIClient._request()` onbereikbare dode code was die alleen `params` als query-string kon
> versturen. Dat klopt niet meer. De client is sindsdien uitgebreid met een echte JSON-body
> (`json_body=`), inclusief afhandeling van fouten die binnen een HTTP 200 aankomen. De blokkade is
> daarmee **verschoven, niet verdwenen**: het transport is er, de body-opbouw voor een REST-filter
> niet.

| Benodigde functionaliteit | Reden | Betrokken notebook | Status |
|---|---|---|---|
| REST-`POST` met JSON-**filter**body | Alle vijf v2 Statistics-endpoints zijn `POST` en nemen filters en paginering in de body. De client kan een JSON-body sturen, maar bouwt hem alleen als **GraphQL**-document. | `notebook_Config_API.py` — `get_entity()` / `_graphql_request()` | **Blokkade** |
| `Method='POST'` zonder GraphQL-blok toestaan | De configuratievalidatie wijst `Method='POST'` expliciet af als er geen `GraphQL`-blok bij zit, en wijst `ExtraParams` in combinatie met `Method='POST'` ook af. | `notebook_Config_API.py` — configuratievalidatie | **Blokkade** |
| Paginering, watermerk en `ExtraParams` in de body binden | `_build_date_params()` en `OffsetPaginationExtractor._iter_offset_pages()` produceren waarden die via `_rest_request()` altijd query-parameters worden. | `notebook_Config_API.py` | **Blokkade** |
| Configureerbare OAuth2-`Scope` | De notebook leest `AuthDetails.OAuth2.Scope` en stuurt hem mee, maar er is geen kolom in `source_connection_configs` en de generator emitteert `Scope` niet. | configuratieschema + configuratiegenerator | **Blokkade indien v2 de scope verplicht stelt** |

**Bewijs, zodat dit niet opnieuw hoeft te worden uitgezocht:**

- `_request()` accepteert `method="GET"|"POST"` en een `json_body`; de POST-tak doet
  `self.session.post(url, headers=headers, json=json_body, timeout=60)` wanneer `json_body` gezet
  is. Het transport is dus aanwezig en getest.
- `get_entity()` kiest de body-opbouw met precies een voorwaarde:
  `if details.get("Method") == "POST" and details.get("GraphQL")`. Zonder `GraphQL`-blok valt hij
  terug op `_rest_request()`, en die bouwt uitsluitend een query-string.
- `_graphql_request()` weigert zonder querydocument: hij verwacht een GraphQL-document uit de
  sectie met entity-queries. Een REST-filterobject past daar niet in.
- De configuratievalidatie bevat drie regels die de weg dichtzetten: `Method` is alleen `'POST'`
  toegestaan en dan alleen voor GraphQL; `Method='POST'` **vereist** een `GraphQL`-blok;
  `ExtraParams` is **niet** toegestaan met `Method='POST'`.
- De configuratiegenerator bouwt het `OAuth2`-blok uit `GrantType`, `TokenEndpoint`,
  `ClientIdSecretTemplate`, `ClientSecretSecretTemplate` en eventueel `RefreshTokenSecretTemplate`.
  `Scope` komt er niet in voor, en er is geen kolom die hem zou kunnen leveren.

**Wat al wel wordt ondersteund en dus niet hoeft te worden gebouwd:** paginering met `chunk_offset`
en `offset` (`OffsetParam`, `PageSizeParam`, `PageSize`, `ResultCountKey`), datum-chunking via
`LoopChunks.ChunkType: days`, markerberekening uit chunk-vensters, `client_credentials`-authenticatie,
en afhandeling van herhaalpogingen bij `401`, `409`, `429` en `5xx` — inclusief respect voor
`Retry-After`.

> **Actie:** maak de user story voor de REST-POST-body aan **voordat** de config-builder start. De
> configuratie kan niet als kopie van v1 worden gebouwd, en ook niet als kopie van de bestaande
> GraphQL-bron.

## Openstaande vragen / UNKNOWNs

Genummerd, met de status na deze run.

1. **v2-inloggegevens — BLOKKEREND, bevestigd op 2026-08-28.** De bestaande client-id en
   client-secret geven `invalid_client` op v2 test en v2 prod, met en zonder scope, en ook met de
   `refresh_token`-grant. Dezelfde secrets werken wel op v1. Er zijn nieuwe v2-client-inloggegevens
   nodig, per omgeving.
2. **Vulgraad van `discountName` — UNKNOWN.** Geblokkeerd door (1). Zie
   [Discount Name](#discount-name--de-leveranciersmelding) voor de exacte call die het antwoord
   geeft zodra er een token is.
3. **Voorbeeld-JSON per entiteit voor v2 — UNKNOWN.** Geblokkeerd door (1). Vereist voordat de
   schema's definitief worden gemaakt: de contracttypes moeten tegen echte responses worden
   bevestigd, met name de datum-tijdopmaak en of een `text/plain`-respons als JSON parseert.
   *Voor v1 is dit sinds 2026-08-28 wel vastgelegd — alle vijf entiteiten zijn live bemonsterd.*
4. **Semantiek van `resultCount` in v2 — UNKNOWN.** De offset-lus stopt zodra
   `resultCount < PageSize`. Is `resultCount` het totaal in plaats van de paginatelling, dan
   eindigt die lus niet correct. De spec definieert het niet. *In v1 is het gemeten en is het de
   paginatelling.*
5. **Rate limits op v2 — UNKNOWN.** Niets gedocumenteerd, geen `429` gedeclareerd. *Voor v1 is de
   limiet nu gemeten: 120 seconden per endpoint, afgedwongen met HTTP 409.*
6. **Waarop filteren `fromDate` / `toDate` in v1? — UNKNOWN, en dit is nieuw.** v2 kent
   `dateRangeType` met `ConfirmationDate` als standaard. Filtert v1 op een andere datum, dan levert
   hetzelfde venster in v2 een andere rijenset zonder dat er iets faalt. Vaststellen door de
   rijaantallen over hetzelfde venster te vergelijken, of navragen bij de leverancier.
7. **Is de scope `TC.Tickets.API` verplicht bij `client_credentials`? — UNKNOWN.** Niet te testen
   zolang de client onbekend is bij de identiteitsserver. Bepaalt of het configuratiehiaat rond
   `Scope` een blokkade is of een nette-to-have.
8. **Delen de omgevingen op v2 een base-URL? — UNKNOWN, ongeverifieerd sinds 2026-07-17.** Op v1 is
   het een host met per omgeving een eigen set inloggegevens. Of v2 dat model aanhoudt, is niet
   vastgesteld.
9. **Primaire sleutel van `sold_tickets` — UNKNOWN, ongeverifieerd sinds 2026-07-17.** Er bestaat
   geen enkel niet-null sleutelveld in het contract. De v1-connector gebruikt `TicketCode` als
   sleutel; of die in v2 uniek blijft, moet met echte data worden bevestigd.
10. **Datavolumes op v2 — UNKNOWN.** Geblokkeerd door (1).
11. **Uitfaseringsdatum van v1 — UNKNOWN.** Zie [Uitfasering van v1](#uitfasering-van-v1): niet in
    de spec, geen publieke documentatie, geen changelog. Alleen de leverancier weet dit.
12. **Bevat `apiv2test` bruikbare data voor validatie? — UNKNOWN, ongeverifieerd sinds 2026-07-17.**

## Vragen aan de leverancier

Deze vragen kan dit onderzoek niet zelf beantwoorden; ze bepalen wel de planning. Ze zijn
geformuleerd om in een keer gesteld te kunnen worden.

1. **Inloggegevens.** Onze bestaande client-id en client-secret werken op `api.ticketcounter.net`
   maar geven `invalid_client` op `apiv2.ticketcounter.eu/connect/token` en op
   `apiv2test.ticketcounter.eu/connect/token`. Kan de bestaande client worden uitgebreid naar v2,
   of moeten er nieuwe client-inloggegevens worden uitgegeven — en dan graag per omgeving,
   afzonderlijk.
2. **Scope.** Is `scope=TC.Tickets.API` verplicht bij de `client_credentials`-grant, of geeft de
   identiteitsserver zonder scope een bruikbaar token?
3. **Uitfasering.** Is er een einddatum voor de `Statistics`-endpoints op `api.ticketcounter.net`?
   Let op dat dit een andere API is dan de spec die de Swagger-UI op de v2-host als "V1"
   publiceert. Waar wordt een uitfasering aangekondigd — is er een changelog, een statuspagina of
   een mailinglijst?
4. **`resultCount`.** Bevat `resultCount` in de v2-Statistics-responses het aantal rijen op de
   opgevraagde pagina, of het totaal aantal gevonden rijen?
5. **`dateRangeType` versus v1.** Op welke datum filteren `fromDate` en `toDate` op de
   v1-`Statistics`-endpoints? Komt dat overeen met `dateRangeType = 0 (ConfirmationDate)` in v2, of
   met `CreationDate` of `VisitDate`?
6. **Rate limits op v2.** De v1-endpoints geven HTTP 409 met "You may only perform this action
   every 120 seconds." Geldt op v2 een vergelijkbare limiet? Zo ja, welke, en per wat — per
   endpoint, per client of per tenant?
7. **Twee vervallen velden.** `BuyingPrice` en `CountryName` zitten wel in de v1-response en niet in
   `SoldTicketsInfo` op v2. Is daar een vervanger voor, of vervallen ze bewust?
8. **Testomgeving.** Bevat `apiv2test.ticketcounter.eu` representatieve data voor onze omgevingen,
   zodat we de migratie daar kunnen valideren voordat we op productie schakelen?

---

> De secties hieronder beschrijven het v2-contract per entiteit. Ze staan hier inline zodat het rapport
> op zichzelf staat; de config-builder heeft ze in hun geheel nodig.

## Ticketcounter v2 — contract van de request body

Het filter- en pagineringsobject dat elk `Statistics`-endpoint in de **POST-body** verwacht.
Onderdeel van [ticketcounter_research.md](../ticketcounter_research.md).

### Inhoudsopgave

| Sectie | Omschrijving |
|---------|-------------|
| [Gedeelde pagineringsvelden](#gedeelde-pagineringsvelden) | offset / limit, op elke entiteit |
| [Datumfiltering per entiteit](#datumfiltering-per-entiteit) | Welke filters waar bestaan |
| [StatisticsFilterDateRangeType](#statisticsfilterdaterangetype) | Enum-waarden |

Alle vijf endpoints nemen een filterobject in de **request body** (niet in de query-string).

### Gedeelde pagineringsvelden

| Body-veld | Type | Betekenis |
|---|---|---|
| `offset` | `int32` | Aantal over te slaan rijen |
| `limit` | `int32` | Maximaal aantal terug te geven rijen. **Max 100 000**, standaard 1000 |

### Datumfiltering per entiteit

| Body-veld | baskets | sold-tickets | sold-subscriptions | cancellations | scans |
|---|---|---|---|---|---|
| `fromDate` / `toDate` (date-time) | ja | ja | ja | ja | ja |
| `modifiedFrom` / `modifiedTo` (date-time) | ja | ja | ja | ja | **nee** |
| `dateRangeType` (enum) | ja | ja | ja | ja | **nee** |
| `excludeContactInfo` (bool) | ja | ja | — | — | ja |
| `eventKey` (uuid) | — | ja | — | ja | — |
| `languageCode` (string) | — | ja | — | — | ja |
| Overig | — | — | — | `includeTicketCodeValues` (bool) | `ticketScansOnly`, `subscriptionScansOnly` (bool) |

### StatisticsFilterDateRangeType

`StatisticsFilterDateRangeType` (`TC.Common.Models.Enums`) — integer-enum die bepaalt op welke datum
`fromDate`/`toDate` filteren:

| Waarde | Naam | Betekenis |
|---|---|---|
| `0` | `ConfirmationDate` | Bevestigingsdatum van de reservering (**standaard**) |
| `1` | `CreationDate` | Aanmaakdatum van de reservering |
| `2` | `VisitDate` | Bezoekdatum van de reservering |

---

## Ticketcounter v2 — veldencatalogus `baskets`

Afgeleid van OpenAPI-schema `TC.Common.Models.Statistics.BasketInfo` (record key `baskets`).
Onderdeel van [ticketcounter_research.md](../ticketcounter_research.md).

### Inhoudsopgave

| Sectie | Omschrijving |
|---------|-------------|
| [Recordvelden](#recordvelden) | Typeoverzicht per veld voor één `baskets`-record |
| [Sub-schema's](#sub-schemas) | Geneste struct-definities waarnaar hierboven wordt verwezen |
| [Voorbeeld-JSON](#voorbeeld-json) | Status van een echte responsvoorbeeld |

### Recordvelden

| API-veld | Spark-type | Nullable | Toelichting |
|---|---|---|---|
| `basketConfirmed` | `TimestampType` | ja |  |
| `basketNumber` | `StringType` | ja |  |
| `basketKey` | `StringType` | nee | UUID. |
| `externalBasketNumber` | `StringType` | ja |  |
| `externalInvoiceId` | `StringType` | ja |  |
| `posFirstName` | `StringType` | ja |  |
| `posMiddleName` | `StringType` | ja |  |
| `posLastName` | `StringType` | ja |  |
| `posName` | `StringType` | ja |  |
| `posGroupName` | `StringType` | ja |  |
| `payments` | `ArrayType(StructType)` (sub-schema `PaymentInfo`) | ja |  |
| `reservations` | `ArrayType(StructType)` (sub-schema `BasketReservationInfo`) | ja |  |
| `cancellations` | `ArrayType(StructType)` (sub-schema `BasketReservationInfo`) | ja |  |
| `partialCancellation` | `ArrayType(StructType)` (sub-schema `PartialCancelInfo`) | ja |  |
| `invitationCodes` | `ArrayType(StringType)` | ja |  |
| `contact` | `StructType` (zie sub-schema `BasketContactInfo`) | nee |  |

### Sub-schema's

#### `PaymentInfo`

| API-veld | Spark-type | Nullable | Toelichting |
|---|---|---|---|
| `payId` | `StringType` | ja |  |
| `paymentType` | `StringType` | ja |  |
| `paymentRemark` | `StringType` | ja |  |
| `amount` | `DoubleType` | nee |  |

#### `BasketReservationInfo`

| API-veld | Spark-type | Nullable | Toelichting |
|---|---|---|---|
| `reservationKey` | `StringType` | nee | UUID. |
| `reservationNumber` | `StringType` | ja |  |
| `amount` | `DoubleType` | nee |  |

#### `PartialCancelInfo`

| API-veld | Spark-type | Nullable | Toelichting |
|---|---|---|---|
| `ticketcode` | `StringType` | ja |  |
| `amount` | `DoubleType` | nee |  |
| `reservationNumber` | `StringType` | ja |  |

#### `BasketContactInfo`

| API-veld | Spark-type | Nullable | Toelichting |
|---|---|---|---|
| `contactKey` | `StringType` | ja | UUID. Unieke sleutel van de koper. Een koper kan meer dan één aankoop hebben |
| `name` | `StringType` | ja | Naam van de koper |
| `email` | `StringType` | ja | E-mailadres van de koper |
| `street` | `StringType` | ja | Straat van de koper |
| `houseNumber` | `StringType` | ja | Huisnummer van de koper |
| `postalCode` | `StringType` | ja | Postcode van de koper |
| `cityName` | `StringType` | ja | Plaats van de koper |
| `countryCode` | `StringType` | ja | Landcode van de koper |
| `lat` | `DoubleType` | ja | Breedtegraad van het adres van de koper |
| `lon` | `DoubleType` | ja | Lengtegraad van het adres van de koper |
| `companyName` | `StringType` | ja | Bedrijfsnaam |
| `firstName` | `StringType` | ja | Voornaam van de koper |
| `middle` | `StringType` | ja | Tussenvoegsel van de koper |
| `lastName` | `StringType` | ja | Achternaam van de koper |
| `phoneNumber` | `StringType` | ja | Telefoonnummer van de koper |
| `receiveNewsLetter` | `BooleanType` | ja | Geeft aan of de nieuwsbrief naar de koper gestuurd moet worden |
| `gender` | `StringType` | ja | Geslacht |
| `birthDate` | `TimestampType` | ja | Geboortedatum |

### Voorbeeld-JSON

**UNKNOWN — niet vastgelegd.** Er zijn geen werkende v2-inloggegevens; op 2026-08-28 opnieuw bevestigd
(`invalid_client`, zie *Openstaande vragen* in het hoofdrapport). De typen hierboven zijn afgeleid van het
gepubliceerde OpenAPI 3.0.4-contract, opgehaald op 2026-08-28, niet van een waargenomen respons. Er zijn geen
voorbeelddata verzonnen.

---

## Ticketcounter v2 — veldencatalogus `sold-tickets`

Afgeleid van OpenAPI-schema `TC.Common.Models.Statistics.SoldTicketsInfo` (record key `soldTickets`).
Onderdeel van [ticketcounter_research.md](../ticketcounter_research.md).

### Inhoudsopgave

| Sectie | Omschrijving |
|---------|-------------|
| [Recordvelden](#recordvelden-1) | Typeoverzicht per veld voor één `sold-tickets`-record |
| [Voorbeeld-JSON](#voorbeeld-json-1) | Status van een echte responsvoorbeeld |

### Recordvelden

| API-veld | Spark-type | Nullable | Toelichting |
|---|---|---|---|
| `eventKey` | `StringType` | ja | UUID. Unieke sleutel van het evenement |
| `type` | `StringType` | ja | Type van de aankoop |
| `reservationKey` | `StringType` | ja | UUID. Unieke sleutel van de reservering. |
| `performanceKey` | `StringType` | ja | UUID. Unieke sleutel van de voorstelling. |
| `performanceSectionKey` | `StringType` | ja | UUID. Unieke sleutel van de sectie van de voorstelling |
| `productName` | `StringType` | ja | Naam van het evenement en de artiest of het type ticket (prijstype) |
| `eventName` | `StringType` | ja | Naam van het evenement |
| `performerName` | `StringType` | ja | Naam van de artiest |
| `saleDate` | `TimestampType` | nee | Datum waarop de bestelling is geplaatst |
| `totalPrice` | `DoubleType` | nee | Verkoopprijs per plaats |
| `price` | `DoubleType` | nee | Verkoopprijs per plaats |
| `originalPrice` | `DoubleType` | ja | Oorspronkelijke verkoopprijs per plaats |
| `nrOfSeats` | `IntegerType` | nee | Aantal plaatsen op dit ticket |
| `channel` | `StringType` | ja | Waar het ticket is gekocht |
| `contactHolderKey` | `StringType` | ja | UUID. Unieke sleutel van de koper. Een koper kan meer dan één aankoop hebben |
| `name` | `StringType` | ja | Naam van de koper |
| `email` | `StringType` | ja | E-mailadres van de koper |
| `street` | `StringType` | ja | Straat van de koper |
| `houseNumber` | `StringType` | ja | Huisnummer van de koper |
| `postalCode` | `StringType` | ja | Postcode van de koper |
| `cityName` | `StringType` | ja | Plaats van de koper |
| `countryCode` | `StringType` | ja | Landcode van de koper |
| `lat` | `DoubleType` | ja | Breedtegraad van het adres van de koper |
| `lon` | `DoubleType` | ja | Lengtegraad van het adres van de koper |
| `validFrom` | `TimestampType` | ja | Datum en tijd vanaf wanneer het ticket geldig is |
| `validTo` | `TimestampType` | ja | Datum en tijd tot wanneer het ticket geldig is |
| `companyName` | `StringType` | ja | Bedrijfsnaam |
| `firstName` | `StringType` | ja | Voornaam van de koper |
| `middle` | `StringType` | ja | Tussenvoegsel van de koper |
| `lastName` | `StringType` | ja | Achternaam van de koper |
| `phoneNumber` | `StringType` | ja | Telefoonnummer van de koper |
| `receiveNewsLetter` | `BooleanType` | ja | Geeft aan of de nieuwsbrief naar de koper gestuurd moet worden |
| `paymentMethod` | `StringType` | ja | Betaalmethode waarmee de bestelling is betaald |
| `brancheID` | `StringType` | ja |  |
| `cancelDate` | `TimestampType` | ja | Datum en tijd van annulering van de bestelling |
| `reservationNumber` | `StringType` | ja | Nummer van de bestelling |
| `language` | `StringType` | ja | NAam van de taal |
| `salesChannel` | `StringType` | ja | Naam van het verkoopkanaal |
| `resellerName` | `StringType` | ja | Naam van de reseller |
| `priceKey` | `StringType` | ja | UUID. Unieke sleutel van het daadwerkelijke product/tickettype dat is gekocht |
| `languageCode` | `StringType` | ja | Code van de taal van de bestelling |
| `ticketCode` | `StringType` | ja | Barcode van het ticket |
| `capacityDate` | `TimestampType` | ja | Datum van het tijdslot, indien aanwezig |
| `capacityNames` | `ArrayType(StringType)` | ja | Namen van de gebruikte capaciteiten/tijdsloten (indien aanwezig) |
| `capacityStartTimeMinutesAfterMidnight` | `IntegerType` | ja | Starttijd van het tijdslot in minuten na middernacht, indien aanwezig |
| `capacityEndTimeMinutesAfterMidnight` | `IntegerType` | ja | Eindtijd van het tijdslot in minuten na middernacht, indien aanwezig |
| `capacityStartDate` | `StringType` | ja | Geformatteerde datum van het tijdslot, indien aanwezig |
| `capacityStartTime` | `StringType` | ja | Geformatteerde starttijd van het tijdslot, indien aanwezig |
| `capacityEndTime` | `StringType` | ja | Geformatteerde eindtijd van het tijdslot, indien aanwezig |
| `posGroupTitle` | `StringType` | ja | Titel van de POS-groep |
| `posTitle` | `StringType` | ja | Naam van de POS |
| `posContact` | `StringType` | ja | Naam van de POS-medewerker |
| `externalReservationNumber` | `StringType` | ja | Extern bestelnummer |
| `externalID` | `StringType` | ja | Externe ID van het tickettype (prijstype) |
| `extraInfo1` | `StringType` | ja | Extra info 1 van de bestelling |
| `extraInfo2` | `StringType` | ja | Extra info 2 van de bestelling |
| `extraInfo3` | `StringType` | ja | Extra info 3 van de bestelling |
| `testPayment` | `BooleanType` | nee | Is gekocht met een testbetaling |
| `confirmedDate` | `TimestampType` | ja | Datum van aankoop |
| `vatNumber` | `StringType` | ja | Btw-nummer |
| `vatLow` | `DoubleType` | nee | Bedrag laag btw-tarief |
| `vatMiddle` | `DoubleType` | nee | Bedrag middelhoog btw-tarief |
| `vatHigh` | `DoubleType` | nee | Bedrag hoog btw-tarief |
| `amountExVatLow` | `DoubleType` | nee | Bedrag exclusief laag btw-tarief |
| `amountExVatMiddle` | `DoubleType` | nee | Bedrag exclusief middelhoog btw-tarief |
| `amountExVatHigh` | `DoubleType` | nee | Bedrag exclusief hoog btw-tarief |
| `cashBooking` | `BooleanType` | nee | Geeft aan of dit een contante boeking betrof |
| `priceTypeName` | `StringType` | ja | Naam van het prijstype (tickettype) |
| `discountCode` | `StringType` | ja | Gebruikte kortingscode, indien van toepassing |
| `discountName` | `StringType` | ja | **Nieuw sinds 2026-07-17.** Naam van de gebruikte korting, indien van toepassing. Contract: `Name of the discount which was used, if any` |
| `creationDate` | `TimestampType` | nee | Aanmaakdatum van een reservering |
| `modificationDate` | `TimestampType` | ja | Wijzigingsdatum van een reservering |

### Voorbeeld-JSON

**UNKNOWN — niet vastgelegd.** Er zijn geen werkende v2-inloggegevens; op 2026-08-28 opnieuw bevestigd
(`invalid_client`, zie *Openstaande vragen* in het hoofdrapport). De typen hierboven zijn afgeleid van het
gepubliceerde OpenAPI 3.0.4-contract, opgehaald op 2026-08-28, niet van een waargenomen respons. Er zijn geen
voorbeelddata verzonnen.

---

## Ticketcounter v2 — veldencatalogus `sold-subscriptions`

Afgeleid van OpenAPI-schema `TC.Common.Models.Statistics.SoldSubscriptionsInfo` (record key `soldSubscriptions`).
Onderdeel van [ticketcounter_research.md](../ticketcounter_research.md).

### Inhoudsopgave

| Sectie | Omschrijving |
|---------|-------------|
| [Recordvelden](#recordvelden-2) | Typeoverzicht per veld voor één `sold-subscriptions`-record |
| [Voorbeeld-JSON](#voorbeeld-json-2) | Status van een echte responsvoorbeeld |

### Recordvelden

| API-veld | Spark-type | Nullable | Toelichting |
|---|---|---|---|
| `subscriptionKey` | `StringType` | nee | UUID. Unieke sleutel van het abonnement |
| `type` | `StringType` | ja | Type van de aankoop |
| `reservationKey` | `StringType` | ja | UUID. Unieke sleutel van de reservering. Er kunnen meerdere abonnementen in één reservering worden gekocht |
| `subscriptionTemplateKey` | `StringType` | nee | UUID. Unieke sleutel van het sjabloon. |
| `productName` | `StringType` | ja | Naam van het abonnementssjabloon |
| `saleDate` | `TimestampType` | ja | Datum waarop het abonnement is gekocht |
| `price` | `DoubleType` | nee | Verkoopprijs van het abonnement |
| `originalPrice` | `DoubleType` | ja | Oorspronkelijke prijs van het abonnement |
| `renewal` | `BooleanType` | nee | Indien true is dit abonnement een verlenging van een ander abonnement |
| `channel` | `StringType` | ja | Waar dit abonnement is gekocht, online of aan de kassa |
| `subscriptionHolderKey` | `StringType` | ja | UUID. Unieke sleutel van de abonnementhouder. Een houder kan meer dan één abonnement hebben |
| `internalId` | `StringType` | ja | Interne id van het abonnementssjabloon. Dit veld kan worden ingevuld op de pagina van het abonnementssjabloon a |
| `name` | `StringType` | ja | Naam van de abonnementhouder |
| `email` | `StringType` | ja | E-mailadres van de abonnementhouder |
| `street` | `StringType` | ja | Straat van de abonnementhouder |
| `houseNumber` | `StringType` | ja | Huisnummer van de abonnementhouder |
| `postalCode` | `StringType` | ja | Postcode van de abonnementhouder |
| `cityName` | `StringType` | ja | Plaats van de abonnementhouder |
| `countryCode` | `StringType` | ja | Landcode van de abonnementhouder |
| `lat` | `DoubleType` | ja | Breedtegraadwaarde van het adres van de abonnementhouder |
| `lon` | `DoubleType` | ja | Lengtegraadwaarde van het adres van de abonnementhouder |
| `validFrom` | `TimestampType` | ja | Startdatum van de geldigheid van het abonnement |
| `validTo` | `TimestampType` | ja | Einddatum van de geldigheid van het abonnement |
| `companyName` | `StringType` | ja | Bedrijfsnaam van de abonnementhouder |
| `firstName` | `StringType` | ja | Voornaam van de abonnementhouder |
| `middle` | `StringType` | ja | Tussenvoegsel van de abonnementhouder |
| `lastName` | `StringType` | ja | Achternaam van de abonnementhouder |
| `phoneNumber` | `StringType` | ja | Telefoonnummer van de abonnementhouder |
| `receiveNewsLetter` | `BooleanType` | ja | Geeft aan of de abonnementhouder de nieuwsbrief wil ontvangen |
| `paymentMethod` | `StringType` | ja | Betaalmethode waarmee het abonnement is gekocht |
| `nrOfSubscriptionProducts` | `IntegerType` | nee | Aantal abonnementskaarten |
| `cancelDate` | `TimestampType` | ja | Annuleringsdatum, indien van toepassing |
| `reservationNumber` | `StringType` | ja | Reserveringsnummer |
| `language` | `StringType` | ja | Naam van de taal van de reservering |
| `languageCode` | `StringType` | ja | Taalcode van de reservering |
| `loyaltyLevel` | `IntegerType` | ja | Loyaliteitsniveau van de abonnementhouder |
| `posGroupTitle` | `StringType` | ja | Titel van de POS-groep |
| `posTitle` | `StringType` | ja | Titel van de POS |
| `posContact` | `StringType` | ja | Naam van de POS-medewerker |
| `externalId` | `StringType` | ja | Externe id van het abonnementssjabloon |
| `testPayment` | `BooleanType` | nee | Geeft aan of het abonnement met een testbetaling is gekocht |
| `gender` | `StringType` | ja | Geslacht van de abonnementhouder |
| `birthDate` | `TimestampType` | ja | Geboortedatum van de abonnementhouder |
| `discountCode` | `StringType` | ja | Gebruikte kortingscode, indien van toepassing |
| `discountName` | `StringType` | ja | **Nieuw sinds 2026-07-17.** Naam van de gebruikte korting, indien van toepassing. Contract: `Name of the discount which was used, if any` |
| `creationDate` | `TimestampType` | nee | Aanmaakdatum van een reservering |
| `modificationDate` | `TimestampType` | ja | Wijzigingsdatum van een reservering |

### Voorbeeld-JSON

**UNKNOWN — niet vastgelegd.** Er zijn geen werkende v2-inloggegevens; op 2026-08-28 opnieuw bevestigd
(`invalid_client`, zie *Openstaande vragen* in het hoofdrapport). De typen hierboven zijn afgeleid van het
gepubliceerde OpenAPI 3.0.4-contract, opgehaald op 2026-08-28, niet van een waargenomen respons. Er zijn geen
voorbeelddata verzonnen.

---

## Ticketcounter v2 — veldencatalogus `scans`

Afgeleid van OpenAPI-schema `TC.Common.Models.Statistics.ScanInfo` (record key `scans`).
Onderdeel van [ticketcounter_research.md](../ticketcounter_research.md).

### Inhoudsopgave

| Sectie | Omschrijving |
|---------|-------------|
| [Recordvelden](#recordvelden-3) | Typeoverzicht per veld voor één `scans`-record |
| [Voorbeeld-JSON](#voorbeeld-json-3) | Status van een echte responsvoorbeeld |

### Recordvelden

| API-veld | Spark-type | Nullable | Toelichting |
|---|---|---|---|
| `scanId` | `IntegerType` | nee | Unieke id van de scan; bij handmatig inchecken is deze waarde 0 |
| `ticketCode` | `StringType` | ja | Barcodewaarde van het ticket of de abonnementskaart |
| `scanGroupName` | `StringType` | ja | De naam van de scangroep waar deze ticketcode is gescand |
| `deviceId` | `StringType` | ja | De ID van het apparaat dat dit ticket heeft gescand |
| `type` | `StringType` | ja | Type van de scan, bijv. Ticket of Subscription |
| `reservationKey` | `StringType` | ja | UUID. Unieke sleutel van de reservering waartoe dit ticket behoort |
| `subscriptionKey` | `StringType` | ja | UUID. Unieke sleutel van het abonnement |
| `subscriptionProductKey` | `StringType` | ja | UUID. Unieke sleutel van het abonnementsproduct |
| `scanDate` | `TimestampType` | nee | De datum waarop deze barcodewaarde is gescand |
| `subscriptionTemplateKey` | `StringType` | ja | UUID. Unieke sleutel van het abonnementssjabloon |
| `productName` | `StringType` | ja | Naam van het abonnementssjabloon |
| `eventName` | `StringType` | ja | Naam van het evenement |
| `performerName` | `StringType` | ja | Naam van de artiest |
| `internalId` | `StringType` | ja | Interne id van het abonnementssjabloon. Dit veld kan worden ingevuld op de pagina van het abonnementssjabloon a |
| `productInternalId` | `StringType` | ja | Interne id van het product. Dit veld bevat de informatie die op de productpagina is ingevuld voor interna |
| `name` | `StringType` | ja | Naam van de abonnementhouder of ticketkoper |
| `email` | `StringType` | ja | E-mailadres van de abonnementhouder of ticketkoper |
| `street` | `StringType` | ja | Straat van de abonnementhouder of ticketkoper |
| `houseNumber` | `StringType` | ja | Huisnummer van de abonnementhouder of ticketkoper |
| `postalCode` | `StringType` | ja | Postcode van de abonnementhouder of ticketkoper |
| `cityName` | `StringType` | ja | Plaats van de abonnementhouder of ticketkoper |
| `countryCode` | `StringType` | ja | Landcode van de abonnementhouder of ticketkoper |
| `lat` | `DoubleType` | ja | Breedtegraad van het adres van de abonnementhouder of ticketkoper |
| `lon` | `DoubleType` | ja | Lengtegraad van het adres van de abonnementhouder of ticketkoper |
| `eventKey` | `StringType` | ja | UUID. Unieke sleutel van een evenement |
| `performanceKey` | `StringType` | ja | UUID. Unieke sleutel van een voorstelling |
| `performanceSectionKey` | `StringType` | ja | UUID. Unieke sleutel van een sectie van een voorstelling |
| `validFrom` | `TimestampType` | ja | Startdatum van de geldigheid van een ticket of abonnement |
| `validTo` | `TimestampType` | ja | Einddatum van de geldigheid van een ticket of abonnement |
| `companyName` | `StringType` | ja | Bedrijfsnaam |
| `firstName` | `StringType` | ja | Voornaam van de koper |
| `middle` | `StringType` | ja | Tussenvoegsel van de koper |
| `lastName` | `StringType` | ja | Achternaam van de koper |
| `phoneNumber` | `StringType` | ja | Telefoonnummer van de koper |
| `reservationNumber` | `StringType` | ja | Nummer van de bestelling |
| `priceKey` | `StringType` | ja | UUID. Unieke sleutel van het daadwerkelijke product/tickettype dat is gekocht |
| `capacityNames` | `ArrayType(StringType)` | ja | Namen van de gebruikte capaciteiten/tijdsloten (indien aanwezig) |
| `price` | `DoubleType` | ja | Prijs per plaats of per abonnement |
| `originalPrice` | `DoubleType` | ja | Oorspronkelijke prijs per plaats of per abonnement |
| `externalId` | `StringType` | ja | Externe ID van het tickettype of abonnementssjabloon |
| `externalReservationNumber` | `StringType` | ja | Nummer van de bestelling in een extern systeem |
| `extraInfo1` | `StringType` | ja | Extra info 1 van de bestelling |
| `extraInfo2` | `StringType` | ja | Extra info 2 van de bestelling |
| `extraInfo3` | `StringType` | ja | Extra info 3 van de bestelling |
| `testPayment` | `BooleanType` | ja | Is gekocht met een testbetaling |
| `receiveNewsLetter` | `BooleanType` | ja | Geeft aan of de abonnementhouder of ticketkoper de nieuwsbrief wil ontvangen |
| `priceTypeName` | `StringType` | ja | Naam van het prijstype (type van het ticket). Alleen van toepassing op tickets. |

### Voorbeeld-JSON

**UNKNOWN — niet vastgelegd.** Er zijn geen werkende v2-inloggegevens; op 2026-08-28 opnieuw bevestigd
(`invalid_client`, zie *Openstaande vragen* in het hoofdrapport). De typen hierboven zijn afgeleid van het
gepubliceerde OpenAPI 3.0.4-contract, opgehaald op 2026-08-28, niet van een waargenomen respons. Er zijn geen
voorbeelddata verzonnen.

---

## Ticketcounter v2 — veldencatalogus `cancellations`

Afgeleid van OpenAPI-schema `TC.Common.Models.Statistics.CancellationsInfo` (record key `cancellations`).
Onderdeel van [ticketcounter_research.md](../ticketcounter_research.md).

### Inhoudsopgave

| Sectie | Omschrijving |
|---------|-------------|
| [Recordvelden](#recordvelden-4) | Typeoverzicht per veld voor één `cancellations`-record |
| [Voorbeeld-JSON](#voorbeeld-json-4) | Status van een echte responsvoorbeeld |

### Recordvelden

| API-veld | Spark-type | Nullable | Toelichting |
|---|---|---|---|
| `reservationKey` | `StringType` | ja | UUID. Unieke sleutel van de reservering. |
| `reservationNumber` | `StringType` | ja | Het reserveringsnummer. |
| `externalReservationNumber` | `StringType` | ja | Extern nummer van de reservering |
| `cancelDate` | `TimestampType` | ja | De datum van annulering |
| `price` | `DoubleType` | nee | Verkoopprijs per plaats |
| `originalPrice` | `DoubleType` | nee | Oorspronkelijke verkoopprijs per plaats |
| `nrOfSeats` | `IntegerType` | nee | Aantal plaatsen op dit ticket |
| `validFrom` | `TimestampType` | ja | Ticket geldig vanaf |
| `validTo` | `TimestampType` | ja | Ticket geldig tot |
| `ticketCode` | `StringType` | ja | De barcode van het ticket |
| `creationDate` | `TimestampType` | nee | Aanmaakdatum van een reservering |
| `modificationDate` | `TimestampType` | ja | Wijzigingsdatum van een reservering |

### Voorbeeld-JSON

**UNKNOWN — niet vastgelegd.** Er zijn geen werkende v2-inloggegevens; op 2026-08-28 opnieuw bevestigd
(`invalid_client`, zie *Openstaande vragen* in het hoofdrapport). De typen hierboven zijn afgeleid van het
gepubliceerde OpenAPI 3.0.4-contract, opgehaald op 2026-08-28, niet van een waargenomen respons. Er zijn geen
voorbeelddata verzonnen.

---

## Ticketcounter — impact van de migratie v1 naar v2

Delta tussen de **v1**-connector die vandaag in productie draait en de **v2**-API. Bijgewerkt op
2026-08-28 met live metingen op v1 en een verse ophaling van het v2-contract. Voor `sold-tickets`
staat de uitgewerkte versie in
[Delta v1 en v2 voor sold-tickets](#delta-v1-en-v2-voor-sold-tickets); dit hoofdstuk is het
overzicht over alle vijf entiteiten.

### Wijzigingsmatrix

| Gebied | v1 (vandaag in productie) | v2 | Impact |
|---|---|---|---|
| Auth-grant | `refresh_token` | `client_credentials` | Alleen configuratie; het framework ondersteunt beide |
| Token-endpoint | `https://api.ticketcounter.net/token` | `https://apiv2{test}.ticketcounter.eu/connect/token` | Alleen configuratie |
| Scope | geen | `TC.Tickets.API` | **Niet configureerbaar — geen kolom, generator emitteert het niet** |
| Inloggegevens | werkend (gemeten 2026-08-28) | **geweigerd, `invalid_client` (gemeten 2026-08-28)** | **Blokkade — nieuwe secrets nodig, per omgeving** |
| HTTP-werkwoord | `GET` plus query-string | `POST` plus JSON-body | **Blokkade — de body-opbouw voor REST bestaat niet** |
| UrlPath | `api/v1/statistics/...` | `api/v2/Statistics/...` | Alleen configuratie; let op de hoofdletter `S` en op `sold-tickets` met koppelteken |
| Hoofdlettergebruik velden | PascalCase | camelCase | **`03_schema.py` en `04_transforms.py` herschrijven** |
| Recordsleutel | `SoldTicketsInfo`, `Baskets`, `TicketScanInfo`, `SoldSubscriptionsInfo`, `Cancellations` | `soldTickets`, `baskets`, `scans`, `soldSubscriptions`, `cancellations` | Alleen configuratie, maar op alle vijf anders |
| Omhulsel | `Offset`, `ResultCount`, `Succeeded`, `ErrorMessage`, `IsRedirect`, `RedirectUrl`, `DisplayError` | idem in camelCase, plus `errorCode` | `ResultCountKey` aanpassen; `errorCode` is additief |
| Rate limit | **120 s per endpoint, HTTP 409** (gemeten) | niets gedocumenteerd | Kans op een fors kortere doorlooptijd; onbevestigd |
| Strategie | `chunk_offset` | `chunk_offset` | Ongewijzigd |
| Paginering | `offset` / `limit` in de query-string | `offset` / `limit` in de body, `limit` maximaal 100 000 | Transport wijzigt, model niet |
| Watermerkfilter | `fromDate` / `toDate`, `%Y-%m-%d` | `fromDate` / `toDate` als `date-time`, plus `modifiedFrom` / `modifiedTo` en `dateRangeType` | Echte change-data capture wordt mogelijk |

### Velddelta per entiteit

v1 live gemeten op 2026-08-28, v2 uit het contract van dezelfde dag. "Gedeeld" telt de velden die
in beide bestaan, ongeacht hoofdlettergebruik.

| Entiteit | v1 velden | v2 velden | Gedeeld | Alleen in v1 | Alleen in v2 |
|---|---|---|---|---|---|
| `sold_tickets` | 65 | 72 | 63 | `BuyingPrice`, `CountryName` | `capacityNames`, `countryCode`, `creationDate`, `discountCode`, `discountName`, `eventName`, `modificationDate`, `performerName`, `priceTypeName` |
| `sold_subscriptions` | 42 | 47 | 41 | `CountryName` | `countryCode`, `creationDate`, `discountCode`, `discountName`, `modificationDate`, `originalPrice` |
| `ticket_scans` | 44 | 47 | 42 | `BuyingPrice`, `CountryName` | `capacityNames`, `countryCode`, `eventName`, `performerName`, `priceTypeName` |
| `baskets` | 15 | 16 | 15 | — | `invitationCodes` |
| `cancellations` | 9 | 12 | 9 | — | `creationDate`, `modificationDate`, `ticketCode` |

**Op geen enkele entiteit heeft ook maar een veld dezelfde spelling in beide generaties.** De
hoofdletterwissel raakt dus letterlijk elke veldverwijzing in schema en transformaties, op alle
vijf entiteiten.

Twee velden verdwijnen structureel: `BuyingPrice` (inkoopprijs, op `sold_tickets` en
`ticket_scans`) en `CountryName` (op alle drie de entiteiten die adresgegevens dragen; v2 levert
alleen `countryCode`). Voor beide is een besluit nodig: vervangen, afleiden, of laten vervallen.

Verder verandert `basket.contact` van een enkel veld naar een geneste struct met 18 velden, en
krijgen vier van de vijf entiteiten een `modificationDate` die er nu niet is.

### Vervolgacties

Het `refresh-token`-secret kan pas na een aantoonbaar stabiele v2-periode worden uitgefaseerd — tot
dat moment is het het terugvalpad. Het configuratiesjabloon dat deze bron als canoniek voorbeeld
van het refresh-token-patroon noemt, moet worden bijgewerkt zodra v2 live is.

---

## Verzamel-endpoints v2 — dimensie- en referentiebronnen

> **Ongeverifieerd sinds 2026-07-17.** Dit hoofdstuk is niet opnieuw gecontroleerd tijdens de
> change-check van 2026-08-28: het valt buiten de vijf entiteiten die in productie draaien, en
> live aftasten is geblokkeerd door de inloggegevens. De bevindingen blijven staan omdat ze nog
> steeds de beste beschikbare kennis zijn, niet omdat ze opnieuw zijn bevestigd.

Dit hoofdstuk verfijnt de rij *Alle overige tags* uit het [Entiteitenoverzicht](#entiteitenoverzicht).
Het documenteert de **21 v2-endpoints die een verzameling (array) teruggeven** buiten de vijf
`Statistics`-feiten die hierboven al volledig zijn beschreven. Doel: bepalen welke ervan bruikbaar zijn als
**dimensie- of referentiebron** naast de bestaande feiten, welke puur **operationeel** zijn, en welke
**persoonsgegevens** bevatten.

- **Scope-afbakening.** De vijf `Statistics`-feiten blijven de enige *bevestigde* ingestie-scope. De negen
  kandidaten in Deel A zijn **voorstellen** ter aanvulling (dimensies), nog niet bevestigd.
- **Bewijsbasis.** Volledig afgeleid uit het gepubliceerde OpenAPI 3.0.4-contract (148 paden, 352 schema's).
  Er is **geen live call** uitgevoerd. Elk type hieronder is een door het contract gedeclareerd type, geen
  waargenomen type.
- **Blokkade op inloggegevens.** De bestaande v2-sleutels geven `invalid_client` op test *en* prod
  (ze werken alleen op v1). Daarom is de **Voorbeeld-JSON UNKNOWN voor alle 21 endpoints** — er is niets
  verzonnen.
- **Auth.** Identiek aan de feiten: het globale bearer-token met scope `TC.Tickets.API`. Geen van deze
  endpoints declareert een eigen `security`-override. Er zijn dus geen nieuwe inloggegevens nodig bovenop de
  (nog geblokkeerde) v2-clientinloggegevens.

### Inhoudsopgave verzamel-endpoints

| Deel | Endpoint | Record key | Aansluiting / reden |
|---|---|---|---|
| A. Kandidaat | [subscriptionTemplates](#subscriptiontemplates--get-apiv2subscriptiontemplates) | `subscriptionTemplates` | `subscriptionTemplateKey` → `sold_subscriptions` + `ticket_scans` (sterkste; enige met watermerk) |
| A. Kandidaat | [performances](#performances--get-apiv2eventsperformances) | `performances` | `eventKey` / `performanceKey` → `sold_tickets` + `ticket_scans` |
| A. Kandidaat | [prices](#prices--get-apiv2productspricetypeproducts) | `prices` | `priceKey` → `sold_tickets` + `ticket_scans` |
| A. Kandidaat | [paymentTypes](#paymenttypes--get-apiv2paymentspayment-types) | `paymentTypes` | Referentie; labelkoppeling op betaalmethode |
| A. Kandidaat | [predefinedReasons](#predefinedreasons--get-apiv2predefinedreasons) | `predefinedReasons` | Referentie (annulerings-/kortingsredenen); geen directe FK |
| A. Kandidaat | [discountReasons](#discountreasons--get-apiv2discountreasons) | `discountReasons` | Referentie (kortingsredenen); geen directe FK |
| A. Kandidaat | [ticketBundles](#ticketbundles--get-apiv2ticketbundles) | `ticketBundles` | Dunne samenvatting; geen FK in de feiten |
| A. Kandidaat | [statuses](#statuses--get-apiv2reservationspossible-statuses) | `statuses` | Statische enum-decode; geen statusveld in de feiten |
| A. Kandidaat | [soldCapacities](#soldcapacities--get-apiv2capacitiessold) | `soldCapacities` | Aggregaat per `priceKey`+datum; geen lijst-modus |
| B. Operationeel | [permissions](#permissions--get-apiv2pospermissions) | `permissions` | Autorisatie op tokenclaims |
| B. Operationeel | [printers](#printers--get-apiv2pospos-printers) | `printers` | POS-hardware |
| B. Operationeel | [templates](#templates--get-apiv2pospos-templates) | `templates` | POS-lay-outsjablonen |
| B. Operationeel | [printTemplates](#printtemplates--get-apiv2posprint-templates) | `printTemplates` | Printopmaak/-markup |
| B. Operationeel | [priceKeys](#pricekeys--get-apiv2posticket-prolongation-pricekeys) | `priceKeys` | POS-verlengingslookup |
| B. Operationeel | [commandScanDevices](#commandscandevices--get-apiv2scannerscommandscandevices) | `commandScanDevices` | Live scannerstatus |
| B. Operationeel | [reservations](#reservations--get-apiv2reservationspos-calendar) | `reservations` | POS-kalender + persoonsgegevens |
| B. Operationeel | [values](#values--get-apiv2webhooksretrieve-data) | `values` | Inkomende webhook-handler |
| C. Persoonsgegevens | [contacts](#contacts--get-apiv2contactsfind-finddebtor-findexternal-findnamebirthdate) | `contacts` | Zoekacties + pure PII — geen ingestiebron |

### Gedeelde responsvorm, paginering en watermerk

Vijf bevindingen gelden voor **alle 21** endpoints en bepalen samen de ingestiestrategie:

1. **Zelfde envelope, maar zonder pagineringsvelden.** Elke respons heeft dezelfde omhulsel-velden als de
   feiten — `succeeded`, `errorMessage`, `isRedirect`, `redirectUrl`, `displayError`, `errorCode` — plus de
   record-array(s). **Maar** anders dan de vijf `Statistics`-feiten bevat geen enkele envelope de velden
   `offset` of `resultCount`. De offset-lus van het framework (die stopt zodra `resultCount < PageSize`) heeft
   hier dus niets om op af te gaan.
2. **Geen offset/limit-paginering.** 19 van de 21 endpoints hebben **geen** `offset`/`limit`-parameter: het
   zijn **single-call full loads**. Alleen `Contacts/findexternal` en `Contacts/findnamebirthdate` accepteren
   `offset`/`limit` — en zelfs die missen `offset`/`resultCount` in de envelope, dus daar zou je moeten
   pagineren tot een lege array terugkomt. Voor de dimensiekandidaten is dit geen probleem: het zijn kleine
   referentietabellen die in één call passen.
3. **HTTP GET, geen POST-body.** Alle endpoints zijn `GET` met query-parameters. Ze raken dus **niet** de
   POST-met-JSON-body-blokkade die de vijf feiten wél treft (zie
   [Benodigde uitbreidingen aan general-notebooks](#benodigde-uitbreidingen-aan-general-notebooks)); de huidige
   GET+query-string-client kan ze ongewijzigd aanroepen. Let op: het pad `/api/v2/TicketBundles` host daarnaast
   een `POST` (aanmaken van een bundel) — gebruik uitdrukkelijk de `GET`-variant.
4. **Watermerk vrijwel afwezig.** Slechts één kandidaat draagt een echt wijzigingsveld
   (`subscriptionTemplates.lastUpdatedOn`). `soldCapacities` draagt alleen zakelijke tijdslot-datums, geen
   wijzigingsstempel. Alle overige endpoints hebben **geen enkel** datum-/wijzigingsveld → **alleen full load**.
   Bovendien biedt **geen** van deze endpoints een server-side `modified`-filterparameter, dus zelfs
   `subscriptionTemplates` moet volledig worden opgehaald (een max-kolom-watermerk kan hooguit client-side uit
   `lastUpdatedOn` worden afgeleid).
5. **Mediatypes & responscodes.** Elk endpoint declareert `text/plain`, `application/json` en `text/json` voor
   de 200-respons (dezelfde `text/plain`-eigenaardigheid als bij de feiten) en **alleen** een `200` — er is
   geen `429` of andere foutcode in het contract gedeclareerd.

### Deel A — Ingestie-kandidaten (dimensies)

Negen endpoints die (mogelijk) aansluiten op sleutels in de bestaande feiten. Per endpoint: het contract, waar
het op aansluit, en of het incrementeel kan.

#### subscriptionTemplates — GET /api/v2/SubscriptionTemplates

1. **Contract:** `GET /api/v2/SubscriptionTemplates` · tag `SubscriptionTemplates` · *"Obtains list of available subscription templates"*.
2. **Request:** optioneel `languageCode` (`string`, standaard `en-US`). **Geen** `offset`/`limit`, geen filter op wijziging. Single-call full load.
3. **Response:** record key `subscriptionTemplates`, items van schema `TC.Tickets.Models.Subscription.SubscriptionTemplateDetails` (24 velden, plus twee geneste sub-schema's).
4. **Watermerk:** `lastUpdatedOn` (`TimestampType`) staat op recordniveau → een client-side max-watermerk is mogelijk. Het endpoint biedt echter **geen** server-side filter, dus de ophaal blijft full load. `validFrom`/`validTo`/`startDate`/`endDate` zijn geldigheidsvensters, geen wijzigingsstempel.
5. **Aansluiting:** `subscriptionTemplateKey` → `sold_subscriptions.subscriptionTemplateKey` én `ticket_scans.subscriptionTemplateKey`. Sterkste koppeling van alle kandidaten (twee feiten) en rijkste payload. **Beste dimensiekandidaat.**
6. **Sample JSON:** `UNKNOWN — v2-inloggegevens ontbreken (invalid_client op test en prod)`.

| API-veld | Spark-type | Nullable | Toelichting |
|---|---|---|---|
| `subscriptionTemplateKey` | `StringType` | nee | UUID. Unieke sleutel van het abonnementssjabloon |
| `partnerKey` | `StringType` | nee | UUID. Partner waartoe dit sjabloon behoort |
| `name` | `StringType` | ja | Naam van het abonnement |
| `originalPrice` | `DoubleType` | ja | Oorspronkelijke prijs (voor het tonen van korting) |
| `price` | `DoubleType` | nee | Prijs per abonnement |
| `validFrom` | `TimestampType` | nee | Startdatum verkoopperiode |
| `validTo` | `TimestampType` | nee | Einddatum verkoopperiode |
| `startDate` | `TimestampType` | nee | Ingangsdatum geldigheid na aankoop |
| `endDate` | `TimestampType` | ja | Einddatum geldigheid na aankoop |
| `subscriptionType` | `IntegerType` | nee | Enum: `0`=`Period`, `1`=`Duration` |
| `durationType` | `IntegerType` | nee | Enum: `0`=`Year`, `1`=`Month`, `2`=`Week`, `3`=`Day` |
| `duration` | `IntegerType` | ja | Duur bij het gekozen `durationType` |
| `lastUpdatedOn` | `TimestampType` | ja | Datum waarop het sjabloon is bijgewerkt (**watermerk-kandidaat**) |
| `maximumQuantity` | `IntegerType` | nee | Max. aantal abonnementen per bestelling |
| `subscriptionTemplateProducts` | `ArrayType(StructType)` (sub-schema `SubscriptionTemplateProductDetails`) | ja | Producten van dit sjabloon |
| `tooltip` | `StringType` | ja | Tooltip voor de gebruiker |
| `cardTemplate` | `StringType` | ja | Sjabloon voor de abonnementskaart |
| `renewal` | `BooleanType` | nee | `true` = alleen voor verlenging bruikbaar |
| `externalId` | `StringType` | ja | Externe id |
| `scanningDisplayMessageTemplate` | `StringType` | ja | Sjabloon voor het scanbericht |
| `internalId` | `StringType` | ja | Interne id |
| `onlineNew` | `BooleanType` | nee | Bruikbaar online voor nieuwe aankoop |
| `onlineRenew` | `BooleanType` | nee | Bruikbaar online voor verlenging |
| `archived` | `BooleanType` | nee | Gearchiveerd |

Sub-schema `TC.Tickets.Models.Subscription.SubscriptionTemplateProductDetails`:

| API-veld | Spark-type | Nullable | Toelichting |
|---|---|---|---|
| `subscriptionTemplateKey` | `StringType` | nee | UUID |
| `productKey` | `StringType` | nee | UUID |
| `minimumNumberOfProduct` | `IntegerType` | ja |  |
| `maximumNumberOfProduct` | `IntegerType` | ja |  |
| `product` | `StructType` (sub-schema `ProductDetails`) | nee |  |
| `isInUse` | `BooleanType` | nee |  |
| `sendCardWithConfirmationMail` | `BooleanType` | nee |  |
| `lastUpdatedOn` | `TimestampType` | ja |  |
| `isTicketStrips` | `BooleanType` | nee |  |

Sub-schema `TC.Tickets.Models.Subscription.ProductDetails`:

| API-veld | Spark-type | Nullable | Toelichting |
|---|---|---|---|
| `productKey` | `StringType` | nee | UUID |
| `name` | `StringType` | ja |  |
| `pluralName` | `StringType` | ja |  |
| `description` | `StringType` | ja |  |
| `externalId` | `StringType` | ja |  |
| `areaCode` | `StringType` | ja |  |
| `ticketCodeBatchId` | `IntegerType` | ja |  |
| `minimumAge` | `IntegerType` | ja |  |
| `maximumAge` | `IntegerType` | ja |  |
| `internalId` | `StringType` | ja |  |

#### performances — GET /api/v2/Events/performances

1. **Contract:** `GET /api/v2/Events/performances` · tag `Events` · *"Get the combination of event-performances for current sales channel"*.
2. **Request:** optioneel `languageCode` (`string`, standaard `en-US`). **Geen** `offset`/`limit`, geen wijzigingsfilter. Single-call full load. Let op: *"for current sales channel"* — de lijst is gescoped op het verkoopkanaal van het token.
3. **Response:** record key `performances`, items van schema `TC.Common.Models.Event.EventPerformanceInfo` (6 velden). **Naamgevingsvalstrik:** elk element van de array `performances` is een **evenement** (`EventPerformanceInfo`) dat op zijn beurt een geneste array `performances[]` met de eigenlijke voorstellingen bevat.
4. **Watermerk:** **geen.** Geen wijzigingsveld; `startDateTime` is de voorstellingsdatum. Alleen full load.
5. **Aansluiting:** `eventKey` → `sold_tickets.eventKey` én `ticket_scans.eventKey`; geneste `performanceKey` → `sold_tickets.performanceKey` én `ticket_scans.performanceKey`. Levert daarnaast `eventName`/`performanceName` als labels. Op één na sterkste kandidaat (twee sleutels, twee feiten).
6. **Sample JSON:** `UNKNOWN — v2-inloggegevens ontbreken (invalid_client op test en prod)`.

| API-veld | Spark-type | Nullable | Toelichting |
|---|---|---|---|
| `eventKey` | `StringType` | nee | UUID. Unieke sleutel van het evenement |
| `eventName` | `StringType` | ja | Naam van het evenement |
| `tagline` | `StringType` | ja | Slagzin |
| `description` | `StringType` | ja | Beschrijving |
| `partnerKey` | `StringType` | nee | UUID |
| `performances` | `ArrayType(StructType)` (sub-schema `EventPerformanceDetailsInfo`) | ja | Voorstellingen binnen dit evenement |

Sub-schema `TC.Common.Models.Event.EventPerformanceDetailsInfo`:

| API-veld | Spark-type | Nullable | Toelichting |
|---|---|---|---|
| `performanceKey` | `StringType` | nee | UUID. Unieke sleutel van de voorstelling |
| `startDateTime` | `TimestampType` | ja | Start van de voorstelling |
| `performanceName` | `StringType` | ja | Naam van de voorstelling |
| `performanceDescription` | `StringType` | ja | Beschrijving van de voorstelling |
| `sortOrder` | `IntegerType` | nee | Sorteervolgorde |

#### prices — GET /api/v2/Products/pricetypeproducts

1. **Contract:** `GET /api/v2/Products/pricetypeproducts` · tag `Products` · *"Obtains price type products accessible by the current sales channel"*.
2. **Request:** optioneel `capacityDate` (`date-time`), `languageId` (`int32`, standaard `0`, **obsolete** — gebruik `languageCode`), `languageCode` (`string`, standaard `en-US`). **Geen** `offset`/`limit`. Single-call full load, gescoped op het verkoopkanaal van het token.
3. **Response:** record key `prices`, items van schema `TC.Tickets.Models.Product.PriceTypeProduct` (6 velden).
4. **Watermerk:** **geen.** Alleen full load.
5. **Aansluiting:** `priceKey` → `sold_tickets.priceKey` én `ticket_scans.priceKey`. Let op: er is **geen veld** `productName`; de weergavenaam van het product zit in `friendlyName`. De feiten dragen `productName`/`priceTypeName` als tekst — de koppeling gaat op `priceKey`.
6. **Sample JSON:** `UNKNOWN — v2-inloggegevens ontbreken (invalid_client op test en prod)`.

| API-veld | Spark-type | Nullable | Toelichting |
|---|---|---|---|
| `priceKey` | `StringType` | nee | UUID. Unieke sleutel van het prijstype/product |
| `partnerKey` | `StringType` | nee | UUID |
| `price` | `DoubleType` | nee | Prijs |
| `friendlyName` | `StringType` | ja | Weergavenaam van het product |
| `partnerName` | `StringType` | ja | Naam van de partner |
| `notificationMessage` | `StringType` | ja | Meldingstekst |

#### paymentTypes — GET /api/v2/Payments/payment-types

1. **Contract:** `GET /api/v2/Payments/payment-types` · tag `Payments` · *"Obtains list of all supported payment types in the system"*.
2. **Request:** **geen** parameters. Single-call full load. Dit is een **systeembrede** lijst (alle ondersteunde betaaltypes), niet tenant-specifiek.
3. **Response:** record key `paymentTypes`, items van schema `TC.Common.Models.Payment.PaymentTypeInfo` (4 velden).
4. **Watermerk:** **geen.** Alleen full load.
5. **Aansluiting:** **referentietabel, geen schone FK.** De feiten dragen de betaling als tekst (`baskets.payments[].paymentType`, `sold_tickets.paymentMethod`, `sold_subscriptions.paymentMethod`), terwijl deze tabel `id` (`int`) + `title` + twee enums heeft. De koppeling gaat dus op naam/label, niet op sleutel — bruikbaar als decodetabel, niet als strikte dimensie.
6. **Sample JSON:** `UNKNOWN — v2-inloggegevens ontbreken (invalid_client op test en prod)`.

| API-veld | Spark-type | Nullable | Toelichting |
|---|---|---|---|
| `id` | `IntegerType` | nee | Interne id van het betaaltype |
| `title` | `StringType` | ja | Weergavenaam |
| `paymentProcessType` | `IntegerType` | nee | Enum (13): `0`=`None`, `1`=`Cash`, `2`=`PIN`, `3`=`Invoice`, `4`=`DepotApi`, `5`=`DepotReseller`, `6`=`Online`, `7`=`Recurring`, `8`=`PaperVoucher`, `9`=`Intersolve_Voucher`, `10`=`Intersolve_Giftcard`, `11`=`FashionCheque`, `12`=`CcvConnect` |
| `paymentMethod` | `IntegerType` | nee | Grote enum (~103 leden): `0`=`iDeal`, `1`=`CreditCard`, `2`=`Internet`, `3`=`GiftCard`, … `24`=`Cash`, `25`=`Invoice`, … `100`=`ApplePay`, `101`=`GooglePay`, `-1`=`Unknown` |

#### predefinedReasons — GET /api/v2/PredefinedReasons

1. **Contract:** `GET /api/v2/PredefinedReasons` · tag `PredefinedReasons` · *"Gets predefined reasons"*.
2. **Request:** optionele filters `isDiscountReason` (`bool`) en `isCancellationReason` (`bool`). **Geen** `offset`/`limit`. Single-call full load.
3. **Response:** record key `predefinedReasons`, items van schema `TC.Common.Models.Discount.PredefinedReason` (5 velden).
4. **Watermerk:** **geen.** Alleen full load.
5. **Aansluiting:** referentie/lookup voor annulerings- en kortingsredenen. De huidige feiten dragen **geen** reden-sleutel (`cancellations` heeft geen reden-veld; `sold_tickets`/`sold_subscriptions` dragen `discountCode` als tekst, niet dit `id`). **Geen directe FK** in de bestaande entiteiten → losstaande referentietabel.
6. **Sample JSON:** `UNKNOWN — v2-inloggegevens ontbreken (invalid_client op test en prod)`.

| API-veld | Spark-type | Nullable | Toelichting |
|---|---|---|---|
| `id` | `IntegerType` | nee |  |
| `reason` | `StringType` | ja | Reden (tekst) |
| `isDiscountReason` | `BooleanType` | nee | Is een kortingsreden |
| `isCancellationReason` | `BooleanType` | nee | Is een annuleringsreden |
| `cancellationAmountPercentage` | `DoubleType` | ja | Percentage van het te annuleren bedrag |

#### discountReasons — GET /api/v2/Discount/reasons

1. **Contract:** `GET /api/v2/Discount/reasons` · tag `Discount` · *"Gets discount's reasons"*.
2. **Request:** **geen** parameters. Single-call full load.
3. **Response:** record key `discountReasons`, items van schema `TC.Common.Models.Discount.DiscountReason` (2 velden).
4. **Watermerk:** **geen.** Alleen full load.
5. **Aansluiting:** dunne referentie (id + reden); overlapt met `predefinedReasons` (met `isDiscountReason=true`). **Geen directe FK** in de feiten (`discountCode` is een code-tekst, niet dit `id`) → losstaande referentietabel.
6. **Sample JSON:** `UNKNOWN — v2-inloggegevens ontbreken (invalid_client op test en prod)`.

| API-veld | Spark-type | Nullable | Toelichting |
|---|---|---|---|
| `id` | `IntegerType` | nee |  |
| `reason` | `StringType` | ja | Kortingsreden (tekst) |

#### ticketBundles — GET /api/v2/TicketBundles

1. **Contract:** `GET /api/v2/TicketBundles` · tag `TicketBundles` · *"Gets ticket bundles"*. **Let op:** hetzelfde pad host ook een `POST` (*"Adds new ticket bundle"*, schrijfactie) — gebruik uitdrukkelijk de `GET`.
2. **Request:** optioneel `searchPhrase` (`string`) en `archived` (`bool`). **Geen** `offset`/`limit`. `searchPhrase` maakt dit deels zoek-georiënteerd, maar met `archived` is een volledige lijst op te vragen. Single-call full load.
3. **Response:** record key `ticketBundles`, items van schema `TC.Common.Models.TicketBundle.TicketBundleSummary` (3 velden).
4. **Watermerk:** **geen.** Alleen full load.
5. **Aansluiting:** dunne samenvatting (barcode + aantal + gearchiveerd). `bundleBarcode` komt **niet** voor in de vijf feiten; de losse ticketcodes van een bundel zitten alleen achter een sub-endpoint (`/{bundleBarcode}/tickets`). Deze lijst alleen heeft dus **geen FK** naar de feiten — marginale dimensiewaarde.
6. **Sample JSON:** `UNKNOWN — v2-inloggegevens ontbreken (invalid_client op test en prod)`.

| API-veld | Spark-type | Nullable | Toelichting |
|---|---|---|---|
| `bundleBarcode` | `StringType` | ja | Barcode van de bundel |
| `nrOfBarcodes` | `IntegerType` | nee | Aantal barcodes in de bundel |
| `isArchived` | `BooleanType` | nee | Gearchiveerd |

#### statuses — GET /api/v2/Reservations/possible-statuses

1. **Contract:** `GET /api/v2/Reservations/possible-statuses` · tag `Reservations` · *"Retrieves list of all possible reservation statuses"*.
2. **Request:** **geen** parameters. Single-call full load.
3. **Response:** record key `statuses`, items van schema `TC.Common.Models.Reservation.ReservationStatusInfo` (2 velden).
4. **Watermerk:** **geen** — statische enum-decode. Alleen full load (verandert vrijwel nooit).
5. **Aansluiting:** statische **enum-decodetabel** (statuscode → naam), identiek voor alle klanten. De `Statistics`-feiten dragen momenteel geen reserveringsstatusveld, dus er is **geen directe FK**. Pure referentie; alleen nuttig als er later een statuskolom wordt ingelezen.
6. **Sample JSON:** `UNKNOWN — v2-inloggegevens ontbreken (invalid_client op test en prod)`.

| API-veld | Spark-type | Nullable | Toelichting |
|---|---|---|---|
| `statusValue` | `IntegerType` | nee | Enum (13): `0`=`Unknown`, `1`=`Unconfirmed`, `2`=`WaitingForPayment`, `3`=`PaymentRetry`, `4`=`PaymentUncertain`, `5`=`Canceled`, `6`=`Declined`, `7`=`Confirmed`, `8`=`WaitingForPSPAnswer`, `9`=`HandledByPartner`, `10`=`ConfirmedPrintTickets`, `11`=`Blocked`, `12`=`Abandoned` |
| `statusName` | `StringType` | ja | Naam van de status |

#### soldCapacities — GET /api/v2/Capacities/sold

1. **Contract:** `GET /api/v2/Capacities/sold` · tag `Capacities` · *"Obtains list of capacities that have at least one reservation linked with the count of those linked reservations."*.
2. **Request:** optioneel `priceKey` (`uuid`), `startDate` (`date-time`), `endDate` (`date-time`; leeg = één dag). **Geen** `offset`/`limit`. De parameters zijn in de spec optioneel, maar **semantisch nodig**: het endpoint geeft capaciteiten per `priceKey` + datumvenster. Er is **geen "alles"-modus**.
3. **Response:** record key `soldCapacities`, items van schema `TC.Tickets.Models.Capacity.SoldCapacityDetails` (3 velden).
4. **Watermerk:** **geen wijzigingsstempel.** `capacityStartTime`/`capacityEndTime` zijn de tijdslot-grenzen (zakelijke datums), geen change-tracking.
5. **Aansluiting:** dit is een **aggregaat/afgeleide metriek** (aantal gekoppelde reserveringen per tijdslot voor één `priceKey`) — het gedraagt zich als een feit/metriek, niet als dimensie. Omdat het `priceKey` + datum vereist en geen lijst-modus heeft, kan het niet als platte dimensie worden ingelezen zonder te itereren over elke `priceKey` × datum. **Valt tussen wal en schip.**
6. **Sample JSON:** `UNKNOWN — v2-inloggegevens ontbreken (invalid_client op test en prod)`.

| API-veld | Spark-type | Nullable | Toelichting |
|---|---|---|---|
| `capacityStartTime` | `TimestampType` | nee | Starttijd van het tijdslot |
| `capacityEndTime` | `TimestampType` | nee | Eindtijd van het tijdslot |
| `reservationsCount` | `IntegerType` | nee | Aantal gekoppelde reserveringen |

### Deel B — Operationeel / geen ingestiebron

Acht endpoints die wél een verzameling teruggeven, maar **geen ingestiebron** zijn. Per endpoint staat expliciet
waarom het afvalt.

#### permissions — GET /api/v2/Pos/permissions

1. **Contract:** `GET /api/v2/Pos/permissions` · tag `Pos` · *"Retrieves the list of permissions based on the claims"*.
2. **Request:** **geen** parameters. Single-call.
3. **Response:** record key `permissions` = `ArrayType(StringType)` — een platte lijst rechten-strings (geen itemschema).
4. **Watermerk:** **geen.**
5. **Waarom het afvalt:** autorisatiegegevens op basis van de **claims van het aanroepende token**, niet van de klant. Verandert per token/gebruiker; geen entiteit, geen sleutel, geen analytische waarde.
6. **Sample JSON:** `UNKNOWN — v2-inloggegevens ontbreken (invalid_client op test en prod)`.

#### printers — GET /api/v2/Pos/pos-printers

1. **Contract:** `GET /api/v2/Pos/pos-printers` · tag `Pos` · *"Retrieve list of POS printers"*.
2. **Request:** **geen** parameters. Single-call.
3. **Response:** record key `printers`, items van schema `TC.Common.Models.Pos.PosPrinterInfo` (`id` `IntegerType`, `title` `StringType`, `archived` `BooleanType`).
4. **Watermerk:** **geen.**
5. **Waarom het afvalt:** POS-hardwareconfiguratie (printers aan de kassa). Operationele apparaatinventaris zonder analytische waarde en zonder FK naar de feiten.
6. **Sample JSON:** `UNKNOWN — v2-inloggegevens ontbreken (invalid_client op test en prod)`.

#### templates — GET /api/v2/Pos/pos-templates

1. **Contract:** `GET /api/v2/Pos/pos-templates` · tag `Pos` · *"Retrieve templates"*.
2. **Request:** **geen** parameters. Single-call.
3. **Response:** record key `templates`, items van schema `TC.Common.Models.Pos.PosTemplateInfo` (`id`, `salesChannelId`, `title`, `languageId`, `languageCode`, `archived`).
4. **Watermerk:** **geen.**
5. **Waarom het afvalt:** POS-UI/lay-outsjablonen. Operationele configuratie zonder analytische waarde.
6. **Sample JSON:** `UNKNOWN — v2-inloggegevens ontbreken (invalid_client op test en prod)`.

#### printTemplates — GET /api/v2/Pos/print-templates

1. **Contract:** `GET /api/v2/Pos/print-templates` · tag `Pos` · *"Retrieve a list of POS print templates"*.
2. **Request:** optioneel `allowNonPosTemplates` (`bool`, standaard `false`). Single-call.
3. **Response:** **twee** arrays — `printTemplates` (schema `TC.Common.Models.Pos.PosPrintTemplateInfo`: `id`, `isPosTemplate`, `title`, `posPrintTemplateType` enum `0`=`Receipt`/`1`=`Ticket`/`2`=`PinReceipt`/`3`=`Download`/`4`=`Subscription`/`5`=`CashCount`, `content`, `archived`) en `defaultPrintTemplateMappings` (schema `TC.Common.Models.Pos.DefaultPrintTemplateMappingInfo` is in de spec **leeg** — `{}`, geen gedefinieerde velden).
4. **Watermerk:** **geen.**
5. **Waarom het afvalt:** printopmaak/-markup (bonnen, tickets); `content` bevat sjabloon-markup. Operationele configuratie zonder analytische waarde.
6. **Sample JSON:** `UNKNOWN — v2-inloggegevens ontbreken (invalid_client op test en prod)`.

#### priceKeys — GET /api/v2/Pos/ticket-prolongation-pricekeys

1. **Contract:** `GET /api/v2/Pos/ticket-prolongation-pricekeys` · tag `Pos` · *"Retrieve a list of price keys for ticket prolongation"*.
2. **Request:** **geen** parameters. Single-call.
3. **Response:** record key `priceKeys`, items van schema `TC.Tickets.Models.PriceKeys.PriceKeyProlongationInfo` (`priceKey` `StringType`, `prolongation` `StringType`).
4. **Watermerk:** **geen.**
5. **Waarom het afvalt:** POS-lookup voor ticketverlenging aan de kassa (welke prijssleutels bruikbaar zijn om te verlengen). `priceKey` overlapt met de dimensie `prices`, maar het doel is de POS-verlengingsflow — smalle operationele configuratie, geen dimensie.
6. **Sample JSON:** `UNKNOWN — v2-inloggegevens ontbreken (invalid_client op test en prod)`.

#### commandScanDevices — GET /api/v2/Scanners/commandscandevices

1. **Contract:** `GET /api/v2/Scanners/commandscandevices` · tag `Scanners` · *"Obtains scan devices with enabled commands"*.
2. **Request:** **geen** parameters. Single-call.
3. **Response:** record key `commandScanDevices`, items van schema `TC.Common.DataAccess.Dto.Scanning.CommandScanDeviceDto` (`deviceId` `StringType`, `scannerName` `StringType`, `isConnected` `BooleanType`).
4. **Watermerk:** **geen.**
5. **Waarom het afvalt:** live status van scanners (verbonden/niet). Realtime apparaatstatus, geen historische bedrijfsdata.
6. **Sample JSON:** `UNKNOWN — v2-inloggegevens ontbreken (invalid_client op test en prod)`.

#### reservations — GET /api/v2/Reservations/pos-calendar

1. **Contract:** `GET /api/v2/Reservations/pos-calendar` · tag `Reservations` · *"Obtains reservation information required for pos calendar"*.
2. **Request:** optioneel `priceKey` (`uuid`), `startTime` (`date-time`), `endTime` (`date-time`). **Geen** `offset`/`limit`. Semantisch gescoped op `priceKey` + tijdslot; geen "alles"-modus.
3. **Response:** record key `reservations`, items van schema `TC.Tickets.Models.Reservation.ReservationPosCalendarDetails` (`reservationKey`, `reservationNumber`, `firstName`, `lastName`, `middle`, `mailAddress`).
4. **Watermerk:** **geen.**
5. **Waarom het afvalt:** **dubbele reden.** (a) POS-kalenderweergave, alleen gescoped op `priceKey` + tijdslot (geen lijst-modus), én (b) het bevat **persoonsgegevens** (`firstName`, `lastName`, `mailAddress`) zónder `excludeContactInfo`-schakelaar. Operationele kassabalie-kalender, geen ingestiebron.
6. **Sample JSON:** `UNKNOWN — v2-inloggegevens ontbreken (invalid_client op test en prod)`.

#### values — GET /api/v2/Webhooks/retrieve-data

1. **Contract:** `GET /api/v2/Webhooks/retrieve-data` · tag `Webhooks` · *"Handles webhook call from third parties to retrieve data (for example for number of scans)"*.
2. **Request:** **geen** parameters. Single-call.
3. **Response:** record key `values`, items van schema `TC.Tickets.Models.Webhooks.NameValues` (`name` `StringType`, `value` `StringType`).
4. **Watermerk:** **geen.**
5. **Waarom het afvalt:** dit is een **inkomende webhook-handler** (derden roepen dit aan om bijvoorbeeld scanaantallen op te halen), geen bladerbare dataset. Retourneert generieke naam/waarde-paren. Geen ingestiebron.
6. **Sample JSON:** `UNKNOWN — v2-inloggegevens ontbreken (invalid_client op test en prod)`.

### Deel C — Persoonsgegevens (zoekacties, geen ingestiebron)

Vier `Contacts`-endpoints die alle **dezelfde** verzameling teruggeven (record key `contacts`, schema
`TC.Common.Models.Contact.ContactDetails`). Ze worden hier gedocumenteerd, maar zijn **nadrukkelijk geen
ingestiebron**.

#### contacts — GET /api/v2/Contacts/find, /finddebtor, /findexternal, /findnamebirthdate

1. **Contract:** tag `Contacts`. Vier endpoints, één responsschema:
   - `GET /api/v2/Contacts/find` — *"Searches for a contact"*
   - `GET /api/v2/Contacts/finddebtor` — *"Searches for a debtors on Vat and country combination"*
   - `GET /api/v2/Contacts/findexternal` — *"Searches for a contact with an external Id"*
   - `GET /api/v2/Contacts/findnamebirthdate` — *"Searches for a contact based on name and birthdate"*
2. **Request:** alle parameters staan als optioneel gedeclareerd, maar het zijn **zoekacties** die criteria vereisen:
   - `find`: `mailAddress`, `externalId`, `includeInactiveAccounts` (`bool`, standaard `true`)
   - `finddebtor`: `vatNumber`, `countryId` (`int32`), `countryCode`
   - `findexternal`: `keyWord`, `offset` (`int32`), `limit` (`int32`)
   - `findnamebirthdate`: `firstName`, `middleName`, `lastName`, `birthDate` (`date-time`), `offset` (`int32`), `limit` (`int32`)
   Alleen `findexternal` en `findnamebirthdate` bieden `offset`/`limit` — en dan nog binnen een zoekfilter, zonder `offset`/`resultCount` in de envelope.
3. **Response:** record key `contacts`, items van schema `TC.Common.Models.Contact.ContactDetails` (29 velden, incl. het geneste `address`).
4. **Watermerk:** **geen** (`birthDate` is PII, geen wijzigingsstempel). Een full load is sowieso onmogelijk (geen lijst-modus).
5. **Waarom het geen ingestiebron is:**
   - **Zoekacties, geen lijst.** Er is **geen "alle contacten"-modus**: je moet al weten wie je zoekt (mail, btw+land, keyword, of naam+geboortedatum).
   - **Pure persoonsgegevens.** De hele payload is klant-PII (naam, geboortedatum, e-mail, telefoon, volledig adres, btw-nummer, opt-ins, `deceased`). Anders dan de feiten is er **geen** `excludeContactInfo`-schakelaar — het doel van het endpoint is juist de persoon teruggeven.
   - **Opname zou klantgegevens in Bronze zetten** — tegen de guard rails (`contracts/agent-behavior.md`, `contracts/sensitive-data-handling/README.md`). De feiten dragen de contact-**sleutel** al (`contactHolderKey` / `subscriptionHolderKey` / `contact.contactKey`) voor koppelingen; de persoonsattributen horen niet integraal gekopieerd te worden.
6. **Sample JSON:** `UNKNOWN — v2-inloggegevens ontbreken (invalid_client op test en prod)`. En zelfs mét inloggegevens zou een echte respons ruwe PII zijn die niet in de repo mag landen.

| API-veld | Spark-type | Nullable | Toelichting |
|---|---|---|---|
| `contactKey` | `StringType` | ja | Sleutel van het contact voor verdere communicatie |
| `companyName` | `StringType` | ja | Bedrijfsnaam |
| `vatNumber` | `StringType` | ja | Btw-nummer |
| `gender` | `StringType` | ja | Geslacht ('M'/'F') |
| `firstName` | `StringType` | ja | Voornaam |
| `middle` | `StringType` | ja | Tussenvoegsel |
| `lastName` | `StringType` | ja | Achternaam |
| `birthDate` | `TimestampType` | ja | Geboortedatum |
| `phoneNumber` | `StringType` | ja | Telefoonnummer |
| `mobileNumber` | `StringType` | ja | Mobiel nummer |
| `mailAddress` | `StringType` | ja | E-mailadres |
| `receiveNewsletter` | `BooleanType` | nee | Nieuwsbrief gewenst |
| `receiveInvoice` | `BooleanType` | nee | Factuur gewenst |
| `optin1` | `BooleanType` | nee | Opt-in voor eigen optie 1 |
| `optin2` | `BooleanType` | nee | Opt-in voor eigen optie 2 |
| `optin3` | `BooleanType` | nee | Opt-in voor eigen optie 3 |
| `address` | `StructType` (sub-schema `AddressDetails`) | nee | Adres |
| `fullName` | `StringType` | ja | Volledige naam |
| `languageCode` | `StringType` | ja | Taalcode van het contact |
| `receivePassbooks` | `BooleanType` | nee | Passbook-tickets gewenst |
| `externalId` | `StringType` | ja | Externe id van het contact |
| `contactInfo1` | `StringType` | ja | Extra contactinfo 1 |
| `contactInfo2` | `StringType` | ja | Extra contactinfo 2 |
| `contactInfo3` | `StringType` | ja | Extra contactinfo 3 |
| `contactInfo4` | `StringType` | ja | Extra contactinfo 4 |
| `deceased` | `BooleanType` | nee | Overleden |
| `isDisabled` | `BooleanType` | nee | Uitgeschakeld |
| `isAccountHolder` | `BooleanType` | nee | Is accounthouder |
| `isActiveAccount` | `BooleanType` | nee | Is een actief account |

Sub-schema `TC.Common.Models.Contact.AddressDetails`:

| API-veld | Spark-type | Nullable | Toelichting |
|---|---|---|---|
| `street` | `StringType` | ja | Straat |
| `number` | `StringType` | ja | Huisnummer |
| `extraAddressLine` | `StringType` | ja | Extra adresregel |
| `postalCode` | `StringType` | ja | Postcode |
| `cityName` | `StringType` | ja | Plaats |
| `stateName` | `StringType` | ja | Provincie/staat |
| `lat` | `DoubleType` | ja | Breedtegraad |
| `lon` | `DoubleType` | ja | Lengtegraad |
| `countryCode` | `StringType` | ja | ISO-landcode |
