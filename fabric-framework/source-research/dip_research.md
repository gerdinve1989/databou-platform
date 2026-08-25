# DIP API-onderzoek

Onderzoek naar **DIP.ExternalApi v1** (Digitaal Informatieplatform Podiumkunsten). Dit rapport documenteert
de vijf entiteiten die een DIP-connector ophaalt — `productions`, `performances`, `theaters`, `sales` en de
**financiële afspraken** (`contracts`) — en plaatst ze in het geheel van de API.

**Aanleiding en opbouw.** Het rapport begon bij één vraag: een financiële rapportage heeft het volledige
afspraak-object nodig, niet alleen de twee percentages, want DIP rekent de uitkomst zelf en de rapportage moet
daarop aansluiten. Dat deel is uitgewerkt op **17-07-2026**. De vier overige entiteiten stonden er toen alleen
als endpoint in; ze zijn op **25-08-2026** alsnog live gemeten. Het rapport is daarmee op zichzelf voldoende om
een volledige DIP-connector te bouwen, zonder een bestaande installatie te hoeven raadplegen.

## Inhoudsopgave

| Sectie | Omschrijving |
|---|---|
| [Kernvragen — korte antwoorden](#kernvragen--korte-antwoorden) | De zes gestelde vragen, direct beantwoord |
| [TypeSource](#typesource) | Bevestigd bronprotocol |
| [Overzicht](#overzicht) | Wat de API is en hoe dit onderzoek is uitgevoerd |
| [Authenticatie](#authenticatie) | OAuth2 client_credentials, secretnamen |
| [Verbinding](#verbinding) | BaseUrl, rate-limit-vertraging, headers |
| [Entiteitenoverzicht](#entiteitenoverzicht) | Alle 53 endpoints, binnen en buiten scope |
| [Paginering en ingestie per entiteit](#paginering-en-ingestie-per-entiteit) | Strategie en waarden per entiteit — alle vijf |
| [Rate limits](#rate-limits) | Waargenomen limieten |
| [Velden en voorbeeld-JSON per entiteit](#velden-en-voorbeeld-json-per-entiteit) | Veldcatalogus en echte samples — alle vijf |
| [Sleutels en aansluiting op bestaande entiteiten](#sleutels-en-aansluiting-op-bestaande-entiteiten) | Geverifieerde joins |
| [Ankercase — verificatie](#ankercase--verificatie) | Eén afspraak, veld voor veld |
| [Belangrijkste datakenmerken per entiteit](#belangrijkste-datakenmerken-per-entiteit) | Sleutels, watermarks, volumes |
| [Benodigde uitbreidingen aan general-notebooks](#benodigde-uitbreidingen-aan-general-notebooks) | Gevonden hiaten |
| [Persoonsgegevens](#persoonsgegevens) | Wat het object bevat en wat DIP niet kan onderdrukken |
| [Openstaande vragen / UNKNOWNs](#openstaande-vragen--unknowns) | Alles wat niet is geverifieerd |

## Kernvragen — korte antwoorden

| # | Vraag | Antwoord |
|---|---|---|
| 1 | Levert de API financiële afspraken? | **JA.** `GET /contracts` (tag `Financial Agreements`), OAuth2 bearer, **geen paginering** — één platte array van 4.217 records (9,4 MB, 4,9 s). Live opgehaald. |
| 2 | Komen auteursrechten-% en partage-% als losse velden? | **JA, allebei los.** `properties.royalties_percentage` (12.0) en `properties.partage_percentage` (80.0). Geen berekend totaal — dit zijn de ruwe invoerwaarden. |
| 3 | Komen de berekeningsvelden mee? | **Deels — en de uitkomsten NIET.** De *invoer* komt mee (`royalties_add_part_percentage` = de 12/112-keuze, `producer_warranty`, `theater_warranty`, `warranty_per_performance` = garantieberekening). Het **recette/netto/verdeling-blok zit NIET in `/contracts`**. Het bestaat wel in de API — `GET /borderellen/{id}` → `calculation` — maar dat endpoint geeft voor de geteste credentials **0 records** terug. Zie [Het berekeningsblok](#het-berekeningsblok--borderellen). |
| 4 | Draagt één afspraak een array `performances`? | **JA.** `performances[]` met `number` + `date`; 1 t/m 6 uitvoeringen per afspraak (1 uitvoering: 3.111 van 4.217). Sleutels: `production.id`, `theater.id`, `performances[].number`. |
| 5 | Sluiten die sleutels aan op wat we al ophalen? | **JA, 100% waar de bronperiode overlapt.** Theaters 100/100, uitvoeringen 132/132. Eén kanttekening: 492 afspraken (11,7%) verwijzen naar 31 producties uit 2015–2019 die de huidige `productions`-ophaalstap niet teruggeeft. |
| 6 | Ankercase (één afspraak, veld voor veld) verifieerbaar? | **JA, exact.** Contract `id` 200761: `royalties_percentage` 12.0, `partage_percentage` 80.0, `producer_warranty` 650000 (= € 6.500,00), uitvoering 11484906. Alle schermwaarden gereproduceerd. |

## TypeSource

- **Bevestigd:** `api` (REST/JSON over HTTPS)
- **Bestaande config:** `type_source = "api"` — identiek, geen correctie nodig.

## Overzicht

- **Titel:** `DIP.ExternalApi`, versie `v1`.
- **De OpenAPI-spec is openbaar — geen login vereist:** `https://external-api.dip.nl/swagger/v1/swagger.json`
  (Swagger UI: `https://external-api.dip.nl/index.html`).
- **Omvang:** 53 paden, 162 schema's, verdeeld over 10 taggroepen.
- **Bewijsbasis:** dit rapport combineert het gepubliceerde OpenAPI-contract **met live calls** tegen de
  productie-API op 17-07-2026, met bestaande DIP-credentials uit de Key Vault van de klant.
  Elk hieronder genoemd type is een **waargenomen** type, tenzij expliciet anders vermeld.
  Waar de spec en de werkelijkheid afwijken, is dat apart genoteerd.
- **Rechtenmodel:** de `Financial Agreements`-endpoints zijn in de spec beschreven als *"Only for agencies"*.
  Credentials met een agency-rol passeren die controle voor `/contracts`, maar **niet** voor
  `/theaters/fees` — dat geeft `400 {"error_description":"Not an agency"}`. De rechtencontrole is dus
  per endpoint verschillend; ga er niet vanuit dat toegang tot `/contracts` toegang tot de hele tag betekent.
- **Scope-afbakening:** alle 4.217 opgehaalde afspraken droegen dezelfde `producer.id` en `agency.id` —
  die van de gebruikte credentials. `GET /contracts` is dus **al aan de bronkant afgebakend** op de
  impresario achter de credentials; er is geen filterparameter nodig om andermans afspraken buiten te houden.

## Authenticatie

- **Patroon:** **Pattern B — OAuth2 Client Credentials** (`01_source_config.template.md`)
- **AuthScheme / Method:** `bearer` / `oauth2`, GrantType `client_credentials`
- **Token-endpoint:** `https://external-api.dip.nl/token` (POST, `application/x-www-form-urlencoded`)
- **Scope:** geen — `securitySchemes.oauth2.flows.clientCredentials.scopes` is leeg.
- **Secretnamen in KeyVault** (alleen namen; waarden zijn nooit gelezen of getoond):
  - Een client-id en een client-secret; de exacte namen staan in de clientconfig (sectie 1), niet hier.
  - **Live geverifieerd** — token van 424 tekens verkregen. Let op bij een bestaande installatie: de namen
    kunnen afwijken van de `{source}-{key}`-conventie, dus lees ze uit de config in plaats van ze af te leiden.
- **Waargenomen afwijking van de spec:** de spec declareert in de request body alleen `client_id` en
  `client_secret` — géén `grant_type`. De live call stuurde wél `grant_type=client_credentials` mee en werd
  geaccepteerd. DIP negeert het veld kennelijk. De bestaande connector werkt hiermee in productie.
- **Onbekende query-parameters worden stil genegeerd** (geen 400) — zie [Persoonsgegevens](#persoonsgegevens).

## Verbinding

- **BaseUrl:** `https://external-api.dip.nl/` — één omgeving; **geen test/acceptatie-omgeving gevonden**.
  Alle calls in dit onderzoek zijn tegen productie gedaan (uitsluitend `GET`, read-only).
- **RateLimitDelay (aanbevolen):** `0.5` — gelijk aan de bestaande config; geen aanleiding gevonden om te wijzigen.
- **ApiHeaders:** geen vaste headers vereist buiten `Authorization: Bearer {token}`.

## Entiteitenoverzicht

Alle 53 endpoints. `GET` tenzij anders vermeld. Alle `POST`/`PUT`-endpoints zijn schrijfacties en vallen
per definitie buiten scope (het platform is read-only op bronnen).

### Financial Agreements — de tag van dit ticket

| Entiteit | Endpoint | In scope | Ouder | Notities |
|---|---|---|---|---|
| `contracts` | `/contracts` | **JA** | — | Alle afspraken voor de impresario. Optioneel `?modifiedSince=`. Platte array, geen paginering. 4.217 records. |
| — | `/contracts/{productionNumber}` | Nee | — | Zelfde schema, gefilterd op één productie. Werkt (318 records voor de geteste productie). Alleen nuttig als per-productie ophalen gewenst is; `/contracts` levert alles in één call. |
| — | `/theaters/fees` | Nee | — | **400 "Not an agency"** — geen toegang met deze credentials. |
| — | `/theaters/{theaterId}/fees` | Nee | — | Werkt wél (200). Toeslagperiodes per theaterzaal. `fee_periods` was leeg voor theater 19. Buiten scope van dit ticket. |
| — | `/theater/contacts` | **Nee — bewust niet** | — | Werkt (200), maar bevat **uitsluitend** persoonsgegevens: `theaters[].contacts[].name` + `.email`. Geen enkel niet-persoonlijk veld. Zie [Persoonsgegevens](#persoonsgegevens). |
| — | `POST /contracts/{rent,partage,volume,suppletion,buyout}/create` | Nee | — | Schrijfactie. |
| — | `PUT /contracts/{contractId}/{type}/{update,revise}`, `PUT /contracts/{contractId}/propose` | Nee | — | Schrijfacties. |

### Borderellen — het berekeningsblok

| Entiteit | Endpoint | In scope | Ouder | Notities |
|---|---|---|---|---|
| — | `/borderellen` | **Nee — leeg** | — | 200 OK, maar `totalItems: 0` voor de geteste credentials. Gepagineerd (`Offset`/`Limit`/`SortColumn`/`SortDirection`). |
| — | `/borderellen/{borderelId}` | **Nee — geen data** | `/borderellen` | Bevat het `calculation`-blok (recette/netto/verdeling). Niet aanroepbaar zonder id's uit de lijst. |

### Productions & Performances

| Entiteit | Endpoint | In scope | Ouder | Notities |
|---|---|---|---|---|
| `productions` | `/producers/{producerId}/productions` | **JA** | — | `startDate`/`endDate` optioneel (`date-time`). Zónder venster geeft DIP alleen het lopende seizoen: **6 records tegen 101** over 2015–2026. Platte array, geen paginering. |
| `performances` | `/producers/{producerId}/productions/{productionNumber}/performances` | **JA** | `productions` | `loop_parent`. **Geen query-parameters** — de spec kent alleen padparameters. Platte array. |
| `theaters` | `/theaters` | **JA** | — | **819 records** (812 op 17-07-2026). **Nul parameters in de spec.** Bevat genest `theater_locations[]` — 2.862 locaties met globaal unieke id's — dát voedt de `theater_locations` Silver-stap en verklaart waarom die geen eigen ophaalstap heeft. |
| — | `/genres`, `/producers` | Nee | — | Referentielijsten. `genre` zit al genest in `productions`. |
| — | `/producers/{producerId}/theaters/{theaterId}/performances`, `/theaters/{theaterId}/performances` | Nee | — | Alternatieve ingangen op dezelfde uitvoeringen. |

### Hall Occupation

| Entiteit | Endpoint | In scope | Ouder | Notities |
|---|---|---|---|---|
| `sales` | `/productions/{productionNumber}/sales` | **JA** | `productions` | `loop_parent`. Geen query-parameters. **`id` is het theater-id, niet een verkoop-id**, en het endpoint geeft **HTTP 400** in plaats van een lege array bij een productie zonder verkoop. Zie [sales](#sales). |
| — | `/productions/{productionNumber}/theaters/{theaterId}/sales`, `/performances/{performanceId}/sales` | Nee | — | Fijnere ingangen op dezelfde verkopen. |
| — | `/productions/{productionNumber}/reservations` | Nee | — | **Reserveringen — bestaat.** Mogelijke vervolgvraag. |
| — | `/productions/{productionNumber}/blockedseats` | Nee | — | **Geblokkeerde stoelen — bestaat.** Mogelijke vervolgvraag. |
| — | `/theaters/{theaterId}` | Nee | — | Eén theater + locatie. |
| — | `/theaters/performances` | Nee | — | Uitvoeringen, theater-ingang. |

### Overige tags

| Tag | Endpoints | In scope | Notities |
|---|---|---|---|
| ` FPK` | `/fpk/data`, `/fpk/producers/{producerId}/productions` | Nee | Fonds Podiumkunsten-rapportage. |
| `Third Party` | `/thirdparty/{productions,producers,theaters}` | Nee | Derde-partij-varianten van bestaande lijsten. |
| `Countries` / `Provinces` | `/countries`, `/provinces` | Nee | Referentielijsten. `province` zit al genest in `theaters`. |
| `Ticket Sales System` | `PUT /tickets/cumulative`, `PUT /reservations/cumulative`, `PUT /blockedseats/cumulative`, `PUT /productions/.../capacity` | Nee | Schrijfacties (kaartverkoopsysteem → DIP). |
| `  Authentication` | `POST /token` | n.v.t. | Zie [Authenticatie](#authenticatie). |

### De DIP-menu-items uit de UI, afgezet tegen de API

De opdracht vroeg te noteren of de monitors bestaan. Waarneming — geen scope-voorstel:

| UI-menu-item | Endpoint in de API? | Notitie |
|---|---|---|
| financiële afspraken | **Ja** — `/contracts` | Onderwerp van dit rapport. |
| verkoopmutaties | **Waarschijnlijk** — `Hall Occupation` sales-endpoints | Deels al opgehaald als `sales`. Geen endpoint dat letterlijk "mutaties" heet. **UNKNOWN** of dit 1-op-1 dekt. |
| verkoopmonitor | **Waarschijnlijk** — zelfde sales-endpoints | Idem. **UNKNOWN.** |
| publieksmonitor | **Geen gevonden** | Geen enkel endpoint of schema met een publieks-/bezoekersstrekking. Mogelijk UI-only of niet ontsloten. **UNKNOWN.** |
| producties | **Ja** — `/producers/{id}/productions` | Al actief. |
| dashboard / beheer | n.v.t. | UI-functies. |

## Paginering en ingestie per entiteit

### contracts

- **Strategy:** `single`
- **WatermarkType:** `none` aanbevolen — zie de toelichting hieronder en
  [Benodigde uitbreidingen](#benodigde-uitbreidingen-aan-general-notebooks).
- **UrlPath:** `contracts`
- **ExtraParams:** geen
- **Output.RecordKey:** `None` — de response is een **kale JSON-array op topniveau**, geen envelope.
- **Output.RecordType:** `list`
- **StrategyDetails:** `{}` — **geen enkele pagineringsparameter**. `/contracts` kent maar één
  query-parameter: `modifiedSince`. Alle 4.217 records komen in één response.
- **Extraction.BatchSize / MaxTotalRecords:** n.v.t. / n.v.t.

**Over `modifiedSince` (waargenomen):** de parameter werkt —
`GET /contracts?modifiedSince=2026-06-01T00:00:00Z` gaf 7 records terug tegen 4.217 zonder filter.
Het is echter een **eenzijdig** filter: er is geen bijbehorende eind-parameter. Het framework kan hier in
zijn huidige vorm geen `date`-watermark op zetten (zie
[Benodigde uitbreidingen](#benodigde-uitbreidingen-aan-general-notebooks)). Dat is **geen blokkade**: een
volledige ophaal is 9,4 MB in 4,9 s en dus prima dagelijks te draaien. De keuze tussen vol en incrementeel
is aan config-builder.

### productions

- **Strategy:** `single`
- **WatermarkType:** `none` — de API kent geen last-modified-veld en geen `modifiedSince` op dit endpoint.
- **UrlPath:** `producers/{producerId}/productions`
- **ExtraParams:** `startDate` + `endDate` (beide `date-time`, beide **optioneel** volgens de spec).
- **Output.RecordKey:** `None` — kale JSON-array op topniveau.
- **Output.RecordType:** `list`
- **StrategyDetails:** `{}` — geen pagineringsparameters; de spec kent er geen.
- **Extraction.BatchSize / MaxTotalRecords:** n.v.t. / n.v.t.

> **Het venster bepaalt de volledigheid, niet de paginering.** Zónder `startDate`/`endDate` geeft DIP
> **6 producties** terug — het lopende seizoen. Met `startDate=2015-01-01&endDate=2026-12-31` zijn het er
> **101**, verdeeld over 13 seizoenen (2014-2015 t/m 2026-2027). Dit is dezelfde oorzaak als de kanttekening
> bij [`production.id`](#sleutels-en-aansluiting-op-bestaande-entiteiten): een te smal venster laat afspraken
> zonder productie achter. De keuze van het venster is aan config-builder; de meting is dat het venster het
> enige is dat het volume stuurt.

### performances

- **Strategy:** `loop_parent` — ouder is `productions`
- **WatermarkType:** `none`
- **UrlPath:** `None` (verplicht bij `loop_parent`; het pad komt uit `UrlPathTemplate`)
- **LoopParent:** `ParentEntity: "productions"`, `UrlPathTemplate:
  "producers/{producerId}/productions/{productionNumber}/performances"`, `ParentIdField: "id"`,
  `InjectField:` de kolom die het productie-id op elk kindrecord zet.
- **ExtraParams:** geen — **de spec kent op dit endpoint uitsluitend padparameters** (`producerId`,
  `productionNumber`). Er is niets te filteren en niets te pagineren.
- **Output.RecordKey:** `None` · **Output.RecordType:** `list`
- **Aantal calls:** één per productie — met een venster van 2015–2026 dus 101 calls per run.

> **`InjectField` is hier optioneel maar nuttig, niet noodzakelijk:** elk uitvoeringsrecord draagt zelf al
> `production.id`. Bij `sales` ligt dat anders — zie hieronder.

### theaters

- **Strategy:** `single`
- **WatermarkType:** `none`
- **UrlPath:** `theaters`
- **ExtraParams:** geen — **de spec declareert nul parameters op dit endpoint.** Alles of niets.
- **Output.RecordKey:** `None` · **Output.RecordType:** `list`
- **StrategyDetails:** `{}`
- **Volume:** 819 records / 276 KB in één response.

### sales

- **Strategy:** `loop_parent` — ouder is `productions`
- **WatermarkType:** `none` — er is een `updated`-veld op elk record, maar **geen enkele parameter om erop te
  filteren**. Incrementeel ophalen is op dit endpoint niet mogelijk.
- **UrlPath:** `None` · **UrlPathTemplate:** `productions/{productionNumber}/sales`
- **LoopParent:** `ParentEntity: "productions"`, `ParentIdField: "id"`, **`InjectField` is hier verplicht** —
  zie de waarschuwing hieronder.
- **ExtraParams:** geen — alleen de padparameter `productionNumber`.
- **Output.RecordKey:** `None` · **Output.RecordType:** `list`

> **`InjectField` is bij `sales` niet optioneel.** Het `id`-veld op een verkooprecord is **het theater-id**,
> niet een verkoop-id: over twee producties gaf de API 140 rijen met slechts **77 unieke `id`-waarden**, en
> `name` kwam **140 van de 140 keer** exact overeen met `theaters.name`. De korrel is (productie × theater) en
> het productie-id staat **nergens in de payload** — het bestaat alleen als de loop-parameter. Zonder
> `InjectField` is de rij niet uniek te maken en botst elke PK die op `id` alleen steunt.

> **`/productions/{n}/sales` geeft HTTP 400 bij een productie zonder verkoopgeschiedenis**, niet een lege
> array:
> ```
> HTTP 400  {"error":"Invalid response",
>            "error_description":"No sales history for production NL-{jj}-{producerId}-{nr}"}
> ```
> In een steekproef van 10 producties over 13 seizoenen overkwam dit er **1**. Bij een loop over de volledige
> historie is dit dus normaal gedrag, geen incident. **Geen blokkade:** `ParentLoopExtractor` vangt elke
> mislukte child-call af als `logger.warning` en gaat door met de volgende ouder
> (`notebook_Config_API.py:2219-2220`). Wat je ervoor terugkrijgt staat in
> [Benodigde uitbreidingen](#benodigde-uitbreidingen-aan-general-notebooks).

## Rate limits

- **Geen gedocumenteerde limiet** — de OpenAPI-spec noemt er geen.
- **Geen limiet-headers waargenomen.** Op elke response is gecontroleerd op headers met `rate`, `limit`
  of `retry` in de naam: geen enkele aanwezig. Er is dus geen signaal om op terug te vallen.
- **Geen 429 waargenomen** tijdens dit onderzoek (ca. 12 calls, waarvan meerdere zware, in enkele minuten).
- **Aanbeveling:** `RateLimitDelay: 0.5` handhaven — de bestaande waarde; draait al in productie zonder klachten.
- **Waargenomen responstijden:** `/contracts` (volledig) 4,9 s · `/contracts?modifiedSince=` 3,1 s ·
  `/contracts/{productionNumber}` 2,6 s · `/theater/contacts` **15,2 s** (traag) · `/theaters` ~2 s.

## Velden en voorbeeld-JSON per entiteit

### contracts

**Top-level velden** (alle waargenomen op 4.217 records):

| API-veld | Type | Nullable | Notities |
|---|---|---|---|
| `id` | IntegerType | Nee | **Uniek over alle 4.217 records** (geverifieerd). De technische sleutel van de afspraak. |
| `type` | StringType | Ja | Waargenomen waarden: `partage` (3.871), `buyout` (285), `volume` (58), `suppletion` (3). Stuurt de inhoud van `properties`. |
| `name` | StringType | Ja | "kenmerk eigen systeem" in de UI, bv. `"Boeking #<nr>"`. **Niet uniek** — zie de opmerking over versies hieronder. |
| `status` | StringType | Ja | Waargenomen: `approved` (2.028), `concept` (1.119), `proposed` (924), `rejected` (128), `revised-in-pki` (17), `revised` (1). |
| `reject_reason` | StringType | Ja | Vaak `""`. Gevuld bij 127 records. Vrije tekst. |
| `modified` | TimestampType | Nee | Bereik: `2015-12-29T10:25:45` t/m `2026-06-29T17:05:16.797`. Geen tijdzone-aanduiding. Voedt `modifiedSince`. |
| `contact_theater` | StringType | Ja | **PERSOONSGEGEVEN** — bevat een e-mailadres. Zie [Persoonsgegevens](#persoonsgegevens). |
| `contact_producer` | StringType | Ja | **PERSOONSGEGEVEN** — bevat een e-mailadres. |
| `agencyAsProvider` | BooleanType | Nee | `True` bij 1.736, `False` bij 2.481. |
| `agency` | StructType | Nee | `{id: int, name: string}`. Constant binnen één credentialset — het agentschap van de credentials. |
| `producer` | StructType | Nee | `{id: int, name: string, type: string}`. Constant binnen één credentialset — de producent van de credentials. |
| `theater` | StructType | Nee | `{id: int, name: string}` — de afnemer. 100 verschillende theaters. |
| `production` | StructType | Nee | `{id: string, title: string}`. `id` is de DIP-productiecode, bv. `NL-{jj}-{producerId}-{nr}`. Nooit leeg. |
| `first_date` | TimestampType | Nee | Datum van de eerste uitvoering onder de afspraak. |
| `performances` | ArrayType(Struct) | Ja | `[{number: int, date: timestamp}]`. **Nooit leeg** op 4.217 records. Lengte 1 (3.111), 2 (871), 3 (81), 4 (144), 5 (9), 6 (1). |
| `properties` | StructType | Ja | **Polymorf** — `oneOf` over 5 varianten, gestuurd door `type`. Zie hieronder. |
| `childIds` | ArrayType(Integer) | Ja | Vaak `[]`; gevuld bij 792 records. Verwijst naar andere `contracts.id`. |
| `parentId` | IntegerType | Ja | Op alle 4.217 records aanwezig. **`0` betekent "dit is de hoofdversie"**; anders de `id` van de ouder. |
| `rejection_fields` | StructType | Ja | 22 boolean-vlaggen (`is_*_rejected`), per afkeurbaar veld. Volledige lijst in de sample. |

**Over `properties` — polymorf.** De spec declareert `properties` als `oneOf` over vijf varianten. Live
bevestigd: de aanwezige sleutels verschillen per `type`. Let op de naamgeving: `type: "volume"` levert het
schema dat DIP intern **`TranchePropertiesResponse`** noemt (met `volumes[]` en `shared_costs`). De
`rent`-variant is in de spec gedeclareerd maar **kwam in de 4.217 records niet voor**.

Gedeelde velden (alle types) — DIP-schema `PropertiesResponse`:

| API-veld | Type | Notities |
|---|---|---|
| `theater_fee` | IntegerType | Theatertoeslag in kaart, **in centen**. |
| `consumption_fee` | IntegerType | Consumptietoeslag, **in centen**. |
| `service_fee` | IntegerType | Servicetoeslag, **in centen**. |
| `wardrobe_fee` | IntegerType | Garderobetoeslag, **in centen**. |
| `mantel_agreement` | BooleanType | Mantelovereenkomst. |
| `remarks` | StringType | **Vrije tekst**, gevuld bij 3.970 records. Zie [Persoonsgegevens](#persoonsgegevens). |
| `theater_technicians` | IntegerType | Ja — vaak `null`. |
| `producer_technicians` | IntegerType | Ja — vaak `null`. |
| `settlement_pricing` | ArrayType(Integer) | Afrekenprijzen **in centen**, per rang. |
| `entrance_pricing` | ArrayType(Integer) | Entreeprijzen **in centen**, per rang. |

Type-specifieke velden:

| Veld | Type | `partage` | `volume` | `buyout` | `suppletion` | `rent` | Notities |
|---|---|:-:|:-:|:-:|:-:|:-:|---|
| `royalties_percentage` | DoubleType | ✅ | ✅ | ✅ | ✅ | — | **auteursrechten-%**, bv. `12.0`. |
| `royalties_add_part_percentage` | BooleanType | ✅ | ✅ | — | ✅ | — | **AR percentageberekening.** `true` ↔ de UI toont `12/112`. Zie de duiding hieronder. |
| `partage_percentage` | DoubleType | ✅ | — | — | ✅ | — | **partage aanbieder-%**, bv. `80.0`. |
| `producer_warranty` | DoubleType (spec) / Integer (waargenomen) | ✅ | ✅ | — | — | — | **garantie aan aanbieder**, **in centen** — `650000` = € 6.500,00. |
| `theater_warranty` | DoubleType (spec) / Integer (waargenomen) | ✅ | ✅ | — | — | — | **garantie aan afnemer**, in centen. |
| `warranty_per_performance` | BooleanType | ✅ | — | — | ✅ | — | **garantieberekening.** Spec: *"If true, calculate per performance"* → `false` ↔ de UI toont "garantie op totale recette". |
| `shared_costs` | IntegerType | — | ✅ | — | — | — | In centen. |
| `volumes` | ArrayType(Struct) | — | ✅ | — | — | — | `[{amount: int (centen), percentage: double}]` — staffel. |
| `buyout_amount` | IntegerType | — | — | ✅ | — | — | Uitkoopsom, in centen. |
| `suppletion` | IntegerType | — | — | — | ✅ | — | In centen. |
| `warranty` | IntegerType | — | — | — | ✅ | — | In centen. |
| `rent` / `other_charges` | IntegerType | — | — | — | — | ✅ | **Gedeclareerd, niet waargenomen.** |

> **Centen, geen euro's — en de spec liegt over het type.** De `PartagePropertiesRequest` in de spec is
> expliciet: `producerWarranty` = *"Provider warranty (excl. VAT) **in cents**"*, type `int32`. De
> *response*-spec declareert `producer_warranty` echter als `double`. Waargenomen is een geheel getal:
> `650000`, en de UI toont € 6.500,00 — dus **centen, en de deling door 100 is aan ons**. Dit geldt voor
> alle bedragvelden hierboven. De percentagevelden zijn wél echte decimalen (`12.0`, `80.0`).

> **`royalties_add_part_percentage` — duiding, niet bewezen.** De waarde `true` correspondeert in de
> ankercase met de UI-tekst `12/112`, wat de gebruikelijke "percentage over het bedrag inclusief het
> percentage zelf"-berekening is (12/(100+12)) tegenover `12/100` bij `false`. De spec omschrijft het veld
> alleen als *"Percentage type"* en definieert de formule niet. **De formule zelf is UNKNOWN** — DIP
> bevestigt hem niet in het contract. Wij hebben één waarneming (`true` ↔ `12/112`); een tegenvoorbeeld met
> `false` is niet tegen de UI gecontroleerd.

**Voorbeeld-JSON (`contracts`) — echte response, ankercase Boeking #<nr>, persoonsgegevens geredigeerd:**

```json
{
  "id": 200761,
  "type": "partage",
  "name": "Boeking #<nr>",
  "status": "approved",
  "reject_reason": "",
  "modified": "2026-03-10T16:25:36.933",
  "contact_theater": "REDACTED",
  "contact_producer": "REDACTED",
  "agencyAsProvider": true,
  "agency": { "id": 0, "name": "REDACTED" },
  "producer": { "id": 0, "name": "REDACTED", "type": "Producent" },
  "theater": { "id": 0, "name": "REDACTED" },
  "production": { "id": "NL-{jj}-{producerId}-{nr}", "title": "REDACTED" },
  "first_date": "2026-05-10T15:00:00",
  "performances": [
    { "number": 11484906, "date": "2026-05-10T15:00:00" }
  ],
  "properties": {
    "royalties_percentage": 12.0,
    "royalties_add_part_percentage": true,
    "partage_percentage": 80.0,
    "producer_warranty": 650000,
    "theater_warranty": 0,
    "warranty_per_performance": false,
    "theater_fee": 200,
    "consumption_fee": 100,
    "service_fee": 0,
    "wardrobe_fee": 50,
    "mantel_agreement": true,
    "remarks": "REDACTED",
    "theater_technicians": null,
    "producer_technicians": null,
    "settlement_pricing": [2600],
    "entrance_pricing": [2800]
  },
  "childIds": [200762, 231775],
  "parentId": 0,
  "rejection_fields": {
    "is_start_time_rejected": false,
    "is_theater_surcharge_rejected": false,
    "is_copyright_calculation_rejected": false,
    "is_copyright_rejected": false,
    "is_provider_guarantee_rejected": false,
    "is_consumer_guarantee_rejected": false,
    "is_guarantee_calculation_rejected": false,
    "is_provider_partage_rejected": false,
    "is_ticket_price_rejected": false,
    "is_consumption_surcharge_rejected": false,
    "is_service_surcharge_rejected": false,
    "is_wardrobe_surcharge_rejected": false,
    "is_remark_rejected": false,
    "is_rent_rejected": false,
    "is_other_costs_rejected": false,
    "is_buyout_amount_rejected": false,
    "is_suppletion_amount_rejected": false,
    "is_tranche_rejected": false,
    "is_combined_budget_rejected": false,
    "is_amount_rejected": false,
    "is_maximum_amount_rejected": false,
    "is_guarantee_per_performance_rejected": false
  }
}
```

**De drie andere `properties`-varianten — echte responses, `remarks` geredigeerd:**

```json
// type: "volume"  (DIP-schema: TranchePropertiesResponse)
{
  "royalties_percentage": 10.0,
  "royalties_add_part_percentage": true,
  "shared_costs": 0,
  "producer_warranty": 0,
  "theater_warranty": 0,
  "volumes": [
    { "amount": 400000, "percentage": 100.0 },
    { "amount": 99999999, "percentage": 50.0 }
  ],
  "theater_fee": 0,
  "consumption_fee": 0,
  "service_fee": 50,
  "wardrobe_fee": 50,
  "mantel_agreement": true,
  "remarks": "REDACTED",
  "theater_technicians": null,
  "producer_technicians": null,
  "settlement_pricing": [1650, 1150, 650],
  "entrance_pricing": [1650, 1150, 650]
}
```

```json
// type: "buyout"
{
  "royalties_percentage": 11.0,
  "buyout_amount": 450000,
  "theater_fee": 0,
  "consumption_fee": 0,
  "service_fee": 0,
  "wardrobe_fee": 0,
  "mantel_agreement": false,
  "remarks": "REDACTED",
  "theater_technicians": null,
  "producer_technicians": null,
  "settlement_pricing": [1000],
  "entrance_pricing": [1000]
}
```

```json
// type: "suppletion"
{
  "royalties_percentage": 11.0,
  "royalties_add_part_percentage": true,
  "partage_percentage": 75.0,
  "suppletion": 250000,
  "warranty": 450000,
  "warranty_per_performance": true,
  "theater_fee": 425,
  "consumption_fee": 0,
  "service_fee": 0,
  "wardrobe_fee": 0,
  "mantel_agreement": true,
  "remarks": "REDACTED",
  "theater_technicians": null,
  "producer_technicians": null,
  "settlement_pricing": [1825, 1475, 1275, 1075],
  "entrance_pricing": [2250, 1900, 1700, 1500]
}
```

### Het berekeningsblok — /borderellen

Het rechterblok uit de screenshot (vrijkaarten, kaartprijs, bruto, af: theater / garantie, recette, af: btw,
af: auteursrechten, netto, verdeling, aandeel, btw, Totaal) **komt niet uit `/contracts`**. `/contracts`
levert uitsluitend de *invoerwaarden* van de afspraak.

DIP heeft die uitkomsten wél in de API, onder een andere tag: **`GET /borderellen/{borderelId}`** geeft een
`BorderelDto` met een genest `calculation`-object. Het contract van dat object dekt precies de
schermelementen:

| `calculation`-veld (spec) | Komt overeen met |
|---|---|
| `grossRevenueInVat` | bruto |
| `theaterDeductionInVat`, `theaterFeeInVat`, `consumptionFeeInVat`, `serviceFeeInVat`, `wardrobeFeeInVat` | af: theater |
| `consumerRevenueExVat`, `providerRevenueExVat` | recette |
| `grossRevenueVat`, `providerRevenueVat`, `copyrightTotalVat` | af: btw / btw |
| `copyrightExVat`, `copyrightTotalExVat` | af: auteursrechten |
| `netRevenueExVat` | netto |
| `providerTotalExVat`, `consumerTotalExVat`, `providerTotalInVat`, `combinedBudgetTotalExVat` | verdeling / aandeel / Totaal |

De `BorderelDto` herhaalt bovendien de afspraakwaarden in berekende vorm (`contractPercentage`,
`contractCopyrightPercentage`, `contractCopyrightTotal`, `contractPartagePercentage`,
`contractGuaranteeProvider`, `contractGuaranteeConsumer`) en draagt `contractId` + `performanceId` — dus op
**uitvoeringsniveau**, waar `/contracts` een array van uitvoeringen draagt.

**Maar: er is geen data.** Live resultaat:

```json
// GET /borderellen?Limit=5
{
  "data": [],
  "meta": {
    "pagination": { "page": 1, "pageSize": 5, "totalItems": 0, "totalPages": 0,
                    "hasNextPage": false, "hasPreviousPage": false }
  }
}
```

`200 OK`, geen `403` — het endpoint is dus toegankelijk voor deze credentials, maar geeft **`totalItems: 0`**.
Zonder id's uit de lijst is `/borderellen/{borderelId}` niet aan te roepen en is het `calculation`-blok
**niet gesampled**. Alle veldnamen en types hierboven komen uit het OpenAPI-contract, **niet uit een
waarneming**.

> **Waarschuwing bij deze respons — spec-afwijking.** De spec declareert voor `/borderellen` een
> `PaginatedList` met `currentPage` / `pageSize` / `items` / `totalCount`. De **echte** respons gebruikt
> `data` + `meta.pagination.{page,pageSize,totalItems,totalPages,hasNextPage,hasPreviousPage}`. Wie hier
> ooit op bouwt, moet uitgaan van de waarneming, niet van de spec.

**Waarom leeg is UNKNOWN.** Twee plausibele verklaringen, geen van beide geverifieerd:
1. Een borderel is de theaterzijdige afrekening; een producent/impresariaat heeft mogelijk
   geen borderellen in DIP.
2. Een rechtenfilter geeft stil 0 records in plaats van een 403 — vergelijkbaar met de
   `400 "Not an agency"` op `/theaters/fees`, maar dan zonder foutmelding.

**Antwoord op kernvraag 3, expliciet: NEE.** DIP levert de door hem berekende uitkomsten vandaag **niet**
via de API. Wie de recette/netto/verdeling in de rapportage wil, moet die **zelf narekenen** uit
de invoerwaarden uit `/contracts` gecombineerd met de verkoopgegevens uit `sales` — met het risico dat de
uitkomst afwijkt van wat DIP op het scherm toont — precies wat een financiële rapportage wil vermijden.

**Alternatieven, in volgorde van voorkeur — beslissing aan de gebruiker, niet aan mij:**
1. **Vraag DIP-support** waarom `/borderellen` leeg is en of het voor een producent/impresariaat gevuld
   kan worden. Dit is de enige route naar DIP's eigen cijfers en kost één e-mail
   (`support.dip.nl`). Als het antwoord "borderellen bestaan niet voor producenten" is, vervalt optie 1
   definitief en is dat een hard, documenteerbaar feit.
2. **Zelf narekenen** uit `/contracts` + `sales`. Alle invoerwaarden zijn beschikbaar en geverifieerd. Blijft
   een reconstructie: de formule achter `royalties_add_part_percentage` is niet gedocumenteerd, dus de
   uitkomst moet tegen de UI worden gevalideerd op een reeks ankercases voordat iemand hem vertrouwt.
3. **Alleen de invoerwaarden ontsluiten** en het narekenen niet doen. Levert de rapportage de percentages en
   garanties, maar niet de aansluiting op DIP's totaal — wat expliciet de wens was.

### productions

Gemeten op 101 records (venster 2015-01-01 t/m 2026-12-31). Geen enkel veld was `null`.

| Veld | Type | Waarneming |
|---|---|---|
| `id` | str | **101/101 uniek.** Formaat `NL-{jj}-{producerId}-{nr}` — hetzelfde formaat als `contracts.production.id`. Let op: `{nr}` is niet uniform (`00279` naast `3776864`), dus behandel het als een string, nooit als een getal. |
| `title` | str | 60 verschillende titels op 101 producties — een titel keert terug per seizoen. **Niet bruikbaar als sleutel.** |
| `startDate` | str (date-time) | Slechts **14 verschillende waarden op 101 records**: dit is de startdatum van het *seizoen*, niet van de productie. Geen last-modified-veld. |
| `season` | str | 13 waarden, `2014-2015` t/m `2026-2027`. |
| `genre` | object | `{id: int, name: str}`. Genest, altijd gevuld — `/genres` als losse ophaalstap is daarmee overbodig. |
| `producer` | object | `{id: int, name: str, type: str}`. Constant op alle records: de producent van de gebruikte credentials. |
| `co_producers` | array | **Leeg in 101/101.** Elementtype niet waargenomen. |
| `accompanied_by_producers` | array | **Leeg in 101/101.** Elementtype niet waargenomen. |
| `cast_members` | array | **Leeg in 101/101.** Elementtype niet waargenomen — zie [Persoonsgegevens](#persoonsgegevens). |

### performances

Gemeten op 267 records over twee producties.

| Veld | Type | Waarneming |
|---|---|---|
| `id` | int | **267/267 uniek.** |
| `number` | int | **267/267 uniek** en op elk record **gelijk aan `id`**. Dit is het veld waarop `contracts.performances[].number` aansluit. |
| `date` | str (date-time) | 267 verschillende waarden, bereik 2025-08-30 t/m 2027-06-27. Geen tijdzone-aanduiding. |
| `status` | str | 2 waarden: `agreed`, `cancellation`. |
| `type` | str | 3 waarden: `normal`, `premiere`, `tryout`. |
| `private` | bool | **`false` in 267/267.** Geen variatie waargenomen. |
| `in_festival` | bool | **`false` in 267/267.** Geen variatie waargenomen. |
| `isOtherLocation` | bool | **`false` in 267/267.** Let op de **camelCase** — het enige veld in de hele API dat afwijkt van `snake_case`. |
| `amount_rank1` | int | Gevuld op elk record, bereik 299–1.559. Capaciteit per rang. |
| `amount_rank2` … `amount_rank10` | int | **0 in 267/267 records, alle negen.** Gedeclareerd, nooit gevuld. Of ze bij een andere producent wél vullen is **UNKNOWN**. |
| `production` | object | `{id: str, title: str, genre: object}` — het productie-id staat dus al op het kindrecord. |
| `theater` | object | `{id: int, name: str}`. |
| `theater_location` | object | `{id: int, name: str}`. **Nooit `null`** in de meting. |
| `forms` | array | **Leeg in 267/267.** Elementtype niet waargenomen. |

### theaters

Gemeten op de volledige respons: 819 records.

| Veld | Type | Waarneming |
|---|---|---|
| `id` | int | **819/819 uniek.** |
| `name` | str | 819 verschillende waarden. |
| `street`, `number`, `zipcode`, `city` | str | Adres van het theater. Altijd gevuld, nooit `null`. |
| `province` | object | `{id: int, name: str}` — genest, waardoor `/provinces` als losse ophaalstap overbodig is. |
| `type` | str | 3 waarden: `Theater`, `Festival`, `Other`. |
| `dip_member` | bool | 162 van de 819 op `true`. |
| `theater_locations` | array van `{id: int, name: str}` | **2.862 locaties in totaal, alle 2.862 id's globaal uniek.** Leeg bij 18 van de 819 theaters. Dit is de voedingsbron voor een aparte `theater_locations` Silver-tabel: de locaties hebben geen eigen endpoint. |

### sales

Gemeten op 140 records over twee producties.

| Veld | Type | Waarneming |
|---|---|---|
| `id` | int | **NIET uniek — dit is het theater-id.** 77 unieke waarden op 140 rijen; zie de waarschuwing bij [sales](#sales). |
| `name` | str | **140/140 exact gelijk aan `theaters.name`** bij het bijbehorende `id`. Bevestigt dat `id` een theaterverwijzing is. |
| `updated` | str (date-time) | 135 verschillende waarden. Er is **geen parameter om hierop te filteren** — het veld is bruikbaar in Silver, niet voor incrementeel ophalen. |
| `tickets` | int | Aantal verkochte kaarten, geaggregeerd over de uitvoeringen in dit theater. |
| `recette` | int | **In centen** — `recette / tickets` geeft een mediaan van €28,41 per kaart over 139 rijen. Consistent met `contracts.producer_warranty`. |
| `performances` | array van `{number, date, tickets, recette, updated}` | 1 t/m 4 elementen per rij, 261 in totaal. **De som klopt exact:** `som(performances[].tickets) == tickets` en `som(performances[].recette) == recette` in **140 van de 140** rijen. |

> **Twee korrels, beide geldig.** De bovenliggende rij is een zuivere aggregatie van de geneste array. Wie op
> uitvoeringsniveau wil rapporteren, exploded `performances[]` en sluit via `number` aan op
> `performances.number`. Wie op theaterniveau wil rapporteren, gebruikt de bovenliggende rij zoals hij is.
> Welke van de twee de Silver-tabel wordt — of allebei — is een beslissing voor config-builder.

## Sleutels en aansluiting op bestaande entiteiten

Geverifieerd met live data uit beide endpoints — dit is meting, geen aanname:

| Sleutel in `contracts` | Sluit aan op | Resultaat |
|---|---|---|
| `production.id` (`"NL-{jj}-{producerId}-{nr}"`) | `productions.id` | **Exact gelijk formaat.** 53 van de 84 producties in afspraken matchen. Zie de kanttekening hieronder. |
| `theater.id` (`19`) | `theaters.id` | **100 van de 100** verschillende theater-id's matchen. Foutloos. |
| `performances[].number` (`11484906`) | `performances.id` **én** `performances.number` | **132 van de 132** matchen voor de geteste productie. In de `performances`-entiteit zijn `id` en `number` op elk record identiek. |
| `producer.id` | het `producerId` in de bestaande `url_path` | Constant op alle 4.217 records — de producent van de credentials. |
| `agency.id` | — | Constant binnen één credentialset. Geen bestaande entiteit. |

> **Kanttekening bij `production.id` — een echt gat.** 492 van de 4.217 afspraken (11,7%) verwijzen naar
> **31 producties uit 2015–2019** die de huidige `productions`-ophaalstap **niet teruggeeft**. Oorzaak: de
> bestaande config zet `startDate: 2020-01-01`, terwijl `contracts` teruggaat tot `modified` 2015-12-29 en
> `first_date` 2015-11-28. Die 492 afspraken zouden dus niet aansluiten op de productietabel. Dit is een
> waarneming, geen voorstel — wat ermee moet gebeuren (bronperiode verruimen, of afspraken beperken tot
> 2020+) is een keuze voor config-builder en de gebruiker.

> **Versies van dezelfde afspraak.** De ankercase levert **drie** records met `name` = `"Boeking #<nr>"`:
> `id` 200761 (`approved`, `parentId` 0, `childIds` [200762, 231775]), `id` 200762 (`concept`,
> `parentId` 200761) en `id` 231775 (`proposed`, `parentId` 200761). Alle drie dragen dezelfde
> uitvoering 11484906 en dezelfde percentages. De ouder/kind-keten via `parentId`/`childIds` draagt dus de
> **versiegeschiedenis** van één boeking. `id` is uniek; `name` is dat niet. Wat dit betekent voor filtering
> op `status` of voor de korrel is expliciet **niet mijn beslissing** — ik documenteer dat de structuur
> bestaat.

### Sleutels tussen de vier basisentiteiten onderling

Gemeten op 267 uitvoeringen, 140 verkooprijen, 101 producties en de volledige theaterlijst van 819 records.

| Sleutel | Sluit aan op | Resultaat |
|---|---|---|
| `performances.production.id` | `productions.id` | Formaat identiek (`NL-{jj}-{producerId}-{nr}`); het kindrecord draagt het ouder-id zelf. |
| `performances.theater.id` | `theaters.id` | **267 van de 267.** Foutloos. |
| `performances.theater_location.id` | `theaters.theater_locations[].id` | **267 van de 267.** Foutloos, en de 2.862 locatie-id's zijn globaal uniek — de locatie is dus zonder het theater-id te identificeren. |
| `sales.id` | `theaters.id` | **140 van de 140**, met `sales.name` == `theaters.name` als extra bevestiging. |
| `sales.performances[].number` | `performances.number` (== `performances.id`) | Zelfde nummerruimte als `contracts.performances[].number`. |
| productie-id op `sales` | `productions.id` | **Bestaat niet in de payload.** Alleen beschikbaar via `LoopParent.InjectField`. |

> **De volledige sleutelketen.** `contracts` → `productions` (via `production.id`), `contracts` →
> `theaters` (via `theater.id`), `contracts` → `performances` (via `performances[].number`). En daarnaast
> `performances` → `productions`/`theaters`/`theater_locations`, en `sales` → `theaters` + (geïnjecteerd)
> `productions`. Alle zes de gemeten joins halen 100% binnen de waargenomen periode; de enige gaten zijn de
> 492 afspraken naar producties buiten het ophaalvenster, hierboven beschreven.

## Ankercase — verificatie

`GET /contracts` → record met `id` 200761. Elk schermveld naast de API-waarde:

| Scherm (DIP-UI) | Schermwaarde | API-veld | API-waarde | ✓ |
|---|---|---|---|:-:|
| kenmerk eigen systeem | Boeking #<nr> | `name` | `"Boeking #<nr>"` | ✅ |
| type afspraak | Partage | `type` | `"partage"` | ✅ |
| aanbieder | agentschap namens producent | `agency.name` + `producer.name` + `agencyAsProvider` | beide namen letterlijk + `true` | ✅ |
| afnemer | de theaterorganisatie | `theater.name` | idem | ✅ |
| productie | de producttitel | `production.title` | idem (`production.id` = `NL-{jj}-{producerId}-{nr}`) | ✅ |
| uitvoeringen | 11484906 / 10-05-2026 15:00 (Grote zaal) | `performances[0].number` + `.date` | `11484906` + `"2026-05-10T15:00:00"` | ✅ |
| — zaal "Grote zaal" | — | **niet in `/contracts`** | via `performances.theater_location.name` (id 19) | ⚠️ |
| **auteursrechten** | **12.00%** | `properties.royalties_percentage` | `12.0` | ✅ |
| AR percentageberekening | 12/112 | `properties.royalties_add_part_percentage` | `true` | ✅ (duiding, zie boven) |
| **partage aanbieder** | **80.00%** | `properties.partage_percentage` | `80.0` | ✅ |
| garantie aan aanbieder (excl. BTW) | € 6.500,00 | `properties.producer_warranty` | `650000` (centen) | ✅ |
| garantie aan afnemer (excl. BTW) | € 0,00 | `properties.theater_warranty` | `0` | ✅ |
| garantieberekening | garantie op totale recette | `properties.warranty_per_performance` | `false` | ✅ |
| contactpersoon / e-mail afnemer | *(persoonsgegeven — niet overgenomen)* | `contact_theater` | e-mailadres, kwam overeen met het scherm — **geredigeerd** | ✅ |
| e-mail aanbieder | *(persoonsgegeven — niet overgenomen)* | `contact_producer` | e-mailadres, kwam overeen met het scherm — **geredigeerd** | ✅ |
| berekeningsblok rechts | recette / netto / verdeling / … | **NIET AANWEZIG** | zie [Het berekeningsblok](#het-berekeningsblok--borderellen) | ❌ |

**Uitkomst: de ankercase is bevestigd.** Beide gevraagde percentages en alle garantie- en
berekeningsinvoer zijn reproduceerbaar uit de API. Twee kanttekeningen:
- De **zaalnaam** ("Grote zaal") zit niet in het afspraak-object; die staat op de uitvoering
  (`performances.theater_location`), die we al ophalen.
- Het **berekende blok** is niet reproduceerbaar — zie kernvraag 3.

## Belangrijkste datakenmerken per entiteit

### contracts

- **Natuurlijke primaire sleutel:** `id` — geverifieerd uniek over alle 4.217 records.
  `name` is **niet** uniek (versies delen een naam).
- **Last-modified / update-timestamp:** `modified` — aanwezig op elk record, bereik 2015-12-29 t/m 2026-06-29.
  Geen tijdzone-aanduiding in de waarde; **UNKNOWN** of dit UTC of Europe/Amsterdam is.
- **Ondersteunt de API incrementeel ophalen?** **Ja, eenzijdig** — `?modifiedSince=` (ISO-8601). Geen
  eind-parameter. Framework-implicatie: zie [Benodigde uitbreidingen](#benodigde-uitbreidingen-aan-general-notebooks).
- **Geeft de API updates op bestaande records?** **Ja** — `modified` verschuift en `status` doorloopt een
  levenscyclus (`concept` → `proposed` → `approved` / `rejected` / `revised`). Records worden dus
  bijgewerkt, niet alleen toegevoegd.
- **Volledige periode nodig voor delete-detectie?** **Waarschijnlijk ja** — de API kent geen
  verwijder-indicatie en `modifiedSince` toont per definitie geen verdwenen records. Of DIP afspraken
  überhaupt hard verwijdert is **UNKNOWN**; `status: "rejected"` suggereert een zachte levenscyclus. Een
  volledige ophaal is goedkoop (zie hieronder) en lost dit hoe dan ook op.
- **Datavolume:** **4.217 records / 9,4 MB in één response, in 4,9 s.** Groeit met ca. 7 records per maand
  op basis van de `modifiedSince`-meting (7 records gewijzigd in de 6 weken vóór 17-07-2026 — één
  waarneming, geen betrouwbaar groeicijfer). Een dagelijkse volledige ophaal is triviaal van omvang.
- **Kandidaat-partitiekolom:** geen. 4.217 records rechtvaardigen geen partitionering. Als het ooit moet:
  `production.id` (84 waarden) of het jaar uit `first_date`.

### productions

- **Natuurlijke primaire sleutel:** `id` — 101/101 uniek. `title` is **niet** uniek (60 waarden op 101 records).
- **Last-modified / update-timestamp:** **geen.** `startDate` is een seizoensdatum, geen recordtijdstempel.
- **Ondersteunt de API incrementeel ophalen?** **Nee.** `startDate`/`endDate` filteren op de *productie*periode,
  niet op wijzigingsmoment. Een run met een vast venster haalt elke keer dezelfde set opnieuw op.
- **Geeft de API updates op bestaande records?** **UNKNOWN** — zonder tijdstempel is dat niet waarneembaar.
- **Volledige periode nodig voor delete-detectie?** **Ja** — dit is sowieso een volledige ophaal.
- **Datavolume:** **101 records / 30 KB** over 2015–2026, in één response. Groei: ca. 6–10 producties per seizoen.
- **Kandidaat-partitiekolom:** geen. `season` (13 waarden) als het ooit moet.

### performances

- **Natuurlijke primaire sleutel:** `id` — 267/267 uniek. `number` is even uniek en op elk record gelijk aan `id`;
  gebruik `number` als de join-sleutel richting `contracts`, want dát is het veld dat `contracts` noemt.
- **Last-modified / update-timestamp:** **geen.** `date` is de speeldatum.
- **Ondersteunt de API incrementeel ophalen?** **Nee** — het endpoint kent uitsluitend padparameters.
- **Geeft de API updates op bestaande records?** **Waarschijnlijk ja** — `status` kent `cancellation`, wat een
  levenscyclus impliceert. Niet direct waarneembaar zonder tijdstempel.
- **Volledige periode nodig voor delete-detectie?** **Ja.**
- **Datavolume:** steekproef van 10 producties over 13 seizoenen gaf **264 rijen / 217 KB**, gemiddeld 26 per
  productie (min 1, max 93). **Extrapolatie: ~2.700 rijen / ~2,1 MB** over 101 producties. Dit is een schatting
  uit een steekproef van 10, geen telling.
- **Kandidaat-partitiekolom:** het geïnjecteerde of geneste productie-id, als het volume ooit groeit.

### theaters

- **Natuurlijke primaire sleutel:** `id` — 819/819 uniek. Voor de geneste locaties:
  `theater_locations[].id`, 2.862/2.862 globaal uniek.
- **Last-modified / update-timestamp:** **geen.**
- **Ondersteunt de API incrementeel ophalen?** **Nee** — het endpoint declareert nul parameters.
- **Geeft de API updates op bestaande records?** **Waarschijnlijk** (adressen, lidmaatschap). Niet waarneembaar.
- **Volledige periode nodig voor delete-detectie?** **Ja** — één volledige ophaal per run, en die is goedkoop.
- **Datavolume:** **819 records / 276 KB** in één response. Gemeten op 17-07-2026 waren het er 812: **+7 in zes
  weken**, dus een langzaam groeiende referentielijst.
- **Kandidaat-partitiekolom:** geen.

### sales

- **Natuurlijke primaire sleutel:** **samengesteld — (productie-id, `id`)**, waarbij het productie-id via
  `LoopParent.InjectField` op de rij moet komen. `id` alleen is het theater-id en dus **niet** uniek: 77 unieke
  waarden op 140 rijen. Voor de geneste korrel: (productie-id, `id`, `performances[].number`).
- **Last-modified / update-timestamp:** `updated` — aanwezig op elk record én op elk genest element.
- **Ondersteunt de API incrementeel ophalen?** **Nee.** Het veld bestaat, de parameter niet.
- **Geeft de API updates op bestaande records?** **Ja, aantoonbaar** — `updated` liep in de meting door tot
  hetzelfde uur waarop de meting draaide. Verkoopcijfers worden doorlopend bijgewerkt.
- **Volledige periode nodig voor delete-detectie?** **Ja.**
- **Datavolume:** steekproef van 10 producties gaf **171 rijen / 73 KB** over 9 producties (de tiende gaf HTTP
  400), gemiddeld 19 per productie (min 1, max 59), plus 261 geneste elementen. **Extrapolatie: ~1.900 rijen /
  ~0,8 MB** over 101 producties. Schatting uit een steekproef, geen telling.
- **Kandidaat-partitiekolom:** het geïnjecteerde productie-id.

> **Kosten van de twee loops samen.** `performances` en `sales` doen elk één call per productie: bij een venster
> van 2015–2026 dus **202 calls per volledige run**, bovenop 2 calls voor `productions` en `theaters` en 1 voor
> `contracts`. Er is in de meting geen enkele 429 opgetreden — maar zie [Rate limits](#rate-limits): dat is
> geen bewijs dat er geen limiet is.

## Benodigde uitbreidingen aan general-notebooks

| Benodigde functionaliteit | Reden | Betrokken notebook | Voorbeeld/omweg | User Story ID |
|---|---|---|---|---|
| Eenzijdig date-watermark (alleen `ParamStart`, geen `ParamEnd`) | `/contracts` kent alleen `?modifiedSince=`. `_build_date_params` **werpt een `ValueError`** als `ParamEnd` ontbreekt (`notebook_Config_API.py:1336-1342`), en de validator eist bij de strategieën `page`/`offset` beide sleutels (`:2438`, `:2450`). Een `date`-watermark op `/contracts` is dus niet configureerbaar. | `notebook_Config_API.py` | **Geen blokkade.** Omweg 1: `strategy: single` zonder watermark — volledige ophaal, 9,4 MB / 4,9 s, prima dagelijks. Omweg 2: DIP negeert onbekende query-parameters stil (live geverifieerd met `excludeContactInfo=true` en `includeContacts=false` → beide 200, geen effect), dus een `ParamEnd` met een genegeerde naam zou technisch werken — een omweg die op stil gedrag van de bron leunt en dus fragiel is. | *aan te vragen — laag* |

| Onderscheid tussen "geen data" en "de bron is stuk" in een parent-loop | `ParentLoopExtractor` vangt élke child-fout af als `logger.warning` en gaat door (`notebook_Config_API.py:2219-2220`). Dat is precies goed voor `/productions/{n}/sales`, dat **HTTP 400** geeft bij een productie zonder verkoopgeschiedenis. Maar het maakt een echte storing — verlopen token, 500'en — óók een reeks warnings met een geslaagde run eromheen. Bij 101 ouders is dat het verschil tussen "1 productie zonder verkoop" en "100 producties niet opgehaald", en beide zien er in de runlog hetzelfde uit. | `notebook_Config_API.py` | **Geen blokkade voor deze bron.** Omweg: na de eerste geslaagde run het rijaantal in Bronze als ondergrens bewaken (`check_data_freshness.py`), zodat een stille halvering opvalt. Een drempel op het aandeel mislukte ouders zou het bij de bron oplossen. | *aan te vragen — midden* |

> **Geen andere hiaten gevonden.** De polymorfe `properties` (`oneOf` over 5 varianten) is geen
> framework-probleem: `03_entity_schema_config.template.md` vraagt om een expliciete `StructType`, en een
> struct met de vereniging van alle variantvelden vangt alle vier de waargenomen types (Spark vult
> afwezige sleutels met `null`). De platte top-level array (`RecordKey: None`, `RecordType: "list"`) en de
> `single`-strategie zijn beide standaard ondersteund.

## Persoonsgegevens

Het financiële-afspraak-object bevat aantoonbaar persoonsgegevens. Dit is voor dit rapport afgehandeld en
voor de ingestie een aandachtspunt.

**Wat het object bevat:**

| Veld | Wat er in staat | Waarneming |
|---|---|---|
| `contact_theater` | **Een e-mailadres**, niet een naam | Bevestigd op de ankercase. |
| `contact_producer` | **Een e-mailadres** | Bevestigd op de ankercase. |
| `properties.remarks` | **Vrije tekst**, gevuld bij 3.970 van de 4.217 records | In de ankercase zakelijke afspraken (speelduur, publiciteitsmateriaal, merchandise-afdracht). Vrije tekst kan echter alles bevatten; het rapporttemplate merkt vrije-tekstopmerkingen aan als te redigeren. |
| `reject_reason` | Vrije tekst, gevuld bij 127 records | Idem. |

De contactpersoonsnaam die de UI toont komt **niet** mee in `/contracts` — alleen het
e-mailadres. Namen + e-mail samen staan in `/theater/contacts`, dat om die reden buiten scope is gehouden.

**Is er een DIP-switch om contactinfo niet mee te sturen? NEE — geverifieerd.**
- Het OpenAPI-contract kent voor `/contracts` **precies één** query-parameter: `modifiedSince`. Er is geen
  enkele onderdrukkings-vlag gedeclareerd.
- Live getest: `?excludeContactInfo=true` en `?includeContacts=false` geven allebei `200` en
  `contact_theater` is in beide gevallen **nog steeds gevuld**. DIP negeert onbekende parameters stil.
- Een Ticketcounter-achtige `"excludeContactInfo": true` bestaat hier dus niet. **Er is niets aan de
  bronkant om op terug te vallen.**

**Wat er in dit rapport is gedaan:** in elke sample zijn `contact_theater`, `contact_producer` en
`remarks` vervangen door `"REDACTED"`. **Sleutel en type blijven staan**, zodat het schema afleidbaar
blijft. Organisatienamen (agentschap, producent, theater) zijn eveneens vervangen: het zijn geen persoonsgegevens,
maar ze maken het rapport wél klantspecifiek, en de platformkopie wordt door elke klant gelezen. Er is één record per variant opgenomen, geen pagina.

**Voor de ingestie:** omdat de bron niets kan onderdrukken, komen deze velden hoe dan ook in Bronze binnen
zodra `contracts` wordt opgehaald. Of ze naar Silver mogen, en zo ja hoe, is een keuze voor config-builder
en de gebruiker — niet voor dit rapport. Ik signaleer alleen dat de keuze onvermijdelijk is.

## Openstaande vragen / UNKNOWNs

| # | Onderwerp | Status |
|---|---|---|
| 1 | **Waarom is `/borderellen` leeg?** | **UNKNOWN — dit is de belangrijkste openstaande vraag.** Bepaalt of DIP's eigen recette/netto/verdeling ooit beschikbaar komt, of dat narekenen de enige route is. Vraagt om één e-mail aan DIP-support. |
| 2 | Het `calculation`-blok is **nooit gesampled** | Alle veldnamen/types in [Het berekeningsblok](#het-berekeningsblok--borderellen) komen uit het OpenAPI-contract, niet uit een waarneming. Als vraag 1 wordt opgelost, moet dit alsnog live worden gesampled. |
| 3 | De formule achter `royalties_add_part_percentage` | **UNKNOWN.** Spec zegt alleen *"Percentage type"*. Eén waarneming (`true` ↔ `12/112`); geen tegenvoorbeeld met `false` tegen de UI gecontroleerd. Wie hierop narekent, moet dit eerst valideren. |
| 4 | Tijdzone van `modified` en `first_date` | **UNKNOWN.** Geen offset in de waarde, niets in de spec. Relevant zodra `modifiedSince` incrementeel wordt gebruikt. |
| 5 | Verwijdert DIP afspraken hard? | **UNKNOWN.** Geen verwijder-indicatie in de API; `status: "rejected"` suggereert een zachte levenscyclus. |
| 6 | Rate limits | **UNKNOWN — niet vastgesteld, alleen niet waargenomen.** Geen documentatie, geen headers, geen 429 bij ~12 calls. Afwezigheid van bewijs is geen bewijs van afwezigheid. |
| 7 | `rent`-varianten van `properties` | **Gedeclareerd, niet waargenomen** in 4.217 records. De veldenlijst (`rent`, `other_charges`) komt uit de spec. |
| 8 | `/theaters/fees` → `400 "Not an agency"` terwijl `/contracts` wél werkt | Rechtenmodel per endpoint verschillend en niet gedocumenteerd. Buiten scope van dit ticket; relevant zodra iemand toeslagperiodes wil. |
| 9 | verkoopmonitor / verkoopmutaties / publieksmonitor | **UNKNOWN** of de sales-endpoints de monitors 1-op-1 dekken; voor publieksmonitor is **geen** endpoint gevonden. Zie het [entiteitenoverzicht](#de-dip-menu-items-uit-de-ui-afgezet-tegen-de-api). |
| 10 | Test-/acceptatie-omgeving | **Niet gevonden.** Alle onderzoek is tegen productie gedaan (read-only). |
| 12 | **`amount_rank2` t/m `amount_rank10` zijn 0 in 267/267 uitvoeringen** | **UNKNOWN** of deze negen velden bij een andere producent of theatertype wél vullen. Alleen `amount_rank1` droeg data (299–1.559). Gesignaleerd voor config-builder: negen kolommen meenemen die altijd 0 zijn, of niet. |
| 13 | `private`, `in_festival` en `isOtherLocation` zijn `false` in 267/267 | Geen variatie waargenomen; de velden zijn niet te valideren op betekenis. `isOtherLocation` is bovendien het enige camelCase-veld in de API — een naamgevingsafwijking, geen fout. |
| 14 | Werken `co_producers`, `accompanied_by_producers`, `cast_members` en `forms` ooit? | **Leeg in élke waargenomen rij** (101 producties, 267 uitvoeringen). Het elementtype is daardoor **nooit waargenomen** en komt uitsluitend uit de spec. Relevant zodra iemand ze nodig heeft — `cast_members` draagt dan persoonsgegevens. |
| 15 | Tijdzone van `sales.updated` en `performances.date` | **UNKNOWN.** Geen offset in de waarde, niets in de spec — dezelfde onduidelijkheid als bij `contracts.modified` (vraag 4). |
| 16 | Geldt de HTTP 400 van `/sales` ook voor `/performances`? | **Niet waargenomen.** Alle 10 bemonsterde producties gaven 200 op `/performances`, ook die met één uitvoering. Of een productie zonder uitvoeringen bestaat, en wat dat endpoint dan doet, is **UNKNOWN**. |
| 11 | `allow_new_connectors` kan op `false` staan voor de klant | Geen blokkade voor dít onderzoek: DIP is een **bestaande** connector, dit betreft een entiteitsuitbreiding, geen nieuwe bron. Gesignaleerd voor config-builder. |

---

**Onderzoek uitgevoerd:** `contracts` en `/borderellen` op **17-07-2026**; `productions`, `performances`,
`theaters` en `sales` op **25-08-2026**. · **Bewijs:** OpenAPI-contract
`https://external-api.dip.nl/swagger/v1/swagger.json` (opnieuw opgehaald op 25-08-2026, 280 KB) + live
`GET`-calls tegen productie met DIP-credentials uit de Key Vault van de klant, via
`scripts/probe_source_api.py` — de waarden blijven server-side en komen nooit in beeld.
Er zijn uitsluitend leesacties uitgevoerd; er is geen enkele schrijfactie tegen DIP gedaan.

**Dekking van de meting van 25-08-2026:** `productions` en `theaters` volledig (101 respectievelijk 819
records); `performances` en `sales` op een **steekproef van 10 producties**, gespreid over alle 13 seizoenen —
264 uitvoeringen en 171 verkooprijen. Volumes voor die twee zijn daarom **extrapolaties**, expliciet als
zodanig gemarkeerd. Er is geen enkele 429 opgetreden in ~35 opeenvolgende calls.
