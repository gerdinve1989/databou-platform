# Ticketcounter API-onderzoek

researched_at: 2026-07-17
checked_at: 2026-09-04
checked_by: research agent (live meetronde op v2, samengevoegd met het bestaande rapport)
source_type: api
overall_verdict: REVIEW — v2 is live gemeten en bruikbaar; de eerder gemelde blokkades bestaan niet meer

Onderzoek naar **TC.Tickets.API**. Er draaien twee generaties naast elkaar: een **legacy v1**
`Statistics`-API op `api.ticketcounter.net`, waarop bestaande connectoren produceren, en de
**v2**-API op de `apiv2`-hosts. Dit rapport documenteert de verbinding met beide en de delta die
een migratie v1 → v2 moet afdekken.

> **Reikwijdte is op 04-09-2026 versmald, en dat is aan dit rapport te zien.**
> Research levert nog uitsluitend **de verbinding met de bron**: `source_config` (sectie 1) en
> `entity_ingestion_config` (sectie 2). Alles wat een **telling** is — veldtypen, vulgraden,
> volumes, kardinaliteit, uniciteit van de sleutel, hoe ver de historie teruggaat — is uit dit
> rapport **verwijderd** en wordt door config-builder uit de **gelande Bronze-data** bepaald.
> Reden: vanuit de bron is dat een steekproef, vanuit Bronze een telling, en een steekproef geeft
> een ander antwoord dan de werkelijkheid. De vorige versie van dit rapport droeg vijf
> veldencatalogi met Spark-typen en nullability per veld; die zijn hier vervangen door
> [Response Shape per Entity](#response-shape-per-entity), dat alleen de **vorm** vastlegt.
> Zoek je die typen: ze komen terug uit Bronze, niet uit dit document.

## Inhoudsopgave

| Sectie | Omschrijving |
|---------|-------------|
| [Aanleiding en oordeel](#aanleiding-en-oordeel) | Waar dit onderzoek vandaan komt en wat eruit komt |
| [Wat deze ronde corrigeert](#wat-deze-ronde-corrigeert) | Vier bevindingen die de vorige versie tegenspreken |
| [Twee kopieën van dit rapport](#twee-kopieën-van-dit-rapport) | Divergentie tussen clientrepo en platformregister |
| [TypeSource](#typesource) | Bevestigd bronprotocol |
| [Overzicht](#overzicht) | Wat v1 en v2 zijn en hoe ze zijn onderzocht |
| [Twee hostfamilies](#twee-hostfamilies--net-en-eu-dragen-hetzelfde-contract) | `.net` en `.eu` dragen hetzelfde contract, maar niet dezelfde klanten |
| [Authenticatie](#authenticatie) | De `api_key`-grant, de valstrik die uren kost, de secretnamen |
| [Toegang per rol](#toegang-per-rol--buiten-statistics-is-het-403) | Wat een Statistics-sleutel wel en niet mag |
| [Verbinding](#verbinding) | BaseUrl, RateLimitDelay, ApiHeaders |
| [Rate limits](#rate-limits) | Gemeten voor beide generaties |
| [Entiteitenoverzicht](#entiteitenoverzicht) | Endpoints binnen en buiten scope |
| [Contract van de request body](#contract-van-de-request-body) | Filters, offset/limit en de datumbereik-enum |
| [Paginering en ingestie per entiteit](#paginering-en-ingestie-per-entiteit) | Sectie 2: strategie, watermerk, pagineerparameters |
| [Response Shape per Entity](#response-shape-per-entity) | Omhulsel, recordsleutel, veldnamen, datumopmaak |
| [Delta v1 → v2 voor de verbinding](#delta-v1--v2-voor-de-verbinding) | Wat er breekt aan transport, auth en paginering |
| [Uitfasering van v1](#uitfasering-van-v1) | Wat er wel en niet over te vinden is |
| [Gemengd draaien](#gemengd-draaien-één-entiteit-op-v2-de-rest-op-v1) | Kan één entiteit vooruit? |
| [Migratieplan](#migratieplan) | Genummerde stappen plus terugvalpad |
| [Benodigde uitbreidingen aan general-notebooks](#benodigde-uitbreidingen-aan-general-notebooks) | Geen — en waarom dat veranderd is |
| [Openstaande vragen / UNKNOWNs](#openstaande-vragen--unknowns) | Alles wat niet is geverifieerd |
| [Vragen aan de leverancier](#vragen-aan-de-leverancier) | Wat alleen de leverancier kan beantwoorden |
| [Verzamel-endpoints v2](#verzamel-endpoints-v2--dimensie--en-referentiebronnen) | De 21 endpoints buiten de vijf Statistics-feiten |

## Aanleiding en oordeel

**De melding van de leverancier:** *"Discount Name is toegevoegd aan de response van het
sold-tickets endpoint. Dit is alleen toegevoegd aan de API V2. De aanpassing is inmiddels
doorgevoerd."*

**De vraag:** kunnen we over naar API v2?

### Oordeel: JA

v2 werkt. De tokenaanvraag slaagt, alle vijf `Statistics`-endpoints geven HTTP 200, de paginering
is gemeten en het framework kan alles wat deze bron vraagt. De vorige versie van dit rapport
concludeerde "JA-MITS" met drie blokkades. **Alle drie zijn weg** — twee omdat ze op een meetfout
berustten, één omdat het framework inmiddels is uitgebreid:

| Was een blokkade (28-08-2026) | Stand op 04-09-2026 |
|---|---|
| v2 weigert de inloggegevens (`invalid_client`) | **Opgelost.** Niet de credentials waren fout maar de grant: v2 gebruikt `grant_type=api_key`, niet `client_credentials`. Met de juiste grant en host: HTTP 200 |
| Het framework kan geen REST-`POST` met JSON-filterbody sturen | **Opgelost.** `StrategyDetails.Method="POST"` + `Body` doet precies dit; zie [Benodigde uitbreidingen](#benodigde-uitbreidingen-aan-general-notebooks) |
| OAuth2-`Scope` is niet configureerbaar | **Opgelost.** De kolom `auth_scope` bestaat en de generator emitteert `AuthDetails.OAuth2.Scope` |

Wat er overblijft is werk, geen blokkade: de configuratie moet worden gebouwd, en `03_schema.py`
en `04_transforms.py` moeten mee (PascalCase → camelCase). Beide horen bij config-builder.

**De grootste winst van de migratie is niet het kortingsveld** maar de doorlooptijd: v1 dwingt een
afkoeltijd van 120 seconden per endpoint af, v2 vertoonde in circa veertig aanroepen op één dag
geen enkele beperking. Zie [Rate limits](#rate-limits).

## Wat deze ronde corrigeert

Vier bevindingen spreken de versie van 28-08-2026 tegen. Ze staan hier bij elkaar omdat elk van de
vier een dag werk kan kosten aan wie ze opnieuw moet ontdekken.

| # | Stond er | Klopt niet, want |
|---|---|---|
| 1 | v2 weigert onze inloggegevens (`invalid_client`) | Er werd `client_credentials` gestuurd. v2 wil `grant_type=api_key` met een aparte API-sleutel en de **letterlijke** client-id `apikeygrant`. Daarmee: HTTP 200 |
| 2 | v2 leeft op `apiv2.ticketcounter.eu` | Het is één contract op **twee hostfamilies**, en een sleutel werkt maar op één ervan. Zie [Twee hostfamilies](#twee-hostfamilies--net-en-eu-dragen-hetzelfde-contract) |
| 3 | `sold-tickets` heeft 72 velden | Het **contract** telt er 72; een **respons** levert er minder omdat de bron elk veld met de waarde `null` weglaat. Dat is geen hostverschil en geen contractverschil — de twee swaggers zijn byte-voor-byte identiek op de `tokenUrl` na |
| 4 | `GET /api/v2/DiscountReasons` bestaat | Dat pad staat niet meer in het contract. Het heet nu `GET /api/v2/Discount/reasons` — en geeft HTTP 403 |

**En de valstrik die de meeste tijd kost, want hij faalt stil.** Er bestaan twee token-endpoints
die allebei HTTP 200 geven op exact dezelfde `api_key`-aanvraag:

```
POST https://apiv2.ticketcounter.net/connect/token  -> 200, JWT met 3 segmenten    werkt op v2
POST https://api.ticketcounter.net/token            -> 200, ondoorzichtig token
                                                            van 1 segment          401 op elk v2-endpoint
POST https://apiv2.ticketcounter.net/token          -> 404 (dit pad bestaat niet)
```

Het tweede token is het formaat van de **oude** API. Elk v2-endpoint antwoordt er `401` op, **met
een lege foutbody** — geen `WWW-Authenticate`, geen JSON, geen aanwijzing. Wie de host overneemt
uit de v1-configuratie en alleen het pad aanpast, krijgt dus een geslaagde tokenaanvraag en daarna
een onverklaarbare 401. Alleen `/connect/token` op de `apiv2`-host levert een bruikbaar token.

## Twee kopieën van dit rapport

| Waar | Stand |
|---|---|
| Clientrepo (`client-outputs/{source}_research.md`) | Aanwezig. Draagt een **extra bijlage** met de omgevingsnamen en de secretnamen van die klant |
| Platformrepo (`fabric-framework/source-research/`) | Aanwezig. Dit document, klantneutraal |
| Catalogusrij `source_research` | Aanwezig |

De twee kopieën spreken elkaar niet tegen: de clientkopie is deze tekst **plus** een bijlage die de
platformkopie niet mag dragen. Waar deze ronde een eerdere bevinding tegenspreekt, staat dat in
[Wat deze ronde corrigeert](#wat-deze-ronde-corrigeert) met de datum erbij. Bevindingen die deze
ronde niet opnieuw konden worden gecontroleerd, blijven staan en zijn gemarkeerd als
**ongeverifieerd**.

## TypeSource

- **Bevestigd:** `api` (REST/JSON over HTTPS), voor beide generaties.
- **Door intake afgeleid:** `api` — hetzelfde, geen correctie nodig.

## Overzicht

### v1 — de generatie waarop vandaag wordt geproduceerd

- **Host:** `https://api.ticketcounter.net`
- **Vorm:** `GET` met query-string-parameters; respons JSON met PascalCase-velden.
- **Documentatie: geen.** `/swagger/v1/swagger.json`, `/swagger/index.html` en `/help` geven alle
  drie HTTP 404; de hostwortel redirect naar de marketingsite. Geen publiek contract, geen
  changelog, geen statuspagina.
- **Bewijsbasis:** live gemeten op 2026-08-28 — alle vijf endpoints aangeroepen.

### v2 — de doelgeneratie

- **Titel:** `TC.Tickets.API`, versie `v2` (OpenAPI 3.0.4).
- **De spec is openbaar, geen login vereist**, op elke host onder `/swagger/v2/swagger.json`.
- **Omvang (opgehaald 04-09-2026):** 148 paden, 353 schemadefinities, 31 taggroepen. Alleen de vijf
  `Statistics`-endpoints vallen binnen de scope.
- **Bewijsbasis: live gemeten op 04-09-2026.** Alle vijf entiteiten aangeroepen, paginering en
  omhulsel waargenomen, de vorm van elke respons vastgelegd. Waar dit rapport zich op het
  gepubliceerde contract baseert in plaats van op een respons, staat dat er expliciet bij.
- **Grootste structurele wijziging ten opzichte van v1:** de Statistics-endpoints zijn **POST met
  een JSON-body**, waar v1 GET met query-string-parameters gebruikt.

> **Pas op met het woord "v1" bij deze leverancier.** De Swagger-UI op de v2-host publiceert twee
> specs naast elkaar: `TC.Tickets.API V1` (`/swagger/v1/swagger.json`) en `TC.Tickets.API V2`. Die
> "V1" is **niet** de legacy Statistics-API. Hij telt 14 paden — `Basket/{basketKey}/changetimeslot`,
> `Heartbeat`, `OfflineModule/*`, `Partner/depots`, `Reservation/*`, `ShopTranslation` — en **geen
> enkel** `Statistics`-pad. De legacy Statistics-API op `api.ticketcounter.net` is een aparte,
> ongedocumenteerde dienst. Dat onderscheid bepaalt hoe je een uitfaseringsmededeling moet lezen:
> "v1 gaat uit" kan over twee verschillende dingen gaan.

## Twee hostfamilies — `.net` en `.eu` dragen hetzelfde contract

**Gemeten op 04-09-2026, drie hosts, `/swagger/v2/swagger.json`, alle drie HTTP 200:**

| Host | Bytes | Verschil met `.net` |
|---|---|---|
| `apiv2.ticketcounter.net` | 759 920 | — (referentie) |
| `apiv2.ticketcounter.eu` | 759 918 | **Alleen de twee `tokenUrl`-waarden** in het `securitySchemes`-blok |
| `apiv2test.ticketcounter.eu` | 760 032 | De `tokenUrl`, plus één extra veld `scanDefinitionName` op `TC.Common.Models.SubscriptionManagement.ProductDto` — buiten de Statistics-schema's |

Genormaliseerd vergeleken (JSON geparseerd, sleutels gesorteerd) is het verschil tussen `.net` en
`.eu` **exact twee regels**, allebei de `tokenUrl`. **Het zijn dus niet twee contracten.** Wie op
de `.eu`-swagger onderzoekt en op `.net` produceert, leest hetzelfde document. Dat sluit een
hostverschil uit als verklaring voor een kortere veldenlijst in een respons; de verklaring staat in
[De bron laat lege velden wég](#de-bron-laat-lege-velden-wég--lees-elke-veldenlijst-als-ondergrens).

Wat wél per hostfamilie verschilt is **welke sleutel er wordt geaccepteerd**. Een sleutel die op
`apiv2.ticketcounter.net/connect/token` een token oplevert, geeft op de `.eu`-hosts:

```
POST https://apiv2.ticketcounter.eu/connect/token      -> HTTP 400 {"error":"invalid_grant",
                                                                    "error_description":"API key is invalid"}
POST https://apiv2test.ticketcounter.eu/connect/token   -> HTTP 400, idem
```

`invalid_grant` — *"API key is invalid"* — en niet `invalid_client`: het endpoint bestaat en de
grant wordt herkend, de **sleutel** hoort er alleen niet thuis. De hostfamilie is dus een
eigenschap van de klant, niet van de API. **Stel hem vast vóór je iets anders meet**, want elke
meting op de verkeerde host mislukt om een reden die niets met je vraag te maken heeft.

## Authenticatie

### v2 (doel) — patroon C2, OAuth2 met grant `api_key`

- **Patroon:** C2 uit `01_source_config.template.md` — OAuth2 `api_key`-grant (`ApiKeyGrantAuth`).
- **AuthScheme / Method:** `bearer` / `oauth2`, `GrantType: api_key`
- **Token-endpoint:** `https://apiv2.ticketcounter.{net|eu}/connect/token` — **het pad `/connect/`
  is verplicht**, zie de valstrik hierboven.
- **Scope:** `TC.Tickets.API`
- **Form-body van de tokenaanvraag:** `client_id=apikeygrant`, `api_key=<sleutel>`,
  `grant_type=api_key`, `scope=TC.Tickets.API`
- **Secretnaam in de Key Vault** (alleen namen; waarden worden nooit gelezen):
  `ticketcounter-{environment}-v2-api-key` — **één** secret per omgeving.
- **`apikeygrant` is géén secret.** Het is een letterlijke constante die de leverancier publiceert,
  gelijk voor elke klant. Hij hoort in de configuratie (`AuthDetails.OAuth2.ClientId`), niet in de
  kluis: een constante in de Key Vault wordt per klant als ontbrekend secret gemeld, zonder enig
  voordeel.
- **Het token:** JWT met drie segmenten, geldig 3600 s (gemeten 04-09-2026). De notebook cachet hem
  tot 60 s vóór het verlopen.
- **De `client-id` / `client-secret` / `refresh-token`-secrets van v1 vervallen** op v2. Ze geven
  `invalid_client`, en dat is terecht: v2 kent dit patroon niet voor deze bron.

### v1 (in productie, werkt) — patroon C, grant `refresh_token`

- **Token-endpoint:** `https://api.ticketcounter.net/token`, grant `refresh_token`, geen scope
- **Secretnamen:** `ticketcounter-{environment}-client-id`, `-client-secret`, `-refresh-token`
- **Gemeten 2026-08-28:** tokenaanvraag geslaagd, toegang tot alle vijf endpoints.

### Gemeten tokencombinaties

| Endpoint | Grant | Uitkomst |
|---|---|---|
| `apiv2.ticketcounter.net/connect/token` | `api_key` + `apikeygrant` + scope | **HTTP 200, JWT (3 segmenten)** — werkt op alle v2-endpoints |
| `apiv2.ticketcounter.net/token` | — | **HTTP 404** — dit pad bestaat niet |
| `api.ticketcounter.net/token` | `api_key` (zelfde sleutel) | **HTTP 200, token van 1 segment** — geeft `401` met lege body op elk v2-endpoint |
| `apiv2.ticketcounter.eu/connect/token` | `api_key` | HTTP 400 `invalid_grant` — *"API key is invalid"* |
| `apiv2test.ticketcounter.eu/connect/token` | `api_key` | HTTP 400, idem |
| `apiv2.ticketcounter.*/connect/token` | `client_credentials` met de v1-secrets | HTTP 400 `invalid_client` (gemeten 28-08-2026) |
| `api.ticketcounter.net/token` | `refresh_token` (v1, controle) | HTTP 200 — v1 blijft werken |

**Meerdere omgevingen.** De bron levert per omgeving een eigen sleutel; de omgevingsnaam wordt via
`{environment}` in de secretnaam ingevuld. Beide omgevingen zijn op 04-09-2026 afzonderlijk
getest: **beide leveren een token en beide geven rijen terug** op de Statistics-endpoints. Ze delen
dezelfde host en hetzelfde token-endpoint; alleen de sleutel verschilt.

- **De discovery** (`/.well-known/openid-configuration`, publiek) noemt als grants:
  `authorization_code`, `client_credentials`, `refresh_token`, `implicit`, `password`,
  `urn:ietf:params:oauth:grant-type:device_code`, `stc_delegation`, `tcproxy_delegation` en
  **`api_key`**. Ondersteunde scopes: `TC.Tickets.API` en `offline_access`.
- **Security geldt globaal:** de spec declareert op topniveau `security: [{oauth2: [], bearer: []}]`
  zonder override per operatie, dus hetzelfde bearer-token geldt voor alle endpoints.

## Toegang per rol — buiten Statistics is het 403

Een sleutel die alle vijf `Statistics`-endpoints mag lezen, mag daarmee **niet** alles. Gemeten op
04-09-2026, opnieuw bevestigd:

| Endpoint | Uitkomst |
|---|---|
| `GET /api/v2/Discount/reasons` | **HTTP 403** |
| `POST /api/v2/Discount/codes-basic-info` | **HTTP 403** |
| `GET /api/v2/Discount/{discountCode}` | **HTTP 403** |

Foutvorm — nuttig, want het is de enige plek waar de foutvelden van het omhulsel zichtbaar worden:

```json
{"succeeded": false,
 "errorMessage": "You do not have the required permissions to access the requested resource.",
 "isRedirect": false, "redirectUrl": null, "displayError": true, "errorCode": ""}
```

**Dit is een vastgesteld feit, geen openstaande actie.** Of er rechten worden aangevraagd is een
klantbesluit; voor het onderzoek zelf betekent het dat de kortingsdimensie (de tabel achter
`discountCode`) niet via deze API bereikbaar is en dat `discountName` de enige beschrijvende
kortingsinformatie in de feiten is. Toegang verschilt bij deze leverancier per rol — reken er niet
op dat een sleutel die Statistics leest, ook referentiedata leest.

## Verbinding

- **BaseUrl:**
  - v1 (in gebruik): `https://api.ticketcounter.net`
  - v2: `https://apiv2.ticketcounter.net` **of** `https://apiv2.ticketcounter.eu` — per klant één
    van beide, zie [Twee hostfamilies](#twee-hostfamilies--net-en-eu-dragen-hetzelfde-contract)
  - v2 test: `https://apiv2test.ticketcounter.eu`
  - De v2-spec declareert geen `servers`-blok; de base-URL's komen uit de token-host.
- **RateLimitDelay:**
  - v1: `125` (seconden) — **noodzakelijk**, de bron dwingt 120 s per endpoint af.
  - v2: `0.5` seconden als voorzichtige startwaarde. Er is geen limiet gedocumenteerd en er is er
    ook geen waargenomen; 0,5 is beleid, geen meting.
- **ApiHeaders:** `Content-Type: application/json` is voor v2 **verplicht** — elke Statistics-call
  draagt een JSON-body. Geaccepteerde request-mediatypes per endpoint: `application/json`,
  `application/json-patch+json`, `text/json`, `application/*+json`. De succesrespons is in de spec
  gedeclareerd als `text/plain`, `application/json` én `text/json` met hetzelfde schema; in de
  praktijk parseerde elke gemeten respons als JSON, dus de `text/plain`-declaratie is een
  documentatie-eigenaardigheid en geen probleem.
- **Stabiliteit v1 (waarneming 28-08-2026):** één van zeven live aanroepen brak af met een
  afgebroken TLS-verbinding en slaagde bij herhaling. Eenmalig, dus geen patroon — maar het
  bevestigt dat de retry-logica van de generieke client hier nut heeft.

## Rate limits

### v1 — gemeten, en strenger dan verwacht

Twee aanroepen op **hetzelfde** endpoint binnen 120 seconden geven:

```
HTTP 409
"You may only perform this action every 120 seconds."
```

Een aanroep op een **ander** endpoint direct na die 409 geeft HTTP 200. De afkoeltijd geldt dus
**per endpoint**, niet per token en niet per client. Dat is nergens gedocumenteerd en verklaart de
`rate_limit_delay` van 125 in de bestaande configuratie: seconden, met marge. Praktisch gevolg: een
volledige herlading kost minimaal `aantal_chunks × aantal_pagina's × 120 s` per entiteit. Vijf
entiteiten kunnen wel parallel, want ze delen de afkoeltijd niet.

### v2 — niets gedocumenteerd, en niets waargenomen

- De spec bevat geen tekst over rate limits, throttling of quota. Op geen enkel Statistics-endpoint
  is een `429` gedeclareerd; `429 Too Many Requests` komt in de hele spec één keer voor, op
  `POST /api/v2/WaitingRoom/claim`.
- **Gemeten 04-09-2026:** acht aanroepen direct achter elkaar op hetzelfde endpoint, plus in totaal
  circa veertig aanroepen binnen een half uur, elk met een eigen tokenaanvraag, verdeeld over alle
  vijf endpoints en beide omgevingen. **Geen enkele 409 en geen enkele 429.** Ook geen vertraagde
  respons of andere aanwijzing van throttling.
- De enige harde grens is een **body-limiet**, geen rate limit: `limit` maximaal 100 000 rijen per
  call, standaard 1000.
- Dat staat scherp tegenover v1. Als deze waarneming standhoudt, is dít de grootste winst van de
  migratie — een herlading die op v1 uren duurt, wordt op v2 begrensd door bandbreedte in plaats
  van door afkoeltijd.
- **Voorbehoud:** "niet waargenomen" is geen "bestaat niet". Verlaag `rate_limit_delay` stapsgewijs
  en meet; de generieke client herhaalt een `429` al met `Retry-After` en een `409` met lineaire
  backoff, dus een ongedocumenteerde limiet leidt tot vertraging in plaats van uitval.

## Entiteitenoverzicht

| Entiteit | Endpointpad (v2) | Binnen scope | Bovenliggende entiteit | Toelichting |
|---|---|---|---|---|
| `baskets` | `POST /api/v2/Statistics/baskets` | Ja | — | Geneste arrays en één genest object; zie Response Shape |
| `sold_tickets` | `POST /api/v2/Statistics/sold-tickets` | Ja | — | Breedste entiteit (contract: 72 velden) |
| `sold_subscriptions` | `POST /api/v2/Statistics/sold-subscriptions` | Ja | — | Contract: 47 velden |
| `ticket_scans` | `POST /api/v2/Statistics/scans` | Ja | — | Contract: 47 velden. **Geen `modified*`-filter** |
| `cancellations` | `POST /api/v2/Statistics/cancellations` | Ja | — | Contract: 12 velden |
| *Alle overige tags* | `Reservations`, `Pos`, `Contacts`, `Payments`, `Webhooks`, … (nog 26) | Nee | — | Buiten scope; inventaris in [Verzamel-endpoints](#verzamel-endpoints-v2--dimensie--en-referentiebronnen) |

De vijf entiteiten binnen scope komen **1-op-1** overeen met de vijf die al op v1 draaien. De
entiteitsnamen in de configuratie moeten ongewijzigd blijven; alleen `url_path` en
`output_record_key` veranderen.

**De v1-paden en hun recordsleutels, ter vergelijking** (gemeten 28-08-2026):

| Entiteit | `url_path` (v1) | Recordsleutel v1 | Recordsleutel v2 |
|---|---|---|---|
| `sold_tickets` | `api/v1/statistics/soldtickets/nl-NL` | `SoldTicketsInfo` | `soldTickets` |
| `baskets` | `api/v1/statistics/baskets` | `Baskets` | `baskets` |
| `ticket_scans` | `api/v1/statistics/ticketScans/nl-NL` | `TicketScanInfo` | `scans` |
| `sold_subscriptions` | `api/v1/statistics/soldsubscriptions/nl-NL` | `SoldSubscriptionsInfo` | `soldSubscriptions` |
| `cancellations` | `api/v1/statistics/cancellations/nl-NL` | `Cancellations` | `cancellations` |

De v1-recordsleutel volgt geen patroon: twee met achtervoegsel `Info`, één in het enkelvoud
daarvan, twee kale meervouden. In v2 zijn het alle vijf camelCase-meervouden. Wie ze uit de oude
configuratie overneemt, zit er op alle vijf naast — en dat faalt stil, met "0 rijen" in plaats van
een fout.

## Contract van de request body

Alle vijf endpoints nemen hun filter- en pagineringsobject in de **request body**, niet in de
query-string.

### Gedeelde pagineringsvelden

| Body-veld | Betekenis |
|---|---|
| `offset` | Aantal over te slaan rijen |
| `limit` | Maximaal aantal terug te geven rijen. **Max 100 000**, standaard 1000 |

### Filtervelden per entiteit — geverifieerd op het contract, 04-09-2026

| Body-veld | baskets | sold-tickets | sold-subscriptions | cancellations | scans |
|---|---|---|---|---|---|
| `fromDate` / `toDate` | ja | ja | ja | ja | ja |
| `modifiedFrom` / `modifiedTo` | ja | ja | ja | ja | **nee** |
| `dateRangeType` | ja | ja | ja | ja | **nee** |
| `excludeContactInfo` | ja | ja | ja | **nee** | ja |
| `eventKey` | — | ja | — | ja | — |
| `languageCode` | — | ja | — | — | ja |
| Overig | — | — | — | `includeTicketCodeValues` | `ticketScansOnly`, `subscriptionScansOnly` |

**Bevestigd: `scans` kent geen `modifiedFrom`/`modifiedTo` en geen `dateRangeType`.** Dat was een
openstaand punt uit de vorige versie en is nu op het contract nagelopen: het schema
`GetScansMessage` draagt uitsluitend `fromDate`, `toDate`, `excludeContactInfo`, `ticketScansOnly`,
`subscriptionScansOnly`, `offset`, `limit` en `languageCode`. `ScanInfo` bevat bovendien geen
`creationDate` of `modificationDate` — er is dus aan geen van beide kanten een wijzigingsveld.

**Ook bevestigd: `cancellations` kent geen `excludeContactInfo`.** Dat is geen omissie maar
consistentie: `CancellationsInfo` bevat geen enkel persoonsgegeven, dus er is niets te
onderdrukken.

### `StatisticsFilterDateRangeType`

Integer-enum die bepaalt op welke datum `fromDate`/`toDate` filteren:

| Waarde | Naam | Betekenis |
|---|---|---|
| `0` | `ConfirmationDate` | Bevestigingsdatum van de reservering (**standaard**) |
| `1` | `CreationDate` | Aanmaakdatum van de reservering |
| `2` | `VisitDate` | Bezoekdatum van de reservering |

> **Dit is een valkuil bij de migratie.** Op welke datum `fromDate`/`toDate` in **v1** filteren is
> niet gedocumenteerd en niet vastgesteld. Is dat niet de bevestigingsdatum, dan levert hetzelfde
> venster op v2 een andere rijenset op zonder dat er iets faalt. Zie
> [Openstaande vragen](#openstaande-vragen--unknowns).

## Paginering en ingestie per entiteit

Dit is sectie 2 van de configuratie. Alle waarden hieronder zijn gemeten op 04-09-2026, tenzij
anders vermeld.

### Wat voor alle vijf geldt

**Paginering: numerieke offset in de body.** `offset` en `limit` gaan mee in het JSON-document; het
omhulsel geeft `offset` en `resultCount` terug.

**`resultCount` telt de rijen op déze pagina, niet het totaal.** Gemeten op alle vijf entiteiten:

| Aanroep | Rijen terug | `resultCount` | `offset` in de respons |
|---|---|---|---|
| `limit=2`, `offset=0` | 2 | 2 | 2 |
| `limit=2`, `offset=2` | 2 | 2 | 4 |
| `limit=2` op een venster met één treffer | 1 | 1 | 1 |
| `limit=2000`, volledig gevulde pagina | 2000 | 2000 | 2000 |
| `limit=2000`, laatste (deel)pagina | minder dan `limit` | gelijk aan de rijen | gelijk aan de rijen |

Twee dingen volgen daaruit, en ze zijn allebei configuratierelevant:

1. **De stopconditie is `resultCount < limit`** — precies wat `OffsetPaginationExtractor` verwacht.
   Zou `resultCount` het totaal zijn geweest, dan zou die lus nooit op tijd stoppen. Dit was in de
   vorige versie een `UNKNOWN` met een expliciet risico; het is nu gemeten.
2. **`offset` in de respons is de *volgende* offset**, niet de opgevraagde: het is
   `verzonden offset + rijen op deze pagina`. Handig als cursor, maar het framework heeft hem niet
   nodig — dat telt zelf op met `PageSize`, wat op hetzelfde neerkomt zolang een volle pagina
   precies `limit` rijen draagt (gemeten: dat klopt).

**Zonder datumfilter komt er niets terug.** Een body met alleen `limit` geeft HTTP 200,
`succeeded: true` en een **lege array** — op elke entiteit en in beide omgevingen getest. De bron
levert dus géén "alles" bij een ontbrekend venster; hij levert niets. Dat is de gevaarlijkste
uitkomst die er is, want een run die zijn startdatum kwijt is, meldt succes en laadt nul rijen.
`WatermarkDetails.DefaultStart` is daarom niet optioneel, en de bestaande guard in
`_build_date_params()` (die weigert bij een lege startdatum) is hier precies op zijn plaats.

**Strategie: `chunk_offset` voor alle vijf**, gelijk aan wat v1 al gebruikt — datumchunks met
offset-paginering binnen elke chunk. `offset` alleen zou alleen werken als de volledige historie in
één venster past. Beide strategienamen komen uit de allow-list van template `02a`.

**Transport: `Method: "POST"` met een `Body`-blok**, `ParamsIn: "body"` (de standaard), zodat de
paginering, de `ExtraParams` en het datumvenster in het JSON-document landen in plaats van in de
query-string.

### baskets / sold_tickets / sold_subscriptions / cancellations

- **Strategy:** `chunk_offset`
- **WatermarkType:** `date`
- **UrlPath:** `api/v2/Statistics/{baskets|sold-tickets|sold-subscriptions|cancellations}` — let op
  de hoofdletter in `Statistics` en op het koppelteken in `sold-tickets` / `sold-subscriptions`
- **ExtraParams:** `{"excludeContactInfo": true}` waar de klant geen contactgegevens wil laden
  (niet beschikbaar op `cancellations`); op `cancellations` daarnaast
  `{"includeTicketCodeValues": true}` — zie de waarschuwing hieronder
- **Output.RecordKey / RecordType:** `baskets` / `soldTickets` / `soldSubscriptions` /
  `cancellations` — `keyed`
- **StrategyDetails:**
  - `Method: "POST"`, `Body: {"Template": {}, "ParamsIn": "body"}`
  - `Pagination.OffsetParam: offset`, `PageSizeParam: limit`, `PageSize: 10000`,
    `ResultCountKey: resultCount`
  - `LoopChunks.ChunkType: days`, `ChunkSize: 30`
- **WatermarkDetails:** `ParamStart: modifiedFrom`, `ParamEnd: modifiedTo`,
  `Format: "%Y-%m-%dT%H:%M:%S"`. **Gemeten: een body met alleen `modifiedFrom` en `limit` geeft
  rijen terug op alle vier**, en de teruggegeven `modificationDate`-waarden liggen op of na de
  opgegeven grens. Echte change-data capture is dus mogelijk — een verbetering ten opzichte van v1,
  dat geen enkel wijzigingsveld draagt.
- **Alternatief venster:** `fromDate`/`toDate` plus `dateRangeType`, wanneer een venster op
  bevestigings-, aanmaak- of bezoekdatum gewenst is in plaats van op wijzigingsdatum. Dat is een
  functionele keuze, geen technische.
- **Extraction.BatchSize / MaxTotalRecords:** `150000` / `None` (spiegelt v1)

> **`baskets` is asymmetrisch, en dat is belangrijk.** De entiteit accepteert
> `modifiedFrom`/`modifiedTo`, maar `BasketInfo` bevat **geen** veld `modificationDate` — niet in
> het contract en niet in een respons. Je kunt dus wel op wijziging filteren, maar de
> wijzigingstimestamp niet opslaan en geen max-kolom-watermerk uit de payload berekenen. Het
> watermerk moet uit het request-venster komen (`WatermarkDetails.Source: "parameter"`), wat
> `chunk_offset` al doet.

> **`cancellations` zonder `includeTicketCodeValues` levert ononderscheidbare rijen.** Gemeten:
> twee opeenvolgende records in dezelfde respons waren **byte-voor-byte identiek** — zelfde
> `reservationKey`, zelfde `cancelDate`, zelfde bedragen. Het zijn twee geannuleerde plaatsen van
> dezelfde reservering, en zonder `ticketCode` is er geen veld dat ze scheidt. Met
> `includeTicketCodeValues: true` verschijnt `ticketCode` en verschillen ze wél. Zet die vlag aan,
> anders is elke deduplicatie stroomafwaarts een gok. (Of de sleutel daarmee uniek **is**, telt
> config-builder uit Bronze — dit is een waarneming over de parameter, niet over de data.)

### ticket_scans

- Zelfde als hierboven, **behalve** het watermerk: `modifiedFrom`/`modifiedTo` en `dateRangeType`
  bestaan hier niet.
- **WatermarkDetails:** `ParamStart: fromDate`, `ParamEnd: toDate`,
  `Format: "%Y-%m-%dT%H:%M:%S"`. Het venster filtert op **scandatum**. Een latere wijziging aan een
  al ingelezen scan is dus niet via het watermerk te detecteren — en `ScanInfo` draagt ook geen
  `modificationDate` om het aan te zien.
- **Output.RecordKey:** `scans`
- **ExtraParams:** `{"excludeContactInfo": true}`; optioneel `ticketScansOnly` /
  `subscriptionScansOnly` om de feed te splitsen.

> **`scans` gaf in de ene omgeving niets terug en in de andere wel.** In omgeving A leverde elk
> beproefd venster — vier verschillende, verspreid over twee jaar — een **lege array** met
> `succeeded: true`. In omgeving B gaf hetzelfde endpoint op hetzelfde venster meteen een volle
> pagina. Het endpoint werkt dus; wat er ontbreekt is data (of een recht) in die ene omgeving. Dat
> is een vraag aan de leverancier, geen defect in de configuratie — maar bouw de entiteit niet op
> zonder te weten welke van de twee je voor je hebt.

## Response Shape per Entity

> **Alleen de vorm.** Veldnamen, de recordsleutel, de datumopmaak en een geredigeerd
> voorbeeldrecord. **Geen** types, vulgraden, volumes of kardinaliteit — die worden door
> config-builder uit Bronze geteld.

### Het omhulsel — identiek voor alle vijf

**Waargenomen sleutels, in deze volgorde:** `{recordKey}`, `offset`, `resultCount`, `succeeded`,
`isRedirect`, `displayError`.

Het **contract** declareert er drie meer: `errorCode`, `errorMessage`, `redirectUrl`. Die
verschijnen alleen bij een fout (zie de 403-respons onder
[Toegang per rol](#toegang-per-rol--buiten-statistics-is-het-403)). Bij een geslaagde aanroep
ontbreken ze — wat ons bij de belangrijkste vormbevinding van dit rapport brengt.

### De bron laat lege velden wég — lees elke veldenlijst als ondergrens

**In geen enkele gemeten respons kwam de waarde `null` voor.** Niet één keer, op duizenden
records. De serializer laat een veld met de waarde `null` eenvoudigweg weg. Dat heeft twee gevolgen
die allebei pijn doen als je ze niet weet:

1. **Records in dezelfde respons hebben verschillende sleutelsets.** Op `sold-tickets`: 2000
   records leverden **15 verschillende sleutelsets** op, met 38 tot 45 velden per record.
2. **Een veldenlijst uit een kleine steekproef is te kort.** Twee records gaven 43 namen; 2000
   records gaven er 51. De acht die je met twee records mist zijn onder meer `discountCode` en
   `discountName` — precies de velden waar deze migratie om begon.

**Daarom staat bij elke lijst hieronder hoeveel records er zijn gezien, en is geen enkele lijst
compleet.** De bovengrens is het contract; de werkelijke lijst komt uit Bronze, waar config-builder
hem telt in plaats van schat.

| Entiteit | Waargenomen namen (N records, `excludeContactInfo: true`) | Contract (bovengrens) |
|---|---|---|
| `sold-tickets` | 51 (2000 records) | 72 |
| `sold-subscriptions` | 24 (1425 records) | 47 |
| `baskets` | 12 top-level (1588 records) | 16 |
| `cancellations` | 10 (203 records) | 12 |
| `scans` | 29 (2000 records) | 47 |

### Datumopmaak — zoals de bron hem letterlijk teruggeeft

Dit geldt voor alle vijf entiteiten en is de belangrijkste parseerbevinding.

| Vorm | Voorbeeld | Waar |
|---|---|---|
| ISO 8601 **zonder tijdzone**, met fractie | `2026-08-01T00:00:23.3136009` | `saleDate`, `creationDate`, `modificationDate`, `cancelDate`, `confirmedDate`, `scanDate`, `basketConfirmed` |
| ISO 8601 **zonder tijdzone**, zonder fractie | `2026-08-01T09:00:00` | `validFrom`, `validTo`, `capacityDate` |
| **`dd-MM-yyyy`** | `01-08-2026` | `capacityStartDate` — een andere volgorde dan alle andere datumvelden |
| **`HH:mm`** | `10:00` | `capacityStartTime`, `capacityEndTime` |

Drie dingen om op te letten:

- **Er staat nooit een `Z` en nooit een offset achter.** In welke tijdzone deze stempels staan is
  **UNKNOWN** — de spec zegt er niets over. De request-kant accepteert een `Z` wél
  (`"2026-08-01T00:00:00Z"` werkt), maar accepteert hem net zo goed zonder.
- **Het aantal fractiecijfers wisselt per record**, van 1 tot 7. Trailing nullen worden getrimd en
  de fractie ontbreekt helemaal wanneer hij nul is. Een vast parseerformaat met `.%f` breekt
  daarop — en Python's `%f` verwerkt bovendien maximaal 6 cijfers, terwijl 7 voorkomt. Dit is de
  reden om de datumconversie in Silver expliciet te regelen in plaats van op een standaard-cast te
  vertrouwen.
- **`capacityStartDate` staat in dagen-eerst-volgorde** terwijl elk ander datumveld ISO is. Wie één
  parseerregel op alle datumvelden loslaat, leest 1 augustus als 8 januari — of stil als `null`.

### Persoonsgegevens: de schakelaar `excludeContactInfo`

Gemeten door dezelfde aanroep twee keer te doen, één keer met `true` en één keer met `false`, over
hetzelfde venster en hetzelfde aantal records. Dit is een verschilmeting tussen twee gelijke
metingen en daarmee betrouwbaarder dan de veldenlijsten hierboven — maar ook hier geldt dat een
veld dat in beide standen leeg was, in geen van beide lijsten voorkomt.

| Entiteit | Onderdrukt door `excludeContactInfo: true` |
|---|---|
| `sold-tickets` (2000 recs) | `contactHolderKey`, `email`, `firstName`, `lastName`, `name`, `postalCode`, `receiveNewsLetter` |
| `sold-subscriptions` (1425 recs) | `birthDate`, `cityName`, `countryCode`, `email`, `firstName`, `gender`, `houseNumber`, `lastName`, `lat`, `lon`, `middle`, `name`, `phoneNumber`, `postalCode`, `receiveNewsLetter`, `street`, `subscriptionHolderKey` |
| `baskets` (1588 recs) | het **hele geneste object `contact`** verdwijnt — met `contactKey`, `name`, `email`, `firstName`, `lastName`, `postalCode`, `street`, `houseNumber`, `cityName`, `countryCode`, `lat`, `lon`, `phoneNumber`, `birthDate`, `gender`, `receiveNewsLetter` |
| `scans` (2000 recs) | `cityName`, `countryCode`, `email`, `firstName`, `houseNumber`, `lastName`, `lat`, `lon`, `middle`, `name`, `phoneNumber`, `postalCode`, `receiveNewsLetter`, `street` |
| `cancellations` | **n.v.t.** — de parameter bestaat hier niet, en het record draagt geen persoonsgegevens |

> **De schakelaar dekt de klant, niet het personeel.** `posFirstName`, `posMiddleName`,
> `posLastName`, `posName` (op `baskets`) en `posContact` / `posTitle` / `posGroupTitle` (op de
> andere entiteiten) blijven in **beide** standen staan. Dat zijn namen van medewerkers achter het
> verkooppunt: nog steeds persoonsgegevens, en er is aan de API-kant geen knop om ze te
> onderdrukken. Wie ze niet wil landen, moet dat in de configuratie regelen.

Zet de schakelaar tijdens onderzoek **altijd aan**, ook wanneer de klant de gegevens straks wél wil
laden. Wat de configuratie doet is een aparte beslissing; de verkenning heeft de waarden niet
nodig.

### sold-tickets

- **Record key:** `soldTickets`
- **Envelope keys:** `soldTickets`, `offset`, `resultCount`, `succeeded`, `isRedirect`, `displayError`
- **Field names — waargenomen in 2000 records, NIET compleet** (`excludeContactInfo: true`):
  `amountExVatHigh`, `amountExVatLow`, `amountExVatMiddle`, `cancelDate`, `capacityDate`,
  `capacityEndTime`, `capacityEndTimeMinutesAfterMidnight`, `capacityNames`, `capacityStartDate`,
  `capacityStartTime`, `capacityStartTimeMinutesAfterMidnight`, `cashBooking`, `channel`,
  `confirmedDate`, `creationDate`, `discountCode`, `discountName`, `eventKey`, `eventName`,
  `externalID`, `externalReservationNumber`, `extraInfo1`, `language`, `languageCode`,
  `modificationDate`, `nrOfSeats`, `originalPrice`, `paymentMethod`, `performanceKey`,
  `performanceSectionKey`, `performerName`, `posContact`, `posGroupTitle`, `posTitle`, `price`,
  `priceKey`, `priceTypeName`, `productName`, `reservationKey`, `reservationNumber`, `saleDate`,
  `salesChannel`, `testPayment`, `ticketCode`, `totalPrice`, `type`, `validFrom`, `validTo`,
  `vatHigh`, `vatLow`, `vatMiddle`
- **Let op de hoofdletters in `externalID`** — op elke andere entiteit heet het veld `externalId`.
- **`capacityNames` is een array van strings**, geen scalar.
- **Wijzigingsveld:** `modificationDate`; `creationDate` staat er los naast.
- **Personal-data switch:** `excludeContactInfo` = aan; onderdrukt de zeven velden in de tabel
  hierboven.

```json
{
  "soldTickets": [
    {
      "reservationKey": "REDACTED", "ticketCode": "REDACTED", "priceKey": "REDACTED",
      "eventKey": "REDACTED", "performanceKey": "REDACTED", "performanceSectionKey": "REDACTED",
      "productName": "REDACTED", "eventName": "REDACTED", "performerName": "REDACTED",
      "type": "REDACTED", "channel": "REDACTED", "salesChannel": "REDACTED",
      "language": "REDACTED", "languageCode": "REDACTED", "priceTypeName": "REDACTED",
      "discountCode": "REDACTED", "discountName": "REDACTED",
      "saleDate": "2026-08-01T00:00:21.1581685",
      "confirmedDate": "2026-08-01T00:00:23.3136009",
      "creationDate": "2026-08-01T00:00:21.1581685",
      "modificationDate": "2026-08-01T00:00:23.3135978",
      "validFrom": "2026-08-01T09:00:00", "validTo": "2026-08-01T19:00:00",
      "capacityDate": "2026-08-01T00:00:00",
      "capacityStartDate": "01-08-2026",
      "capacityStartTime": "10:00", "capacityEndTime": "18:00",
      "capacityNames": ["REDACTED"],
      "totalPrice": "REDACTED", "price": "REDACTED", "originalPrice": "REDACTED",
      "nrOfSeats": "REDACTED", "posContact": "REDACTED"
    }
  ],
  "offset": "REDACTED", "resultCount": "REDACTED",
  "succeeded": true, "isRedirect": false, "displayError": false
}
```

> Waarden zijn geblankt; alleen de datum- en tijdwaarden staan er letterlijk, omdat ze de **vorm**
> aantonen die hierboven wordt beschreven. Dit is geen volledige respons en geen volledig record.

### sold-subscriptions

- **Record key:** `soldSubscriptions`
- **Envelope keys:** `soldSubscriptions`, `offset`, `resultCount`, `succeeded`, `isRedirect`, `displayError`
- **Field names — waargenomen in 1425 records, NIET compleet** (`excludeContactInfo: true`):
  `cancelDate`, `channel`, `creationDate`, `externalId`, `language`, `languageCode`,
  `modificationDate`, `nrOfSubscriptionProducts`, `originalPrice`, `posContact`, `posGroupTitle`,
  `posTitle`, `price`, `productName`, `renewal`, `reservationKey`, `reservationNumber`, `saleDate`,
  `subscriptionKey`, `subscriptionTemplateKey`, `testPayment`, `type`, `validFrom`, `validTo`
- **Wijzigingsveld:** `modificationDate`
- **Personal-data switch:** `excludeContactInfo` = aan; onderdrukt zeventien velden (zie tabel).

```json
{
  "soldSubscriptions": [
    {
      "subscriptionKey": "REDACTED", "subscriptionTemplateKey": "REDACTED",
      "reservationKey": "REDACTED", "reservationNumber": "REDACTED",
      "productName": "REDACTED", "type": "REDACTED", "channel": "REDACTED",
      "language": "REDACTED", "languageCode": "REDACTED", "externalId": "REDACTED",
      "renewal": "REDACTED", "testPayment": "REDACTED",
      "price": "REDACTED", "originalPrice": "REDACTED",
      "nrOfSubscriptionProducts": "REDACTED",
      "saleDate": "2026-01-02T21:00:01.5980614",
      "creationDate": "2025-06-26T23:28:56.4830824",
      "modificationDate": "2026-01-02T21:00:01.598056",
      "validFrom": "2026-01-05T00:00:00", "validTo": "2026-01-07T23:59:59",
      "posTitle": "REDACTED", "posGroupTitle": "REDACTED", "posContact": "REDACTED"
    }
  ],
  "offset": "REDACTED", "resultCount": "REDACTED",
  "succeeded": true, "isRedirect": false, "displayError": false
}
```

### baskets

- **Record key:** `baskets`
- **Envelope keys:** `baskets`, `offset`, `resultCount`, `succeeded`, `isRedirect`, `displayError`
- **Field names — waargenomen in 1588 records, NIET compleet** (`excludeContactInfo: true`):
  `basketConfirmed`, `basketKey`, `basketNumber`, `cancellations`, `invitationCodes`,
  `partialCancellation`, `posFirstName`, `posGroupName`, `posLastName`, `posMiddleName`, `posName`,
  `reservations`
- **Genest, en dat is het onderscheidende kenmerk van deze entiteit:**
  - `reservations[]` → `reservationKey`, `reservationNumber`, `amount`
  - `cancellations[]` → `reservationKey`, `reservationNumber`, `amount`
  - `partialCancellation[]` → `ticketcode`, `reservationNumber`, `amount`
  - `invitationCodes[]` → array van scalars
  - `contact` → één object, verdwijnt volledig met de privacyschakelaar aan
  - `payments` staat in het contract maar kwam in 1588 records niet voor (leeg = weggelaten)
- **Let op: `partialCancellation[].ticketcode` is volledig kleingeschreven**, terwijl hetzelfde
  begrip elders `ticketCode` heet. Dat is geen typefout in dit rapport maar in het contract.
- **Wijzigingsveld: GEEN.** Er is `basketConfirmed` (een zakelijke datum) en verder niets. Zie de
  asymmetrie-waarschuwing bij [Paginering en ingestie](#paginering-en-ingestie-per-entiteit).
- **Personal-data switch:** `excludeContactInfo` = aan; verwijdert het hele object `contact`, maar
  **niet** `posFirstName` / `posMiddleName` / `posLastName` / `posName`.

```json
{
  "baskets": [
    {
      "basketKey": "REDACTED", "basketNumber": "REDACTED",
      "basketConfirmed": "2026-01-01T05:48:25.3834131",
      "posFirstName": "REDACTED", "posMiddleName": "REDACTED", "posLastName": "REDACTED",
      "posName": "REDACTED", "posGroupName": "REDACTED",
      "reservations": [{"reservationKey": "REDACTED", "reservationNumber": "REDACTED", "amount": "REDACTED"}],
      "cancellations": [],
      "partialCancellation": [],
      "invitationCodes": []
    }
  ],
  "offset": "REDACTED", "resultCount": "REDACTED",
  "succeeded": true, "isRedirect": false, "displayError": false
}
```

### cancellations

- **Record key:** `cancellations`
- **Envelope keys:** `cancellations`, `offset`, `resultCount`, `succeeded`, `isRedirect`, `displayError`
- **Field names — waargenomen in 203 records, NIET compleet** (geen privacyschakelaar beschikbaar):
  `cancelDate`, `creationDate`, `modificationDate`, `nrOfSeats`, `originalPrice`, `price`,
  `reservationKey`, `reservationNumber`, `validFrom`, `validTo` — plus `ticketCode` zodra
  `includeTicketCodeValues: true` meegaat.
- **Enige entiteit met één enkele sleutelset** in de gemeten records. Dat betekent niet dat de
  lijst compleet is: `externalReservationNumber` staat in het contract en kwam niet voor.
- **Wijzigingsveld:** `modificationDate`
- **Personal-data switch:** n.v.t.

```json
{
  "cancellations": [
    {
      "reservationKey": "REDACTED", "reservationNumber": "REDACTED",
      "ticketCode": "REDACTED",
      "cancelDate": "2026-01-01T12:58:59.290912",
      "creationDate": "2025-12-31T13:23:54.5781908",
      "modificationDate": "2026-01-01T12:58:59.290912",
      "validFrom": "2026-01-02T09:30:00", "validTo": "2026-01-02T19:00:00",
      "price": "REDACTED", "originalPrice": "REDACTED", "nrOfSeats": "REDACTED"
    }
  ],
  "offset": "REDACTED", "resultCount": "REDACTED",
  "succeeded": true, "isRedirect": false, "displayError": false
}
```

### scans

- **Record key:** `scans`
- **Envelope keys:** `scans`, `offset`, `resultCount`, `succeeded`, `isRedirect`, `displayError`
- **Field names — waargenomen in 2000 records, NIET compleet** (`excludeContactInfo: true`):
  `capacityNames`, `deviceId`, `eventKey`, `eventName`, `externalId`, `externalReservationNumber`,
  `extraInfo1`, `originalPrice`, `performanceKey`, `performanceSectionKey`, `performerName`,
  `price`, `priceKey`, `priceTypeName`, `productInternalId`, `productName`, `reservationKey`,
  `reservationNumber`, `scanDate`, `scanGroupName`, `scanId`, `subscriptionKey`,
  `subscriptionProductKey`, `subscriptionTemplateKey`, `testPayment`, `ticketCode`, `type`,
  `validFrom`, `validTo`
- **Wijzigingsveld: GEEN.** `scanDate` is het enige tijdstempel, en het is een zakelijke datum. Het
  contract kent hier geen `creationDate` en geen `modificationDate`.
- **Personal-data switch:** `excludeContactInfo` = aan; onderdrukt veertien velden (zie tabel).

```json
{
  "scans": [
    {
      "scanId": "REDACTED", "ticketCode": "REDACTED", "scanGroupName": "REDACTED",
      "deviceId": "REDACTED", "type": "REDACTED",
      "reservationKey": "REDACTED", "reservationNumber": "REDACTED",
      "subscriptionKey": "REDACTED", "subscriptionProductKey": "REDACTED",
      "subscriptionTemplateKey": "REDACTED",
      "eventKey": "REDACTED", "eventName": "REDACTED", "performanceKey": "REDACTED",
      "performanceSectionKey": "REDACTED", "performerName": "REDACTED",
      "productName": "REDACTED", "productInternalId": "REDACTED", "priceKey": "REDACTED",
      "priceTypeName": "REDACTED", "capacityNames": ["REDACTED"],
      "scanDate": "2026-08-01T10:00:01.320151",
      "validFrom": "2026-07-31T00:00:00", "validTo": "2026-08-03T23:59:59",
      "price": "REDACTED", "originalPrice": "REDACTED",
      "externalId": "REDACTED", "externalReservationNumber": "REDACTED",
      "extraInfo1": "REDACTED", "testPayment": "REDACTED"
    }
  ],
  "offset": "REDACTED", "resultCount": "REDACTED",
  "succeeded": true, "isRedirect": false, "displayError": false
}
```

## Delta v1 → v2 voor de verbinding

Wat er breekt aan **transport, authenticatie en paginering** — dus binnen de scope van dit rapport.
De veld- en typedelta is verplaatst naar config-builder, die hem op de gelande data maakt; zie het
kader bovenaan.

| # | Onderwerp | v1 (gemeten 28-08-2026) | v2 (gemeten 04-09-2026) | Label |
|---|---|---|---|---|
| 1 | **Transport** | `GET` met query-string | **`POST` met JSON-body** | **BREAKING** |
| 2 | **Recordsleutel + omhulsel** | PascalCase (`SoldTicketsInfo`, `ResultCount`) | camelCase (`soldTickets`, `resultCount`), plus `errorCode` in het contract | **BREAKING** |
| 3 | **Paginering** | `offset`/`limit` als query-parameters; `ResultCount` = rijen op deze pagina | `offset`/`limit` **in de body**; `resultCount` = rijen op deze pagina (**gemeten, gelijk aan v1**); `limit` max 100 000, standaard 1000 | **BREAKING** (alleen het transport) |
| 4 | **Datumfilters** | `fromDate`/`toDate` als query-parameters, formaat `%Y-%m-%d` | `fromDate`/`toDate` in de body als `date-time`; erbij: `modifiedFrom`/`modifiedTo` en `dateRangeType` | **BREAKING** |
| 5 | **Authenticatie** | `api.ticketcounter.net/token`, grant `refresh_token`, geen scope, drie secrets | `apiv2.ticketcounter.{net\|eu}/connect/token`, grant **`api_key`**, scope `TC.Tickets.API`, **één** secret plus een letterlijke client-id | **BREAKING** |
| 6 | **Veldnamen** | PascalCase | camelCase | **BREAKING** — raakt `03_schema.py` / `04_transforms.py`, en dat is werk voor config-builder |
| 7 | **Wijzigingsveld** | bestaat niet | `modificationDate` op vier van de vijf | **Verbetering** — maakt echte CDC mogelijk |
| 8 | **Rate limits** | 120 s per endpoint, afgedwongen met HTTP 409 | Niets gedocumenteerd, niets waargenomen | **NIET-BREAKING** |

Het *model* van de ingestie verandert niet: `chunk_offset` met een datumvenster en
offset-paginering per chunk blijft staan, inclusief `PageSize`, `ChunkSize` en `BatchSize`. Wat
verandert is waar de parameters landen (body in plaats van query-string) en hoe het token wordt
gehaald.

## Uitfasering van v1

**Onbekend — de leverancier moet worden bevraagd.** Dit is wat er is gezocht en wat het opleverde:

| Waar gezocht | Uitkomst |
|---|---|
| v2-spec, alle 148 paden en 353 schemadefinities | Geen enkel `Statistics`-pad of `Statistics`-schema is `deprecated`. De `deprecated`-vlaggen die er staan, zitten op ongerelateerde velden |
| v2-spec op `sunset`, `deprecat`, `obsolete`, `legacy` | Geen sunset-datum. `legacy` gaat over kortingscode- en uitnodigingscodeversies in het product, niet over de API |
| `api.ticketcounter.net`: swagger, `/help`, hostwortel | HTTP 404, HTTP 404, redirect naar de marketingsite. Geen publiek contract en geen changelog |
| Publieke ontwikkelaarsportalen (`docs.`, `developer.`, `support.`, `helpdesk.`) | Bestaan niet; DNS lost niet op |
| Websearch op uitfaseringsbeleid en release notes | Niets van deze leverancier gevonden |

Zolang die datum ontbreekt is er **geen deadline** en dus geen dwang om te migreren. Dat maakt het
een verbeteringsbesluit in plaats van een continuïteitsbesluit. Zodra de leverancier wel een datum
noemt, kantelt dat.

## Gemengd draaien: één entiteit op v2, de rest op v1

**Nee, niet binnen één bronconfiguratie.** De reden is de tokenflow, en die is gedeeld.

Het configuratieschema legt verbinding en authenticatie vast op **bronniveau**:
`source_connection_configs` draagt `base_url`, `auth_method`, `auth_grant_type`,
`auth_token_endpoint`, `auth_scope`, de secret-templates, `key_vault_url` en `rate_limit_delay`.
`source_entity_ingestion_configs` heeft **geen enkele** auth- of base-url-kolom: alleen `url_path`,
`strategy`, de watermerkvelden, de recordsleutel en `strategy_details`. Eén entiteit op een ander
grant-type zetten kan dus niet — er is maar één plek waar dat staat.

**Nuance:** de API-client kent wel een per-entiteit override van de base-URL
(`Details.EntityBaseUrl`), maar geen kolom vult hem, en een andere host is nog geen ander token.

**Wat wel kan, met open ogen:** een **tweede bron-slug** met een eigen
`source_connection_configs`-rij die op v2 wijst, met daarin alleen de entiteit die vooruit mag. De
prijs: een tweede Bronze-landingsmap, een tweede watermerkreeks voor dezelfde entiteit, een eigen
paar `03_schema.py` / `04_transforms.py`, en de plicht om de entiteit uit de oude configuratie te
halen — anders schrijven twee configuraties naar dezelfde Silver-tabel.

Sinds alle drie de blokkades weg zijn, levert die tweedeling **geen tijdwinst** meer op. Ze is
alleen nog zinvol als je het risico van de eerste v2-productierun tot één entiteit wilt beperken.

## Migratieplan

1. **Stel de hostfamilie vast** (`.net` of `.eu`) door één tokenaanvraag te doen. Doe dit eerst;
   elke andere meting is zinloos op de verkeerde host.
2. **Laat de klant de v2-API-sleutel invoeren** via het portalformulier, per omgeving, onder de
   naam `ticketcounter-{environment}-v2-api-key`. Nooit via een agent, nooit via een chat. De
   bestaande v1-secrets blijven staan; die zijn het terugvalpad.
3. **Laat config-builder de v2-configuratie bouwen.** Wijzigt ten opzichte van vandaag: `base_url`,
   `auth_grant_type` (`api_key`), `auth_token_endpoint` (met `/connect/`), `auth_scope`,
   `auth_api_key_template`, `auth_client_id` (`apikeygrant`), de vervallen
   id/secret/refresh-templates, `url_path` per entiteit, `output_record_key` per entiteit,
   `ResultCountKey`, het nieuwe `Method`/`Body`-blok, de watermerkparameters en `rate_limit_delay`.
   Ongewijzigd: `strategy`, `PageSize`, `ChunkSize`, `batch_size`.
4. **Laat config-builder de secties 3 tot en met 5 uit Bronze bepalen** — veldtypen, hernoemingen,
   sleutel en historie. Dat gebeurt op de gelande data, niet op een API-steekproef, en dat is
   precies waarom dit rapport ze niet meer bevat.
5. **Draai in DEV en vergelijk op rijaantal en op som per dag** tegen de laatste v1-run over
   hetzelfde venster. Verschil in rijaantal wijst op `dateRangeType`; verschil in bedragen op een
   veldmapping.
6. **Verlaag `rate_limit_delay` stapsgewijs** van 125 naar iets in de orde van 0,5 en meet per stap
   of er 409 of 429 terugkomt. Ga niet in één keer.
7. **Promoveer naar PRD** volgens de normale promotiepoort, met de v1-configuratie nog intact.
8. **Faseer de v1-secrets uit** en werk het configuratiesjabloon bij dat deze bron als canoniek
   voorbeeld van het refresh-token-patroon noemt. Pas na een aantoonbaar stabiele periode op v2.

### Terugvalpad

- **Tot stap 7** verandert er niets aan de draaiende v1-connector. Stoppen kost het werk, niet de
  productie.
- **Na stap 7, bij een probleem in PRD:** zet de bronconfiguratie terug op de v1-waarden en herstel
  het vorige paar `03_schema.py` / `04_transforms.py`. Een configuratieterugrol plus twee bestanden,
  geen datamigratie.
- **Wat het terugvalpad open houdt:** de v1-secrets **niet** verwijderen tot stap 8. Zonder het
  `refresh-token`-secret is v1 onbereikbaar en is er geen weg terug.

## Benodigde uitbreidingen aan general-notebooks

**Geen.** Dat is een wijziging ten opzichte van de vorige versie, die vier hiaten opsomde. Alle
vier zijn inmiddels dicht. Nagelopen op 04-09-2026 in de broncode, niet in de documentatie:

| Was gemeld als hiaat | Stand nu |
|---|---|
| REST-`POST` met JSON-filterbody | `StrategyDetails.Method="POST"` + `Body: {Template, ParamsIn}`. `_rest_request()` merget paginering, `ExtraParams` en het datumvenster in het JSON-document (`ParamsIn: "body"`, de standaard) |
| `Method='POST'` toestaan zonder GraphQL-blok | De validator eist `GraphQL` **of** `Body`, nooit beide en nooit geen van beide — een POST zonder een van tweeën zou als GET vertrekken en een 200 op ongefilterde data opleveren, en wordt daarom geweigerd |
| Paginering en watermerk in de body binden | Dezelfde `params`-dict voedt beide bestemmingen; `Body.ParamsIn` bepaalt alleen waar hij landt. Waarden houden hun type, dus `PageSize: 10000` komt als getal in de body |
| Configureerbare OAuth2-`Scope` | Kolom `auth_scope` → `AuthDetails.OAuth2.Scope` |
| *(nieuw sinds de vorige versie)* de grant `api_key` | `ApiKeyGrantAuth` + `get_api_key_grant_token()`; `create_auth_from_config()` routeert `oauth2` → `GrantType: api_key`. Configuratiekolommen `auth_api_key_template` en `auth_client_id` |

Verder al ondersteund en dus niet te bouwen: `offset`- en `chunk_offset`-paginering
(`OffsetParam`, `PageSizeParam`, `PageSize`, `ResultCountKey` met stopconditie
`resultCount < PageSize`), datum-chunking via `LoopChunks.ChunkType: days`, markerberekening uit
chunk-vensters, en herhaalpogingen bij `401`, `409`, `429` en `5xx` inclusief respect voor
`Retry-After`.

**Eén aandachtspunt zonder user story:** `_build_date_params()` formatteert de datumgrenzen met één
`Format`-string. Voor de request-kant is dat genoeg (`%Y-%m-%dT%H:%M:%S` werkt). Voor het **lezen**
van de teruggegeven stempels geldt dat niet, want de fractie varieert van 1 tot 7 cijfers — zie
[Datumopmaak](#datumopmaak--zoals-de-bron-hem-letterlijk-teruggeeft). Dat raakt de
Silver-transformatie, niet de ingestie, en hoort dus bij config-builder.

## Openstaande vragen / UNKNOWNs

1. **Tijdzone van de teruggegeven tijdstempels — UNKNOWN.** Geen `Z`, geen offset, niets in de
   spec. Bepaalt of een `to_utc_timestamp` nodig is en met welke bronzone. Vraag aan de
   leverancier.
2. **Waarop filteren `fromDate`/`toDate` in v1? — UNKNOWN.** v2 kent `dateRangeType` met
   `ConfirmationDate` als standaard. Filtert v1 op een andere datum, dan levert hetzelfde venster
   op v2 een andere rijenset zonder dat er iets faalt. Vast te stellen door rijaantallen over
   hetzelfde venster te vergelijken, of navragen.
3. **`scans` in de ene omgeving leeg — UNKNOWN.** Vier vensters over twee jaar gaven
   `succeeded: true` met een lege array, terwijl dezelfde aanroep in de andere omgeving direct een
   volle pagina gaf. Data-, rechten- of configuratiekwestie aan de kant van de leverancier:
   onbekend.
4. **Rate limits op v2 — UNKNOWN, maar nu wel afgetast.** Niets gedocumenteerd en in circa veertig
   aanroepen niets waargenomen. "Niet waargenomen" is geen "bestaat niet".
5. **Uitfaseringsdatum van v1 — UNKNOWN.** Niet in de spec, geen publieke documentatie, geen
   changelog. Alleen de leverancier weet dit.
6. **Bevat `apiv2test` bruikbare data voor validatie? — UNKNOWN, ongeverifieerd sinds 2026-07-17.**
7. **Kortingsreferentiedata — vastgesteld ontoegankelijk, geen UNKNOWN.** Alle drie de
   `Discount`-endpoints geven HTTP 403 voor een Statistics-sleutel. Zie
   [Toegang per rol](#toegang-per-rol--buiten-statistics-is-het-403).
8. **`payments` op `baskets` — vorm ongeverifieerd.** Het staat in het contract maar kwam in 1588
   records niet voor; met `null`-weglating betekent dat "niet gevuld in deze steekproef", niet
   "bestaat niet". De geneste vorm ervan is dus niet waargenomen.
9. **Verplaatst naar config-builder, uit Bronze te tellen (04-09-2026):** vulgraden per veld,
   rijvolumes per entiteit, kardinaliteit, uniciteit van de kandidaat-sleutels, de diepte van de
   beschikbare historie, en de volledige veldenlijst per entiteit. De vorige versie van dit rapport
   voerde die als UNKNOWN op; ze zijn nu niet onbekend maar **elders belegd**.

## Vragen aan de leverancier

1. **Tijdzone.** In welke tijdzone staan de tijdstempels in de `Statistics`-responses? Ze dragen
   geen offset en geen `Z`.
2. **`dateRangeType` versus v1.** Op welke datum filteren `fromDate`/`toDate` op de
   v1-`Statistics`-endpoints? Komt dat overeen met `dateRangeType = 0 (ConfirmationDate)`, of met
   `CreationDate` of `VisitDate`?
3. **Uitfasering.** Is er een einddatum voor de `Statistics`-endpoints op `api.ticketcounter.net`?
   Let op dat dit een andere API is dan de spec die de Swagger-UI op de v2-host als "V1"
   publiceert. Waar wordt een uitfasering aangekondigd — changelog, statuspagina, mailinglijst?
4. **Rate limits op v2.** De v1-endpoints geven HTTP 409 met "You may only perform this action
   every 120 seconds." Geldt op v2 een vergelijkbare limiet? Zo ja, welke, en per wat — per
   endpoint, per client of per tenant?
5. **`scans` zonder rijen.** Eén omgeving geeft over elk beproefd venster een lege array terwijl de
   andere direct rijen levert. Is dat een rechtenkwestie, een configuratiekwestie of ontbreekt de
   data?
6. **Twee vervallen velden.** `BuyingPrice` en `CountryName` zitten wel in de v1-response en niet in
   `SoldTicketsInfo` op v2. Is daar een vervanger voor, of vervallen ze bewust?
7. **Testomgeving.** Bevat `apiv2test.ticketcounter.eu` representatieve data, zodat de migratie daar
   te valideren is voordat er op productie wordt geschakeld?

## Verzamel-endpoints v2 — dimensie- en referentiebronnen

> **Ongeverifieerd sinds 2026-07-17, met één correctie op 04-09-2026.** Dit hoofdstuk beschrijft de
> 21 v2-endpoints die een verzameling teruggeven buiten de vijf `Statistics`-feiten. Het is dit keer
> alleen nagelopen op **bestaan** — de per-veld typetabellen die de vorige versie hier droeg zijn
> verwijderd, want dat zijn sectie-3-gegevens en die komen uit Bronze. Wat blijft is de inventaris:
> welk endpoint er is, wat de recordsleutel is, en of het incrementeel kan.

- **Scope.** De vijf `Statistics`-feiten blijven de enige bevestigde ingestie-scope. Deel A is een
  lijst **voorstellen**, niet bevestigd.
- **Bewijsbasis:** het gepubliceerde OpenAPI-contract, opgehaald 04-09-2026. Er zijn hiervan **geen
  responses opgehaald** — de enige drie die live zijn geprobeerd (`Discount/*`) gaven 403.

**Correctie 04-09-2026:** `GET /api/v2/DiscountReasons` bestaat niet meer. Het pad is nu
`GET /api/v2/Discount/reasons`, en het geeft HTTP 403. De overige twintig paden uit de vorige versie
bestaan alle nog, ongewijzigd.

### Vijf eigenschappen die voor alle 21 gelden

1. **Zelfde omhulsel, maar zonder pagineringsvelden.** `succeeded`, `errorMessage`, `isRedirect`,
   `redirectUrl`, `displayError`, `errorCode` plus de record-array — **maar geen `offset` en geen
   `resultCount`**. De offset-lus van het framework heeft hier dus niets om op af te gaan.
2. **Geen offset/limit-paginering.** 19 van de 21 hebben geen `offset`/`limit`: het zijn
   single-call full loads. Alleen `Contacts/findexternal` en `Contacts/findnamebirthdate`
   accepteren ze, en zelfs die missen `offset`/`resultCount` in het omhulsel.
3. **HTTP `GET` met query-parameters, geen POST-body.** Ze raken de POST-body-vorm dus niet. Let op:
   `/api/v2/TicketBundles` host daarnaast een `POST` (aanmaken) — gebruik uitdrukkelijk de `GET`.
4. **Watermerk vrijwel afwezig.** Slechts één kandidaat draagt een echt wijzigingsveld
   (`subscriptionTemplates.lastUpdatedOn`), en **geen** van de 21 biedt een server-side
   `modified`-filter. Dus: full load, altijd.
5. **Mediatypes en responscodes.** Elk endpoint declareert `text/plain`, `application/json` en
   `text/json` voor de 200, en **alleen** een `200` — geen `429` of andere foutcode in het contract.

### Deel A — ingestiekandidaten (dimensies)

| Endpoint | Record key | Aansluiting op de feiten | Incrementeel? |
|---|---|---|---|
| `GET /api/v2/SubscriptionTemplates` | `subscriptionTemplates` | `subscriptionTemplateKey` → `sold_subscriptions` + `ticket_scans` | Alleen client-side, via `lastUpdatedOn` |
| `GET /api/v2/Events/performances` | `performances` | `eventKey` / `performanceKey` → `sold_tickets` + `ticket_scans` | Nee |
| `GET /api/v2/Products/pricetypeproducts` | `prices` | `priceKey` → `sold_tickets` + `ticket_scans` | Nee |
| `GET /api/v2/Payments/payment-types` | `paymentTypes` | Labelkoppeling op betaalmethode | Nee |
| `GET /api/v2/PredefinedReasons` | `predefinedReasons` | Referentie (annulerings-/kortingsredenen); geen directe FK | Nee |
| `GET /api/v2/Discount/reasons` | *(403 — niet waargenomen)* | Kortingsredenen | **Niet toegankelijk** |
| `GET /api/v2/TicketBundles` | `ticketBundles` | Dunne samenvatting; geen FK in de feiten | Nee |
| `GET /api/v2/Reservations/possible-statuses` | `statuses` | Statische enum-decode; geen statusveld in de feiten | Nee |
| `GET /api/v2/Capacities/sold` | `soldCapacities` | Aggregaat per `priceKey` + datum; geen lijst-modus | Nee |

De sterkste kandidaat blijft `SubscriptionTemplates`: het koppelt aan twee feiten en is de enige met
een wijzigingsstempel op recordniveau.

### Deel B — operationeel, geen ingestiebron

`GET /api/v2/Pos/permissions` (`permissions`), `GET /api/v2/Pos/pos-printers` (`printers`),
`GET /api/v2/Pos/pos-templates` (`templates`), `GET /api/v2/Pos/print-templates` (`printTemplates`),
`GET /api/v2/Pos/ticket-prolongation-pricekeys` (`priceKeys`),
`GET /api/v2/Scanners/commandscandevices` (`commandScanDevices`),
`GET /api/v2/Reservations/pos-calendar` (`reservations`),
`GET /api/v2/Webhooks/retrieve-data` (`values`).

Autorisatie, POS-hardware, lay-outsjablonen, live scannerstatus en een inkomende webhook-handler.
Geen analytische waarde; `pos-calendar` bevat bovendien persoonsgegevens.

### Deel C — persoonsgegevens, geen ingestiebron

`GET /api/v2/Contacts/find`, `/finddebtor`, `/findexternal`, `/findnamebirthdate` — record key
`contacts`. Dit zijn **zoekacties** op personen, geen exportbronnen: ze vragen om zoektermen en
geven persoonsgegevens terug. Ze horen niet in een ingestiepijplijn.
