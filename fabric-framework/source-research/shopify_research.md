# Shopify API-onderzoek

Onderzoek naar de **Shopify Admin API** — de bron zoals een connector hem ziet: authenticatie,
entiteiten, paginering, incrementeel ophalen, veldtypen en rate limits.

**Scope:** verkooporders (inclusief orderregels), producten en productvarianten, plus klanten.
Deze scope is overgenomen uit de eerste meting van 21-08-2026 en in deze ronde **niet uitgebreid**.
**Inventory (voorraad) valt expliciet buiten scope** en is niet uitgezocht.

**Bewijsbasis.** Dit rapport is **live gemeten** tegen een echte productiewinkel, uitsluitend met
leesacties. Twee meetronden:

| Ronde | Datum | Wat |
|---|---|---|
| v1.0 | **21-08-2026** | eerste volledige meting |
| v1.1 | **28-08-2026** | volledige herverificatie van elke bevinding hieronder, plus correcties en nieuwe bevindingen |

Elk genoemd veld, elke limiet en elk voorbeeld komt uit een **echte respons**, tenzij er expliciet
`ONBEVESTIGD` of `UNKNOWN` bij staat. Waar de officiële documentatie en de waarneming van elkaar
afwijken, staat de waarneming voor.

**Meetcontext, in algemene termen.** De gemeten winkel is een productiewinkel op Shopify's
`Advanced`-plan (`plan.partnerDevelopment = false`, `plan.shopifyPlus = false`), aangemaakt in 2023,
tijdzone `Europe/Amsterdam`, valuta `EUR`, met een orderhistorie vanaf medio 2023. Geen
development store: de gemeten limieten zijn echte productielimieten. Ze zijn wel **plan-gebonden** —
zie [Rate limits](#rate-limits).

**Waarom dit rapport bestaat.** Shopify is de eerste GraphQL-bron van het framework. De
GraphQL-ondersteuning in de generieke API-notebook was *geschreven maar nooit tegen een echte bron
uitgevoerd*, en de veldnamen waarmee het framework Shopify's kosten- en throttlerespons afhandelt
waren ingevuld op basis van algemene kennis van het mechanisme, niet op een waargenomen respons.
Dit rapport is het bewijsmateriaal onder die code: het bevestigt of corrigeert die namen met
**letterlijk geciteerde** responses. Zie [Rate limits](#rate-limits).

---

## Herstelnotitie — de platformkopie ontbrak

Dit hoort in het rapport thuis, want het verklaart waarom v1.1 bestaat en waaruit hij is
samengesteld.

**Wat er aan de hand was.** De catalogus (`source_research`) had een rij voor `shopify` op v1.0,
gevalideerd 21-08-2026, die verwees naar `fabric-framework/source-research/shopify_research.md` in
de platformrepo. **Dat bestand stond daar niet.** `--action list` meldde het als
`NOT IN PLATFORM REPO` en `--action get --source shopify` faalde met `NOT_FOUND`. De klantkopie in
`client-outputs/` bestond wél: 1057 regels, tijdstempel 21-08-2026.

**Wat de oorzaak was.** Het bestand is op **24-08-2026** verwijderd door een opruimcommit met de
boodschap *"Refactor code structure for improved readability and maintainability"*. Die commit
verwijderde in één keer **vijf** researchrapporten uit `fabric-framework/source-research/`
(`dip`, `hubspot`, `shopify`, `taxi`, `ticketcounter` — samen 3.390 regels). Alleen `dip` is daarna
opnieuw aangemaakt en gepusht; de andere vier zijn nooit hersteld. Het is dus geen research die
nooit is gedaan, maar research die tussen twee runs door verloren is gegaan.

**Waaruit is hersteld — en wat het verschil was.** De laatst bekende platformversie is teruggehaald
uit de gitgeschiedenis (de commit die hem op 21-08-2026 toevoegde) en vergeleken met de klantkopie:

| Vergelijking | Uitkomst |
|---|---|
| klantkopie ↔ laatst bekende platformkopie | **byte-identiek** — zelfde MD5, 1057 regels, `diff` leeg |
| inhoudelijke tegenspraak tussen de kopieën | **geen** |

De twee kopieën liepen dus **niet** uiteen; er viel op geen enkel punt iets te verzoenen. De merge
naar v1.1 is daarmee: de v1.0-inhoud als basis, waar deze ronde iets anders mat gaat de nieuwe
meting voor, en wat deze ronde niet opnieuw kon worden gecontroleerd blijft staan met een markering.
Zie [Wat er ten opzichte van v1.0 is veranderd](#wat-er-ten-opzichte-van-v10-is-veranderd).

**Wat hieruit te leren valt** — niet over Shopify, wel over het proces: een catalogusrij is geen
bewijs dat het rapport bestaat. Alleen een geslaagde `--action get` met een niet-leeg bestand is dat.

**Klantneutraliteit.** v1.0 was geschreven als klantdocument: winkelnaam, `myshopify`-domein,
Key Vault-naam, secretnaam en de naam van de klant stonden erin, en daarmee kon het nooit als
platformkopie worden gepubliceerd. v1.1 beschrijft de bron en niet de klant. Waar v1.0 een
klantspecifieke waarde noemde, staat hier de conventie of de rol; die waarden horen in de
klantconfig (secties 01–02), niet in gedeelde research.

## Inhoudsopgave

| Sectie | Omschrijving |
|---|---|
| [Herstelnotitie](#herstelnotitie--de-platformkopie-ontbrak) | Waarom v1.1 bestaat en waaruit hij is samengesteld |
| [Kernvragen — korte antwoorden](#kernvragen--korte-antwoorden) | De gestelde vragen, direct beantwoord |
| [TypeSource](#typesource) | Bevestigd bronprotocol |
| [Overzicht](#overzicht) | API-versie en versiebeleid |
| [Authenticatie](#authenticatie) | Headervorm, secretverwijzing, scopes |
| [Verbinding](#verbinding) | BaseUrl, RateLimitDelay, headers |
| [GraphQL of REST — per entiteit](#graphql-of-rest--per-entiteit) | Welke koppelingsvorm werkt, en of REST een terugvaloptie is |
| [Entiteitenoverzicht](#entiteitenoverzicht) | Wat er is, wat in scope is |
| [Paginering en ingestie per entiteit](#paginering-en-ingestie-per-entiteit) | Strategie, cursor en watermark per entiteit |
| [Rate limits](#rate-limits) | Letterlijk gemeten, beide varianten, inclusief de throttle |
| [Velden en voorbeeld-JSON per entiteit](#velden-en-voorbeeld-json-per-entiteit) | Veldcatalogus en echte samples |
| [Belangrijkste datakenmerken per entiteit](#belangrijkste-datakenmerken-per-entiteit) | Sleutels, watermarks, volumes |
| [Validatie tegen de general-notebooks](#validatie-tegen-de-general-notebooks) | Past dit op wat het framework kan? |
| [Persoonsgegevens](#persoonsgegevens) | Wat de bron bevat en hoe het is uitgesloten |
| [Wat er ten opzichte van v1.0 is veranderd](#wat-er-ten-opzichte-van-v10-is-veranderd) | Correcties, aanvullingen, vervallen bevindingen |
| [Openstaande vragen / UNKNOWNs](#openstaande-vragen--unknowns) | Alles wat niet is geverifieerd |

## Kernvragen — korte antwoorden

| # | Vraag | Antwoord |
|---|---|---|
| 1 | Zijn de vier rate-limitveldnamen die het framework aanneemt correct? | **JA — alle vier letterlijk bevestigd** op een op **28-08-2026** uitgelokte `THROTTLED`-respons: `errors[].extensions.code == "THROTTLED"`, `extensions.cost.requestedQueryCost`, `extensions.cost.throttleStatus.currentlyAvailable` en `extensions.cost.throttleStatus.restoreRate`. **Eén correctie, op de documentatie en niet op de code:** de foutcode staat in `errors[].extensions.code`, **niet** in het top-level `extensions`-blok. Zie [Rate limits](#rate-limits). |
| 2 | GraphQL of REST? | **GraphQL, op API-versie `2026-07`, voor alle entiteiten in scope.** REST is voor alle vier de entiteiten nog steeds een **werkende terugvaloptie**, met precies één harde beperking (paginering + filter gaan niet samen) en één afschrijvingssignaal (Products en Variants). Zie [GraphQL of REST — per entiteit](#graphql-of-rest--per-entiteit). |
| 3 | Kan elke entiteit incrementeel? | **Ja, alle vier**, via `query: "updated_at:>='<start>'"` op de GraphQL-connectie met `sortKey: UPDATED_AT`. De ondergrens is inclusief en werkt exact op de seconde. Orderregels erven het watermark van de bovenliggende order. |
| 4 | Geldt de 60-dagenbeperking van `read_orders`? | **NEE bij deze rechten.** Het gebruikte token draagt `read_all_orders`; de oudste opgehaalde order dateert van ruim drie jaar vóór de meting. Een volledige historische load kan. Dit is een eigenschap van de **app-installatie**, niet van de API — zie [Authenticatie](#authenticatie). |
| 5 | Kunnen orderregels een eigen bron-entiteit worden? | **NEE.** Er bestaat geen top-level `lineItems`-query — geverifieerd via introspectie van 268 `QueryRoot`-velden op 28-08-2026. Orderregels komen alleen genest binnen `orders` mee. Varianten kunnen dat **wel**: `productVariants` bestaat als top-level query. |
| 6 | Zijn er blokkades voor de bouwfase? | **Niet meer.** Shopify weigert de `Authorization`-header en eist een eigen header. Het framework ondersteunt dat inmiddels rechtstreeks via `AuthDetails.AuthHeaderName`; de omweg die v1.0 nog beschreef is vervallen. Zie [Validatie tegen de general-notebooks](#validatie-tegen-de-general-notebooks). |
| 7 | Zijn er stille valkuilen? | **Twee, allebei gemeten.** (a) `productVariantsCount` **negeert het `query`-filter stilzwijgend** en geeft altijd het totaal terug. (b) Een datumfilter zónder aanhalingstekens wordt fout geparseerd tot een tweede, onzinnig zoekveld — zonder dat de call faalt. |

## TypeSource

- **Bevestigd:** `api` — HTTP/JSON over HTTPS.
- **TypeIngestion:** `api_graphql` voor alle entiteiten in scope. GraphQL is binnen dit framework
  **geen** aparte TypeSource: het is een POST met een body over dezelfde client, dezelfde
  authenticatie en dezelfde Bronze-landing als REST. De bron blijft `type_source: "api"` en
  varieert alleen per entiteit.
- **Gevolg:** deze bron heeft ook een **sectie 06** (`06_queries.graphql`) nodig — het
  querydocument met één benoemde operatie per entiteit.

## Overzicht

### API-versie

- **Gebruikte en aanbevolen versie: `2026-07`** — de actuele stabiele versie, opnieuw bevestigd op
  28-08-2026 door de responsheader `X-Shopify-API-Version: 2026-07` op élke call.
- Shopify versioneert **vier keer per jaar**; elke versie wordt minimaal 12 maanden ondersteund.
  De versie staat in het **URL-pad**, dus een versiewissel is een configwijziging (`BaseUrl`),
  geen codewijziging.
- **Let op:** endpoints *zonder* versie in het pad — zoals `/admin/oauth/access_scopes.json` —
  antwoordden met `X-Shopify-API-Version: 2025-10`. Dat is de op de app vastgezette versie, niet de
  nieuwste. Zet de versie daarom **altijd expliciet** in het pad.
- `GET /admin/api/api_versions.json` gaf **HTTP 404** (herbevestigd 28-08-2026): de versielijst is
  via dat pad niet op te vragen.

## Authenticatie

- **Patroon:** statieke API-key (`StaticTokenAuth`) — pattern A uit `01_source_config.template.md`.
- **AuthScheme / Method:** `token` / `api_key`.
- **Secret:** één Admin API access token van een custom app. **De naam van het secret en de Key
  Vault waarin het staat horen in de klantconfig (sectie 01), niet in dit rapport.** De waarde is
  server-side uit de Key Vault gelezen en staat nergens in dit rapport, in geen voorbeeldcommando
  en in geen log.
- **Token endpoint:** n.v.t. — geen OAuth2-flow, geen tokenuitwisseling, geen verlooptijd.

### De headervorm is dwingend

Shopify accepteert **uitsluitend** `X-Shopify-Access-Token`. Gemeten op
`GET /admin/api/2026-07/shop.json`, opnieuw op **28-08-2026**:

| Verstuurde header(s) | Resultaat |
|---|---|
| `X-Shopify-Access-Token: <token>` | **HTTP 200** |
| `Authorization: Bearer <token>` | **HTTP 401** |
| `Authorization: Token <token>` | **HTTP 401** |
| geen auth-header | **HTTP 401** |
| `Authorization: Token <token>` **én** `X-Shopify-Access-Token` | **HTTP 200** |
| `Authorization: Bearer <token>` **én** `X-Shopify-Access-Token` | **HTTP 200** |

Twee dingen volgen hieruit. Ten eerste: het credential moet in `X-Shopify-Access-Token`, als
**kale waarde** zonder schemaprefix — een prefix hoort bij de `Authorization`-grammatica, niet bij
een vendorheader. Ten tweede: een overbodige `Authorization`-header wordt **genegeerd** zolang de
juiste header aanwezig is. Dat tweede was in v1.0 het bewijs dat de bron ondanks de toenmalige
frameworkbeperking bereikbaar was; inmiddels is die beperking weg (zie
[Validatie tegen de general-notebooks](#validatie-tegen-de-general-notebooks)) en is het alleen nog
een prettige eigenschap.

### Scopes — gemeten, niet aangenomen

`GET /admin/oauth/access_scopes.json` gaf **HTTP 200** met 17 scopes (herbevestigd 28-08-2026):

```
read_all_orders          read_analytics         read_content
read_customers           read_discounts         read_draft_orders
read_fulfillments        read_gift_cards        read_inventory
read_locations           read_marketing_events  read_orders
read_price_rules         read_products          read_reports
read_shipping            read_shopify_payments_payouts
```

Alle scopes zijn **lees-scopes**; er zit geen enkele `write_`-scope op. Voor de entiteiten in scope
is de dekking volledig: `read_orders` + `read_all_orders`, `read_products`, `read_customers`.

Dit endpoint is de enige betrouwbare manier om te weten wat een token mag. Voer hem uit bij elke
tokenwissel — Shopify meldt ontbrekende rechten niet als fout, maar als minder data.

### De 60-dagenbeperking van `read_orders`

Shopify's documentatie beschrijft dat `read_orders` alleen orders binnen *"the default window of
orders created within the last 60 days"* teruggeeft, en dat `read_all_orders` die beperking opheft.
`read_all_orders` moet Shopify apart goedkeuren.

**Op het gemeten token staat `read_all_orders`, en dat is ook feitelijk werkzaam.** Twee
onafhankelijke bewijzen uit echte responses (28-08-2026):

1. De oudste order die de API teruggeeft is `name` **`#1001`**, `createdAt`
   **`2023-06-08T12:09:52Z`** — ruim 1.100 dagen vóór de meetdatum, dus ver buiten elk
   60-dagenvenster.
2. `ordersCount` met filter `created_at` in 2023 geeft **3.281**, `precision: EXACT`. Met alleen
   `read_orders` zou dat 0 zijn geweest.

Een volledige historische load is dus mogelijk zolang deze scope op de installatie staat.

> **Waarschuwing.** `read_all_orders` hangt aan de **app-installatie**. Wordt het token opnieuw
> uitgegeven of de app opnieuw geïnstalleerd zonder dat de goedkeuring meekomt, dan valt de API
> stilzwijgend terug op 60 dagen — zonder foutmelding, met simpelweg minder records.

## Verbinding

| Sleutel | Waarde |
|---|---|
| `BaseUrl` | `https://<shop>.myshopify.com/admin/api/2026-07` — het `myshopify`-subdomein van de klant hoort in sectie 01 |
| `KeyVaultUrl` | de Key Vault van de klant (sectie 01) |
| `RateLimitDelay` | **`0.5`** (seconden) — zie onderbouwing hieronder |
| `AuthDetails.AuthHeaderName` | `X-Shopify-Access-Token` |

**Onderbouwing `RateLimitDelay = 0.5`.** Voor GraphQL is dit ruim: een pagina van 250 orders mét
orderregels kostte gemeten **35 punten werkelijk verbruik**, terwijl het budget met **200
punten/seconde** aangroeit — één request per halve seconde verbruikt dus tientallen punten en
herstelt er honderd. Voor REST is 0,5 s óók veilig: de gemeten harde grens is **4 requests per
seconde**, dus 2 req/s zit op de helft. De waarde is bewust conservatief zodat hij blijft werken op
een lager Shopify-plan, waar alle limieten halveren.

## GraphQL of REST — per entiteit

**Kort:** GraphQL op `2026-07` voor alles in scope. REST werkt nog voor alles in scope en is een
**bruikbare terugvaloptie**, maar met een gemeten beperking die bepaalt *waarvoor* je hem kunt
inzetten.

### Uitspraak per entiteit

| Entiteit | Werkende koppelingsvorm | Waarom | REST als terugvaloptie? |
|---|---|---|---|
| `orders` | **GraphQL** — `orders`-connectie, cursor + `query`-filter | filter en cursor gaan samen; UTC-tijdstempels; velden selecteerbaar (persoonsgegevens uitsluitbaar) | **JA, met beperking.** `GET /orders.json` gaf HTTP 200 en draagt **geen** deprecation-header. Bruikbaar zolang de delta in één pagina van 250 past — daarboven breekt de paginering (zie hieronder) |
| `order_line_items` | **GraphQL, genest in `orders`** — geen eigen top-level query | `lineItems` bestaat alleen als connectie op `Order`; introspectie bevestigt dat `lineItem`/`lineItems` op `QueryRoot` **afwezig** zijn | **JA, in dezelfde vorm.** REST heeft evenmin een losse regel-endpoint; `GET /orders.json` levert `line_items[]` genest mee (25 velden per regel, gemeten). De terugvaloptie is dus even goed én even beperkt als GraphQL |
| `products` | **GraphQL** — `products`-connectie | zelfde patroon als orders; `variantsCount` maakt afkapping detecteerbaar | **JA, maar afgeschreven.** `GET /products.json` gaf HTTP 200 mét `X-Shopify-API-Deprecated-Reason`. Werkt vandaag; gebruik het niet voor nieuwbouw |
| `product_variants` | **GraphQL** — top-level `productVariants`-connectie, óf genest onder `products` | beide bestaan en filteren correct op `updated_at` | **JA, maar afgeschreven.** `GET /variants.json` gaf HTTP 200 mét `X-Shopify-API-Deprecated-Reason`; nesten binnen `GET /products.json` kan ook |
| `customers` | **GraphQL** — `customers`-connectie | **doorslaggevend:** bij GraphQL bepaalt de query welke velden over de lijn komen, dus persoonsgegevens zijn uitsluitbaar bij het ophalen | **TECHNISCH JA, functioneel afgeraden.** `GET /customers.json` gaf HTTP 200 zonder deprecation-header, maar levert ongevraagd `first_name`, `last_name`, `email`, `phone` en volledige adressen. Als terugvaloptie betekent dat: persoonsgegevens ontvangen en achteraf redigeren |

### 1. Wat Shopify zelf in de headers meestuurt

Gemeten op versie `2026-07`, opnieuw op **28-08-2026**:

| REST-endpoint | HTTP | `X-Shopify-API-Deprecated-Reason` | `Sunset` |
|---|---|---|---|
| `GET /orders.json` | 200 | *(geen)* | *(geen)* |
| `GET /orders/count.json` | 200 | *(geen)* | *(geen)* |
| `GET /customers.json` | 200 | *(geen)* | *(geen)* |
| `GET /customers/count.json` | 200 | *(geen)* | *(geen)* |
| `GET /products.json` | 200 | `https://shopify.dev/api/admin-rest/latest/resources/product` | *(geen)* |
| `GET /products/count.json` | 200 | `https://shopify.dev/api/admin-rest/latest/resources/product` | *(geen)* |
| `GET /variants.json` | 200 | `https://shopify.dev/api/admin-rest/latest/resources/product-variant` | *(geen)* |

De REST Admin API heet bij Shopify *"a legacy API as of October 1, 2024"*, en sinds 1 april 2025
moeten nieuwe **publieke** apps op GraphQL gebouwd zijn. Voor een **custom app** geldt die
verplichting formeel niet — en dat komt overeen met wat we meten: alles antwoordt gewoon met 200.

**Er is nergens een `Sunset`-header waargenomen** en in de geraadpleegde documentatie staat geen
einddatum per resource. Externe bronnen melden dat `products/count.json` in `2025-10` verwijderd
zou zijn; **dat is hier weerlegd** — het endpoint gaf een geldige telling terug. Behandel externe
einddatums dus als onbevestigd.

### 2. De beperking die bepaalt waarvoor REST bruikbaar blijft

Dit is de reden die niet omzeild kan worden, en hij is **gemeten**, niet afgeleid.

Shopify's REST pagineert met een cursor in de `Link`-header. Zodra je een `page_info`-cursor
meestuurt, mag je **geen enkele filterparameter meer meesturen** — alleen `limit` en `fields`.
Letterlijk gemeten antwoord bij `page_info` + `updated_at_min` samen (28-08-2026), **HTTP 400**:

```json
{
  "errors": {
    "updated_at_min": "updated_at_min cannot be passed when page_info is present. See https://shopify.dev/api/usage/pagination-rest for more information."
  }
}
```

Dezelfde call met alléén `limit` + `page_info` gaf **HTTP 200**. Het datumfilter zit bij REST
versleuteld ín de cursor — zichtbaar in de base64 van de `Link`-header, die `updated_at_min` en
`status` letterlijk meedraagt.

**Wat dat praktisch betekent, preciezer dan v1.0 het stelde.** Er is geen `Link`-header zolang het
resultaat in één pagina past. Gemeten: `GET /orders.json?limit=250&updated_at_min=<7 dagen terug>`
gaf **116 records, HTTP 200, géén `Link`-header**. Daaruit volgt:

| REST-scenario | Werkt? |
|---|---|
| dagelijkse delta die binnen één pagina van 250 past | **JA** — één call, filter mag mee, geen cursor nodig |
| delta groter dan 250 records | **NEE** — pagina 2 vereist `page_info`, en dan is `updated_at_min` verboden (HTTP 400) |
| volledige historische load | **NEE langs deze weg** — dat zijn honderden pagina's |

Dat botst met hoe dit framework REST-requests bouwt: `Details.ExtraParams` wordt bij de
`marker`-strategie **aan iedere pagina** toegevoegd, ook aan de vervolgpagina's. Een REST-config met
`updated_at_min` in `ExtraParams` haalt pagina 1 op en loopt daarna op **elke** volgende pagina vast
op HTTP 400.

**GraphQL heeft dit probleem niet** — daar mag en moet het filter juist bij élke pagina mee.
Gemeten met `first: 2` en filter `updated_at:>='2026-08-01T00:00:00Z'` (28-08-2026):

| Aanroep | Resultaat |
|---|---|
| pagina 1 (`first` + `query`) | twee orders, oplopend in `updatedAt` |
| pagina 2 (`first` + `query` + `after`) | de volgende twee orders |
| pagina 2 (`first` + `after`, **zónder** `query`) | **identiek dezelfde twee orders** |

Filter en cursor gaan dus probleemloos samen, en de cursor draagt de filtercontext zelf al. Dat is
precies het patroon dat het framework bouwt (`FilterVar` en `CursorVar` samen in `variables`) —
compatibel, zonder aanpassing.

### 3. Waarvoor REST vroeger nodig was, en nu niet meer

v1.0 adviseerde de REST-`count`-endpoints te gebruiken omdat GraphQL's `*Count`-velden
`precision: "AT_LEAST"` zouden geven. **Dat is in deze ronde gecorrigeerd.** De aftopping komt van
het `limit`-argument, en dat argument mag hoger:

| Aanroep | Resultaat |
|---|---|
| `ordersCount` (zonder `limit`) | `10000`, `AT_LEAST` |
| `ordersCount(limit: 1000)` | `1000`, `AT_LEAST` |
| `ordersCount(limit: 10000)` | `10000`, `AT_LEAST` |
| `ordersCount(limit: 100000)` | **`23770`, `EXACT`** |
| `ordersCount(limit: 1000000)` | **`23770`, `EXACT`** |

Zet `limit` boven het verwachte totaal en GraphQL geeft een **exact** getal. De REST-count-endpoints
gaven op dezelfde dag exact dezelfde getallen (orders 23.770, products 765, customers 245.503), dus
beide routes zijn eensluidend. **REST is voor tellen dus niet langer nodig.**

**Eén uitzondering, en die is nieuw en stil:** `productVariantsCount` **negeert het `query`-filter**.
Zie [de valkuil bij product_variants](#product_variants--een-stille-valkuil-in-de-telling).

## Entiteitenoverzicht

| Entiteit | GraphQL-operatie | UrlPath | In scope | Parent | Opmerkingen |
|---|---|---|---|---|---|
| `orders` | `orders` | `graphql.json` | **Ja** | — | 23.770 records gemeten; `read_all_orders` actief |
| `order_line_items` | genest in `orders` | *(geen eigen call)* | **Ja** | `orders` | **Geen top-level query** — komt genest mee, wordt in Silver uitgeklapt |
| `products` | `products` | `graphql.json` | **Ja** | — | 765 records gemeten |
| `product_variants` | `productVariants` | `graphql.json` | **Ja** | `products` (logisch) | 948 records gemeten; kan óók als **eigen** entiteit met eigen watermark |
| `customers` | `customers` | `graphql.json` | **Ja** | — | 245.503 records gemeten |
| `inventoryItems`, `inventoryLevels` | — | — | **Nee** | — | **Expliciet buiten scope** |
| `events` | `events` | `graphql.json` | Nee (kandidaat) | — | Mogelijke bron voor verwijderdetectie — zie hieronder |
| `draftOrders`, `fulfillments`, `refunds`, `locations`, `priceRules`, `discounts` | — | — | Nee | — | Toegankelijk met de gemeten scopes, niet gevraagd |

De `QueryRoot` telt **268** top-level velden. Via introspectie geverifieerd op **28-08-2026**:

| Veld | Status |
|---|---|
| `orders`, `ordersCount` | PRESENT |
| `products`, `productsCount` | PRESENT |
| `productVariants`, `productVariantsCount` | PRESENT |
| `customers`, `customersCount` | PRESENT |
| `events`, `bulkOperation` | PRESENT |
| `lineItem`, `lineItems` | **ABSENT** |

### Orderregels kunnen geen eigen bron-entiteit worden

Omdat er geen top-level `lineItems`-query bestaat, moeten orderregels genest binnen `orders`
opgehaald worden. Een geneste connectie kapt **stilzwijgend** af: `lineItems(first: N)` geeft
hooguit N regels terug zonder foutmelding.

**Gemeten risico, over de 100 meest recent gewijzigde orders (28-08-2026):**

| Maat | Waarde |
|---|---|
| minimum aantal orderregels per order | 1 |
| **maximum** | **13** |
| gemiddelde | 2,38 |
| orders die tegen de limiet van 250 aanliepen | **0** |

Met `lineItems(first: 250)` — het maximum dat GraphQL toestaat — is er een marge van ruim 19× op de
zwaarste waargenomen order. **Selecteer desondanks altijd `lineItems { pageInfo { hasNextPage } }`
mee**, zodat afkapping zichtbaar wordt als het assortiment ooit verandert.

### Verwijderdetectie

Geen van de entiteiten in scope levert een "deleted"-vlag of een tombstone-record. Wél bestaat er
een `events`-feed die verwijderingen registreert. Gemeten met filter `verb:destroy` (28-08-2026),
met geredigeerde appnaam:

```json
{
  "id": "gid://shopify/BasicEvent/186050315682119",
  "action": "destroy",
  "appTitle": "REDACTED — naam van een integratie-app van derden",
  "attributeToApp": false,
  "attributeToUser": false,
  "createdAt": "2026-06-30T08:50:22Z",
  "criticalAlert": false,
  "message": "",
  "subjectId": "gid://shopify/ProductVariant/54253411402055",
  "subjectType": "PRODUCT_VARIANT"
}
```

`subjectId` en `subjectType` koppelen het event aan het verwijderde record, en dat is precies wat
verwijderdetectie nodig heeft. Verwijderdetectie via `events` is daarmee **technisch haalbaar**,
maar **niet end-to-end uitgewerkt** — de bewaartermijn van de feed en de dekking per entiteitstype
zijn niet gemeten. Zie [UNKNOWNs](#openstaande-vragen--unknowns).

## Paginering en ingestie per entiteit

Alle entiteiten in scope volgen hetzelfde patroon: `api_graphql`, strategie `marker`
(cursorpaginering), watermark op `updatedAt`.

**Gemeten paginagrenzen (28-08-2026):**

| Grens | Waarneming |
|---|---|
| GraphQL `first` maximum | **250**. `first: 251` gaf `code: "BAD_REQUEST"` met de boodschap `first cannot exceed 250. To query larger amounts of data with fewer limits, bulk operations should be used instead.` |
| REST `limit` maximum | **250**. `limit=251` gaf HTTP 400 `{"errors":"Limit exceeds maximum limit of 250"}` |
| Geneste connectie (`lineItems`, `variants`) | eveneens **250** |

**Waarom `CursorResetPerRun: true` verplicht is.** Een Shopify-cursor is een base64-string die de
positie *binnen één zoekresultaat* codeert. Gedecodeerd ziet hij eruit als
`{"last_id": <n>, "last_value": "<sorteerwaarde>"}` — bij `sortKey: UPDATED_AT` is `last_value` de
`updatedAt` van het laatste record van de pagina. Hij is niet betekenisvol in een volgende run met
een ander datumfilter. De incrementele voortgang hoort daarom in het **watermark**
(`WatermarkDetails.Source = "data_column"`, `Field = "updatedAt"`), niet in de cursor.

### Het datumfilter moet tussen aanhalingstekens — bevestigd, met bewijs

De vorm `updated_at:>='{start}'` **mét** enkele aanhalingstekens is aantoonbaar de juiste; de vorm
zonder is stil kapot. Herbevestigd op 28-08-2026.

Zonder aanhalingstekens (`updated_at:>=2026-01-01T00:00:00Z`) rapporteert Shopify in
`extensions.search`:

```json
"parsed": {
  "and": [
    { "field": "updated_at", "range_gte": "2026-01-01T00:00:00+01:00" },
    { "field": "00", "match_all": "00Z" }
  ]
},
"warnings": [
  { "field": "00", "message": "Invalid search field for this query.", "code": "invalid_field" }
]
```

De zoekparser knipt de tijdstempel op de dubbele punten en maakt er een tweede, onzinnige zoekterm
`00` van. De call faalt niet — hij levert stilzwijgend een ander resultaat. Mét aanhalingstekens
(`updated_at:>='2026-01-01T00:00:00Z'`) verdwijnt het hele `extensions.search`-blok: de query wordt
schoon geparseerd, zonder waarschuwing.

**De tijdzone is daarbij correct.** Getest op de seconde tegen een order met een bekende `updatedAt`:

| Filter | Bevat de order? |
|---|---|
| `updated_at:>='<updatedAt van de order>'` | **Ja** — de ondergrens is inclusief |
| `updated_at:>='<updatedAt + 1 seconde>'` | **Nee** — precies één seconde later valt hij eruit |

De `Z`-notatie wordt dus als echte UTC geïnterpreteerd, exact op de seconde. Er is **geen**
tijdzoneverschuiving naar de winkeltijdzone. De `+01:00` in het `parsed`-blok hierboven was een
bijproduct van de kapotte parse, niet van de tijdzone.

> **Let op — REST verschilt hierin.** GraphQL geeft tijdstempels in UTC
> (`2026-08-28T06:59:14Z`), REST in **winkel-lokale tijd mét offset**
> (`2026-08-28T06:59:14+02:00`) — allebei letterlijk gemeten op dezelfde dag. Bij een mengvorm van
> beide routes is dat een reële bron van fouten. Ook `tags` verschilt: GraphQL geeft een **array**,
> REST een **komma-gescheiden string** (leeg gemeten als `""`).

### orders

- **Strategy:** `marker` — **WatermarkType:** `date` — **UrlPath:** `graphql.json`
- **ExtraParams:** *geen* — bij `Method: "POST"` verboden; waarden gaan via GraphQL-variabelen
- **Output.RecordKey / RecordType:** `data.orders.nodes` / `keyed`
- **StrategyDetails:**
  - `Method`: `POST`
  - `GraphQL.OperationName`: `orders`
  - `GraphQL.PageSizeVar`: `first`
  - `GraphQL.CursorVar`: `after`
  - `GraphQL.FilterVar`: `q`
  - `GraphQL.FilterTemplate`: `updated_at:>='{start}'`
  - `Pagination.PageSize`: `250`
  - `Pagination.MarkerResponseKey`: `data.orders.pageInfo.endCursor`
  - `Pagination.MoreDataKey`: `data.orders.pageInfo.hasNextPage`
  - `Pagination.CursorResetPerRun`: `true`
- **WatermarkDetails:** `Source: "data_column"`, `Field: "updatedAt"`, `DefaultStart` op de datum
  van de oudste order (per winkel verschillend — bepaal hem met
  `orders(first: 1, sortKey: CREATED_AT)`), `Overlap` aanbevolen op enkele minuten
- **Extraction.BatchSize:** `2500` (10 pagina's) — **MaxTotalRecords:** geen
- **Sorteren:** `sortKey: UPDATED_AT`, oplopend (`reverse` weggelaten). Gemeten: opeenvolgende
  records liepen op in `updatedAt`, wat nodig is om het watermark veilig te kunnen bijwerken
  tijdens de run.
- **Kosten:** een pagina van 250 orders mét `lineItems(first: 250)` kostte
  `requestedQueryCost` 156 / `actualQueryCost` 35. Ruim onder de per-query-grens van 1000.

### order_line_items

Geen eigen ingestieblok: de regels komen mee in de `orders`-query en worden pas in Silver
uitgeklapt. De **parent key** is de `id` van de omvattende order; die moet bij het uitklappen
meegenomen worden.

### products

Identiek aan `orders`, met `OperationName: products`, `RecordKey: data.products.nodes`,
`MarkerResponseKey: data.products.pageInfo.endCursor` en
`MoreDataKey: data.products.pageInfo.hasNextPage`. `DefaultStart` op de aanmaakdatum van de winkel.
`PageSize` kan op `250`; een pagina van 250 producten met `variants(first: 250)` en `options` kostte
`requestedQueryCost` 167 / `actualQueryCost` 46.

### product_variants — een stille valkuil in de telling

`productVariants` bestaat als top-level query, filtert correct op `updated_at` en heeft een eigen
`updatedAt`. Config verder gelijk aan `products`, met `RecordKey: data.productVariants.nodes`.

**Maar `productVariantsCount` negeert het `query`-filter — stilzwijgend.** Gemeten 28-08-2026:

| Aanroep | Resultaat |
|---|---|
| `productVariantsCount(limit: 10000)` | `948`, `EXACT` |
| `productVariantsCount(limit: 10000, query: "updated_at:>='2026-08-21T00:00:00Z'")` | **`948`**, `EXACT` |
| `productVariantsCount(limit: 10000, query: "updated_at:>='2026-08-27T00:00:00Z'")` | **`948`**, `EXACT` |
| `productVariantsCount(limit: 10000, query: "updated_at:>='2027-01-01T00:00:00Z'")` | **`948`**, `EXACT` — een datum in de toekomst |
| `productVariants(first: 250, query: "updated_at:>='2026-08-27T00:00:00Z'")`, doorgepagineerd | **53** records |
| `productVariants(first: 5, query: "updated_at:>='2027-01-01T00:00:00Z'")` | **0** records |

De **connectie** filtert dus wél correct; alleen het **count-veld** doet dat niet. Het geeft
`EXACT` terug bij een filter dat het niet toepast — de gevaarlijkste combinatie die er is.

Het enige signaal staat in `extensions.search`, en alleen als je ernaar kijkt. Letterlijk:

```json
[
  {
    "path": ["productVariantsCount"],
    "query": "updated_at:>='2026-08-21T00:00:00Z'",
    "parsed": { "field": "updated_at", "range_gte": "2026-08-21T00:00:00Z" },
    "warnings": [
      { "field": "updated_at", "message": "Invalid search field for this query.", "code": "invalid_field" }
    ]
  }
]
```

Ter contrast: `ordersCount`, `productsCount` en `customersCount` **honoreren** hetzelfde filter wél
— met een toekomstige datum gaven ze alle drie `0`, en geen van de drie leverde een
`extensions.search`-blok op.

**Gevolg:** gebruik `productVariantsCount` **nooit** om een delta te verifiëren of te monitoren.
Tel de opgehaalde nodes, of tel via de doorgepagineerde connectie.

**Afweging voor de config-builder:** varianten genest binnen `products` ophalen is eenvoudiger
(één call, één watermark), maar mist in theorie variantwijzigingen die het product niet aanraken.
Gemeten over de 250 varianten die in een venster van zeven dagen wijzigden: **0** hadden een product
waarvan de `updatedAt` buiten dat venster viel. In de gemeten winkel bewegen product en variant dus
samen. Dat is één winkel en één venster — geen algemene garantie.

### customers

Identiek aan `orders`, met `OperationName: customers`, `RecordKey: data.customers.nodes`,
`MarkerResponseKey: data.customers.pageInfo.endCursor` en
`MoreDataKey: data.customers.pageInfo.hasNextPage`. Bij 245.503 records en `PageSize: 250` is een
volledige load **983 pagina's**. Een pagina van 2 klanten zonder persoonsgegevensvelden kostte
`requestedQueryCost` 10 / `actualQueryCost` 8.

## Rate limits

Dit is het kernonderdeel van dit onderzoek. Beide varianten zijn **letterlijk uitgelokt en
vastgelegd op 28-08-2026** — de GraphQL-kostenvariant én de REST-headervariant. Niets in deze
sectie is uit documentatie afgeleid; waar iets wél uit documentatie komt, staat dat erbij.

### Variant 1 — GraphQL: `extensions.cost`

Elke succesvolle GraphQL-respons draagt een `extensions.cost`-blok. Letterlijk, uit een echte
respons van 28-08-2026:

```json
"extensions": {
  "cost": {
    "requestedQueryCost": 2,
    "actualQueryCost": 2,
    "throttleStatus": {
      "maximumAvailable": 4000.0,
      "currentlyAvailable": 3998,
      "restoreRate": 200.0
    }
  }
}
```

| Veldpad | Gemeten | Betekenis |
|---|---|---|
| `extensions.cost.requestedQueryCost` | wisselend | Vooraf geschatte kosten; **hierop** wordt toegelaten of geweigerd |
| `extensions.cost.actualQueryCost` | wisselend, **`null` bij throttling** | Werkelijk verbruik; alleen bekend als de query is uitgevoerd |
| `extensions.cost.throttleStatus.maximumAvailable` | **`4000.0`** | Emmergrootte |
| `extensions.cost.throttleStatus.currentlyAvailable` | wisselend | Resterend budget |
| `extensions.cost.throttleStatus.restoreRate` | **`200.0`** | Aangroei per seconde |

De gemeten `restoreRate` van 200 punten/s komt overeen met wat Shopify voor het `Advanced`-plan
documenteert (Standard 100/s, Advanced 200/s, Plus 1000/s, Enterprise 2000/s — dat rijtje is
documentatie, alleen de 200 is gemeten). De emmer is 20× de aangroei per seconde.

**De emmer wordt belast met de werkelijke kosten, niet met de geschatte.** Gemeten: één query met
`requestedQueryCost` 862 en `actualQueryCost` 158 liet `currentlyAvailable` van 4000 naar **3842**
zakken — precies 158. De geschatte kosten bepalen de **toelating**, de werkelijke bepalen het
**verbruik**.

### De throttle-respons — letterlijk uitgelokt en gemeten

**Meetopstelling.** 16 gelijktijdige queries met elk `requestedQueryCost` **862**, afgevuurd in
**1,18 seconden**. Budget: 4000 punten, aangroei 200/s. Uitkomst: **4 geslaagd, 12 geweigerd met
`THROTTLED`**, alle 16 met **HTTP 200**.

De **letterlijke** respons van de eerste geweigerde query, ongewijzigd overgenomen:

```json
{
  "errors": [
    {
      "message": "Throttled",
      "extensions": {
        "code": "THROTTLED",
        "documentation": "https://shopify.dev/api/usage/rate-limits"
      }
    }
  ],
  "extensions": {
    "cost": {
      "requestedQueryCost": 862,
      "actualQueryCost": null,
      "throttleStatus": {
        "maximumAvailable": 4000.0,
        "currentlyAvailable": 572,
        "restoreRate": 200.0
      }
    }
  }
}
```

**HTTP-status: `200`.** Responsheaders op die 200: `x-shopify-api-version: 2026-07`,
`content-type: application/json; charset=utf-8`, en **geen `Retry-After`** — de volledige headerset
bevatte geen enkele rate-limit-header.

### De vier aannames van het framework, afgevinkt tegen deze meting

Dit is waarvoor deze meting is gedaan. Alle vier bevestigd, **letterlijk**:

| Aanname | Status | Bewijs uit de respons hierboven |
|---|---|---|
| `errors[].extensions.code == "THROTTLED"` | **BEVESTIGD — GEMETEN** | letterlijk `"code": "THROTTLED"` in `errors[0].extensions` |
| `extensions.cost.requestedQueryCost` | **BEVESTIGD — GEMETEN** | `862` |
| `extensions.cost.throttleStatus.currentlyAvailable` | **BEVESTIGD — GEMETEN** | `572` |
| `extensions.cost.throttleStatus.restoreRate` | **BEVESTIGD — GEMETEN** | `200.0` |

**Eén correctie, en die zit in de documentatie, niet in de code.** De statusbeschrijving van
`api_graphql` schrijft het pad als `extensions.code`. Dat pad bestaat niet: er is geen `code` in het
top-level `extensions`-blok. De foutcode staat in **`errors[].extensions.code`** — een ander
`extensions`-object, dat op het foutelement hangt. De notebookcode leest hem op de juiste plek
(`(e.get("extensions") or {}).get("code")` over `data["errors"]`); alleen de verkorte notatie in de
documentatie is misleidend. Neem het volledige pad over.

**De wachttijdformule klopt.** Het framework rekent
`(requestedQueryCost - currentlyAvailable) / restoreRate`. Op deze respons:
`(862 - 572) / 200 = 1,45 seconde`. Dat is de juiste wachttijd — na 1,45 s is er weer 862 punten
budget.

**Twee aanvullingen die uit de meting volgen:**

1. **`actualQueryCost` is `null` bij throttling.** Wie op dat veld terugvalt om de wachttijd te
   bepalen, rekent met `None`. Gebruik `requestedQueryCost` — zoals het framework doet.
2. **Er is géén `Retry-After` bij een GraphQL-throttle**, en de status is 200. Statuscode-gebaseerde
   afhandeling (de 429-tak) ziet dit dus niet. De GraphQL-tak is niet optioneel.

### Een derde limiet: `MAX_COST_EXCEEDED`

Naast de emmer van 4000 punten geldt een **harde bovengrens van 1000 punten per afzonderlijke
query**, ongeacht het resterende budget. Uitgelokt op 28-08-2026 met een query van 1293 punten.
Letterlijk:

```json
{
  "errors": [
    {
      "message": "Query cost is 1293, which exceeds the single query max cost limit (1000).\n\nSee https://shopify.dev/docs/api/usage/rate-limits for more information on how the\ncost of a query is calculated.\n\nTo query larger amounts of data with fewer limits, bulk operations should be used instead.\nSee https://shopify.dev/docs/api/usage/bulk-operations/queries for usage details.\n",
      "extensions": {
        "code": "MAX_COST_EXCEEDED",
        "cost": 1293,
        "maxCost": 1000,
        "documentation": "https://shopify.dev/api/usage/rate-limits"
      }
    }
  ]
}
```

**Let op de andere vorm:** bij `MAX_COST_EXCEEDED` ontbreekt het `extensions.cost`-blok op topniveau
**volledig** (gemeten: geen `extensions`-sleutel in de respons). De kosteninformatie zit in
`errors[0].extensions.cost` — een **geheel getal**, geen object — en `errors[0].extensions.maxCost`.
Dat is een wezenlijk andere structuur dan bij `THROTTLED`, en opnieuw proberen heeft geen zin: de
kosten zijn een eigenschap van de query, niet van het moment. De query moet kleiner.

**Praktische betekenis:** houd elke query onder 1000 punten. Gemeten kosten van echte pagina's
(28-08-2026):

| Query | `requestedQueryCost` | `actualQueryCost` |
|---|---|---|
| `shop`-info (platte velden) | 2 | 2 |
| 250 orders, alleen platte velden | 13 | 13 |
| 250 orders + `lineItems(first: 250) { id }` | 156 | 35 |
| 250 orders + `lineItems(first: 250)` met volledig veldpakket | 431 | 79 |
| 250 producten + `variants(first: 250)` + `options` | 167 | 46 |
| 3 varianten (top-level `productVariants`) | 10 | 10 |
| 2 klanten (zonder persoonsgegevens) | 10 | 8 |
| bovenstaande orderquery **tweemaal** in één document | 862 | 158 |
| bovenstaande orderquery **driemaal** in één document | **1293 — geweigerd** | n.v.t. |

De geschatte kosten liggen structureel **hoger** dan de werkelijke: Shopify rekent vooraf met het
maximale aantal nodes. De toets tegen de 1000-puntengrens gebeurt op de **geschatte** waarde, dus
daar moet je op ontwerpen.

### Variant 2 — REST: de `X-Shopify-Shop-Api-Call-Limit`-header

Elke REST-respons draagt:

```
X-Shopify-Shop-Api-Call-Limit: 1/80
```

De vorm is `<verbruikt>/<emmergrootte>`. De emmer is hier **80**. Onder belasting is de teller
gemeten oplopend van `1/80` tot en met **`80/80`** — alle 80 tussenwaarden zijn waargenomen.

**De 429 is letterlijk uitgelokt** met 120 gelijktijdige requests in ongeveer 6 seconden: 97 gaven
HTTP 200, **23 gaven HTTP 429**. Letterlijk gemeten:

```
HTTP/1.1 429 Too Many Requests
retry-after: 4.0
```
```json
{"errors":"Exceeded 4 calls per second for api client. Reduce request rates to resume uninterrupted service."}
```

| Waarneming | Waarde |
|---|---|
| Emmergrootte | **80** |
| Lekfrequentie | **4 requests/seconde** — letterlijk in de foutmelding |
| `Retry-After` bij 429 | **`"4.0"`** — een **decimaal getal als string**, geen geheel getal. Alle 23 waargenomen 429's gaven dezelfde waarde |
| `X-Shopify-Shop-Api-Call-Limit` bij een 429 | **afwezig** — de header ontbreekt juist op de respons die hem het hardst nodig heeft |
| Headernaam op de lijn | **`retry-after`, kleine letters** (HTTP/2). Een hoofdlettergevoelige lookup op `"Retry-After"` mist hem; `requests` lost dit zelf op met een hoofdletterongevoelige headermap |

> **Belangrijk voor iedereen die deze header verwerkt:** `Retry-After` is hier `"4.0"`, niet `"4"`.
> Een parser die de waarde als geheel getal leest, faalt op deze respons. Lees hem als decimaal.

### Samenvatting van de limieten

| | GraphQL | REST |
|---|---|---|
| Meeteenheid | kostenpunten | requests |
| Emmer | `4000` | `80` |
| Herstel | `200`/s | `4`/s |
| Per-query maximum | `1000` punten | n.v.t. |
| Signaal bij overschrijding | HTTP **200** + `errors[].extensions.code = "THROTTLED"` | HTTP **429** + `retry-after` |
| Budget zichtbaar in | `extensions.cost.throttleStatus` | header `X-Shopify-Shop-Api-Call-Limit` |
| `Retry-After` aanwezig | **nee** | ja, als decimaal (`"4.0"`) |

Beide limieten zijn **plan-gebonden**. De gemeten winkel zit op `Advanced`, wat volgens Shopify's
documentatie het dubbele is van `Standard`. Draait een winkel op een lager plan, dan **halveren** de
limieten (GraphQL 200 → 100 punten/s, REST 4 → 2 requests/s) en loopt een op 200/s afgestemde config
tegen throttling aan. **Alleen de Advanced-waarden zijn gemeten**; de andere plannen zijn
documentatie — `ONBEVESTIGD`.

## Velden en voorbeeld-JSON per entiteit

Alle voorbeelden hieronder zijn **echte responses**, opgehaald op **28-08-2026**, telkens **één
record**.

**Wat er in de samples is geredigeerd, en waarom.** Deze samples dienen om het schema uit af te
leiden, dus **sleutels en types blijven ongewijzigd**; alleen waarden die een persoon of de winkel
zouden aanwijzen zijn vervangen door `"REDACTED — <wat het was>"`. Concreet: klant- en adres-GID's,
productnamen, artikelnummers, leveranciersnamen, appnamen en de winkel-URL. Alles wat structuur,
type of nullability laat zien — tijdstempels, bedragen, enums, GID-vorm, `null`-waarden — is
onaangeroerd overgenomen.

### orders

| API-veld | Type | Nullable | Opmerkingen |
|---|---|---|---|
| `id` | String (GID) | nee | **Primaire sleutel.** Vorm `gid://shopify/Order/<n>` |
| `legacyResourceId` | String (numeriek) | nee | Het numerieke REST-id; handig als joinsleutel |
| `name` | String | nee | Ordernummer zoals getoond, bv. `#24364` |
| `createdAt` | Timestamp (UTC) | nee | |
| `updatedAt` | Timestamp (UTC) | nee | **Watermarkveld** |
| `processedAt` | Timestamp (UTC) | ja | |
| `cancelledAt` | Timestamp (UTC) | ja | `null` bij niet-geannuleerd |
| `cancelReason` | String (enum) | ja | bv. `OTHER` |
| `closed` / `confirmed` / `test` | Boolean | nee | |
| `closedAt` | Timestamp (UTC) | ja | |
| `currencyCode` | String (enum) | nee | bv. `EUR` |
| `displayFinancialStatus` | String (enum) | ja | bv. `PAID`, `REFUNDED` |
| `displayFulfillmentStatus` | String (enum) | nee | bv. `FULFILLED`, `UNFULFILLED` |
| `sourceName` | String | ja | het verkoopkanaal, bv. `shopify_draft_order` of een marktplaatsnaam |
| `tags` | Array&lt;String&gt; | nee | **In GraphQL een array; in REST een komma-string** |
| `currentTotalPriceSet` … `totalRefundedSet` | Object | ja | Genest `shopMoney { amount currencyCode }`; `amount` is een **String**, geen getal — cast naar decimal in Silver |
| `customer` | Object | ja | Alleen `id` opgehaald — zie [Persoonsgegevens](#persoonsgegevens) |
| `shippingAddress` | Object | ja | Alleen `countryCodeV2`, `provinceCode` opgehaald; `provinceCode` gemeten als `null` voor NL |
| `app` | Object | ja | `id`, `name` — welke app de order aanmaakte |
| `lineItems` | Object → `nodes[]` + `pageInfo` | nee | **Sub-schema vereist** |

**Sample JSON:**

```json
{
  "id": "gid://shopify/Order/8017484906823",
  "legacyResourceId": "8017484906823",
  "name": "#24364",
  "createdAt": "2026-08-02T08:17:13Z",
  "updatedAt": "2026-08-03T04:03:50Z",
  "processedAt": "2026-08-02T08:17:13Z",
  "cancelledAt": null,
  "cancelReason": null,
  "closed": true,
  "closedAt": "2026-08-03T04:03:50Z",
  "confirmed": true,
  "test": false,
  "currencyCode": "EUR",
  "displayFinancialStatus": "PAID",
  "displayFulfillmentStatus": "FULFILLED",
  "sourceName": "REDACTED — naam van een verkoopkanaal",
  "tags": [],
  "currentTotalPriceSet": { "shopMoney": { "amount": "25.98", "currencyCode": "EUR" } },
  "totalPriceSet":        { "shopMoney": { "amount": "25.98", "currencyCode": "EUR" } },
  "subtotalPriceSet":     { "shopMoney": { "amount": "25.98", "currencyCode": "EUR" } },
  "totalTaxSet":          { "shopMoney": { "amount": "0.0",   "currencyCode": "EUR" } },
  "totalDiscountsSet":    { "shopMoney": { "amount": "0.0",   "currencyCode": "EUR" } },
  "totalRefundedSet":     { "shopMoney": { "amount": "0.0",   "currencyCode": "EUR" } },
  "customer": { "id": "gid://shopify/Customer/REDACTED" },
  "shippingAddress": { "countryCodeV2": "NL", "provinceCode": null },
  "app": { "id": "gid://shopify/App/1234486", "name": "REDACTED — appnaam" },
  "lineItems": {
    "nodes": [
      {
        "id": "gid://shopify/LineItem/19635972571463",
        "name": "REDACTED — productnaam",
        "sku": "REDACTED — artikelnummer",
        "quantity": 1,
        "currentQuantity": 1,
        "requiresShipping": true,
        "taxable": true,
        "vendor": "REDACTED — leveranciersnaam",
        "product": { "id": "gid://shopify/Product/10283599298887" },
        "variant": { "id": "gid://shopify/ProductVariant/52057334350151" },
        "originalUnitPriceSet": { "shopMoney": { "amount": "25.98", "currencyCode": "EUR" } },
        "discountedTotalSet":   { "shopMoney": { "amount": "25.98", "currencyCode": "EUR" } }
      }
    ],
    "pageInfo": {
      "hasNextPage": false,
      "endCursor": "eyJsYXN0X2lkIjoxOTYzNTk3MjU3MTQ2MywibGFzdF92YWx1ZSI6MTk2MzU5NzI1NzE0NjN9"
    }
  }
}
```

### order_line_items (genest in `orders`)

| API-veld | Type | Nullable | Opmerkingen |
|---|---|---|---|
| `id` | String (GID) | nee | **Primaire sleutel**, vorm `gid://shopify/LineItem/<n>` |
| `name` | String | nee | Productnaam zoals op de order — **een product, geen persoon** |
| `sku` | String | ja | Kan leeg zijn (`""`) |
| `quantity` | Integer | nee | Oorspronkelijk besteld aantal |
| `currentQuantity` | Integer | nee | Na annulering/retour; `0` bij volledige retour |
| `requiresShipping` / `taxable` | Boolean | nee | |
| `vendor` | String | ja | Leverancier |
| `product.id` / `variant.id` | String (GID) | ja | **Foreign keys** naar `products` / `product_variants` |
| `originalUnitPriceSet` / `discountedTotalSet` | Object | ja | `shopMoney.amount` is een String |

Sample: zie het `lineItems.nodes[0]`-blok in de order hierboven — dat is een echt, ongewijzigd
regelrecord op alles na de geredigeerde naam, sku en leverancier.

**REST-equivalent** (voor het geval de terugvaloptie nodig is): `GET /orders.json` levert
`line_items[]` genest mee met 25 velden per regel, waaronder `id`, `admin_graphql_api_id`, `name`,
`title`, `sku`, `quantity`, `current_quantity`, `fulfillable_quantity`, `fulfillment_status`,
`price`, `price_set`, `total_discount`, `total_discount_set`, `discount_allocations`, `duties`,
`tax_lines`, `taxable`, `requires_shipping`, `grams`, `gift_card`, `product_id`, `product_exists`,
`variant_id`, `properties` en `fulfillment_service`. Namen in `snake_case`, prijzen als String.

### products

| API-veld | Type | Nullable | Opmerkingen |
|---|---|---|---|
| `id` | String (GID) | nee | **Primaire sleutel** |
| `legacyResourceId` | String (numeriek) | nee | |
| `title` | String | nee | |
| `handle` | String | nee | URL-slug, uniek binnen de winkel, **kan wijzigen** |
| `status` | String (enum) | nee | `ACTIVE`, `DRAFT`, `ARCHIVED` |
| `productType` / `vendor` | String | ja | `productType` kan `""` zijn |
| `tags` | Array&lt;String&gt; | nee | |
| `createdAt` / `updatedAt` | Timestamp (UTC) | nee | `updatedAt` is het **watermarkveld** |
| `publishedAt` | Timestamp (UTC) | ja | `null` bij `DRAFT` |
| `totalInventory` | Integer | nee | Aanwezig, maar inventory is buiten scope |
| `tracksInventory` / `hasOnlyDefaultVariant` | Boolean | nee | |
| `onlineStoreUrl` | String | ja | `null` als niet gepubliceerd; bevat het **eigen domein van de winkel** |
| `descriptionHtml` | String | ja | Kan `""` zijn; kan **groot** worden — gemeten records van meerdere kB HTML |
| `category` | Object | ja | `id`, `name` uit Shopify's taxonomie; kan `null` zijn |
| `priceRangeV2` | Object | nee | `minVariantPrice` / `maxVariantPrice`, elk `{amount, currencyCode}` |
| `variantsCount` | Object | nee | `{ count }` — betrouwbaar om afkapping van `variants` te detecteren |
| `options` | Array&lt;Object&gt; | nee | `id`, `name`, `position`, `values[]` |
| `variants` | Object → `nodes[]` + `pageInfo` | nee | **Sub-schema vereist** |

**Sample JSON:**

```json
{
  "id": "gid://shopify/Product/10541611417927",
  "legacyResourceId": "10541611417927",
  "title": "REDACTED — producttitel",
  "handle": "redacted-product-handle",
  "status": "ACTIVE",
  "productType": "REDACTED — producttype",
  "vendor": "REDACTED — leveranciersnaam",
  "tags": ["REDACTED — tag", "REDACTED — tag"],
  "createdAt": "2025-12-12T08:14:49Z",
  "updatedAt": "2026-08-02T21:15:57Z",
  "publishedAt": "2025-12-12T11:39:27Z",
  "totalInventory": 6,
  "tracksInventory": true,
  "hasOnlyDefaultVariant": true,
  "onlineStoreUrl": "REDACTED — https://<winkeldomein>/products/<handle>",
  "descriptionHtml": "REDACTED — HTML-productbeschrijving, hier 1,5 kB",
  "category": { "id": "gid://shopify/TaxonomyCategory/lb", "name": "Luggage & Bags" },
  "priceRangeV2": {
    "minVariantPrice": { "amount": "14.99", "currencyCode": "EUR" },
    "maxVariantPrice": { "amount": "14.99", "currencyCode": "EUR" }
  },
  "variantsCount": { "count": 1 },
  "options": [
    {
      "id": "gid://shopify/ProductOption/13540422648135",
      "name": "Title",
      "position": 1,
      "values": ["Default Title"]
    }
  ],
  "variants": {
    "nodes": [
      {
        "id": "gid://shopify/ProductVariant/52946458771783",
        "legacyResourceId": "52946458771783",
        "title": "Default Title",
        "sku": "REDACTED — artikelnummer",
        "barcode": "REDACTED — EAN",
        "price": "14.99",
        "compareAtPrice": null,
        "position": 1,
        "availableForSale": true,
        "inventoryQuantity": 6,
        "taxable": true,
        "createdAt": "2025-12-12T08:14:49Z",
        "updatedAt": "2026-08-02T21:15:58Z",
        "selectedOptions": [{ "name": "Title", "value": "Default Title" }],
        "inventoryItem": {
          "id": "gid://shopify/InventoryItem/54527466930503",
          "measurement": { "weight": { "unit": "KILOGRAMS", "value": 0.0 } }
        }
      }
    ],
    "pageInfo": { "hasNextPage": false, "endCursor": "eyJsYXN0X2lkIjo1Mjk0NjQ1ODc3MTc4MywibGFzdF92YWx1ZSI6MX0=" }
  }
}
```

> Let op: een product zonder varianten bestaat niet. Shopify maakt altijd één variant met
> `title = "Default Title"`; `hasOnlyDefaultVariant` geeft aan of dat het geval is. Gemeten in de
> onderzochte winkel: 765 producten tegen 948 varianten, dus de meeste producten hebben er één.

### product_variants

Als eigen entiteit opgehaald via de top-level `productVariants`-query. `id` is de primaire sleutel,
`updatedAt` het watermarkveld. Velden zijn dezelfde als in het geneste `variants`-blok hierboven,
met `product { id updatedAt }` er extra bij als je de koppeling naar het product nodig hebt.

| API-veld | Type | Nullable | Opmerkingen |
|---|---|---|---|
| `id` | String (GID) | nee | **Primaire sleutel** |
| `legacyResourceId` | String (numeriek) | nee | |
| `title` | String | nee | `"Default Title"` bij een product zonder echte varianten |
| `sku` | String | ja | **Kan `""` zijn — dus géén bruikbare sleutel** |
| `barcode` | String | ja | vaak `null` |
| `price` | **String** | nee | geen getal — cast in Silver |
| `compareAtPrice` | **String** | ja | vaak `null` |
| `position` | Integer | nee | |
| `availableForSale` / `taxable` | Boolean | nee | |
| `inventoryQuantity` | Integer | nee | Aanwezig, maar inventory is buiten scope |
| `createdAt` / `updatedAt` | Timestamp (UTC) | nee | `updatedAt` is **eigen aan de variant** |
| `selectedOptions` | Array&lt;Object&gt; | nee | `{name, value}` |
| `product` | Object | nee | `{id, updatedAt}` — **foreign key** naar `products` |
| `inventoryItem` | Object | nee | `id` + `measurement.weight {unit, value}` |

**Sample JSON** (top-level `productVariants`, echt record van 28-08-2026):

```json
{
  "id": "gid://shopify/ProductVariant/46686515462471",
  "legacyResourceId": "46686515462471",
  "title": "Default Title",
  "sku": "REDACTED — artikelnummer",
  "barcode": "REDACTED — EAN",
  "price": "16.99",
  "compareAtPrice": null,
  "position": 1,
  "availableForSale": true,
  "inventoryQuantity": 128,
  "taxable": true,
  "createdAt": "2023-05-04T13:34:03Z",
  "updatedAt": "2026-05-19T07:26:09Z",
  "selectedOptions": [{ "name": "Title", "value": "Default Title" }],
  "product": { "id": "gid://shopify/Product/8401051025735", "updatedAt": "2026-06-17T02:34:24Z" },
  "inventoryItem": {
    "id": "gid://shopify/InventoryItem/48785865146695",
    "measurement": { "weight": { "unit": "KILOGRAMS", "value": 0.0 } }
  }
}
```

Dit record laat meteen zien waarom variant en product losse watermarks kúnnen hebben: de variant is
voor het laatst gewijzigd op `2026-05-19`, het product op `2026-06-17`. Het product beweegt hier
dus **later** dan de variant — de omgekeerde richting is de risicovolle, en die is in deze winkel
niet waargenomen (zie
[product_variants — een stille valkuil in de telling](#product_variants--een-stille-valkuil-in-de-telling)).

### customers

**Deze entiteit bevat persoonsgegevens. Zie [Persoonsgegevens](#persoonsgegevens) voor wat bewust
niet is opgehaald.** De veldtabel hieronder is volledig: hij komt uit **GraphQL-introspectie** van
het `Customer`-type (39 velden), niet uit data — zo zijn ook de persoonsgegevensvelden bekend
zonder dat er ooit een waarde is opgehaald.

| API-veld | Type | Persoonsgegeven | Opgehaald |
|---|---|---|---|
| `id` | `ID!` | nee | **ja** — primaire sleutel |
| `legacyResourceId` | `UnsignedInt64!` | nee | ja |
| `createdAt` / `updatedAt` | `DateTime!` | nee | ja — `updatedAt` is het watermarkveld |
| `state` | `CustomerState!` | nee | ja — bv. `DISABLED`, `ENABLED` |
| `verifiedEmail` | `Boolean!` | nee | ja — een vlag, geen adres |
| `taxExempt` | `Boolean!` | nee | ja |
| `taxExemptions` | `[…]!` | nee | ja |
| `tags` | `[…]!` | nee | ja |
| `locale` | `String!` | nee | ja — bv. `nl-NL` |
| `numberOfOrders` | `UnsignedInt64!` | nee | ja — **als String geleverd** (`"1"`) |
| `lifetimeDuration` | `String!` | nee | ja — vrije tekst, bv. `"27 days"` |
| `canDelete` | `Boolean!` | nee | ja |
| `productSubscriberStatus` | `CustomerProductSubscriberStatus!` | nee | ja |
| `amountSpent` | `MoneyV2!` | nee | ja — `{amount, currencyCode}`, `amount` is String |
| `emailMarketingConsent` | object | nee | ja — alleen toestemmingsstatus, geen adres |
| `smsMarketingConsent` | object | nee | ja — gemeten als `null` |
| `defaultAddress` | `MailingAddress` | **deels** | alleen `id`, `countryCodeV2`, `provinceCode` |
| `addressesV2` | `MailingAddressConnection!` | **deels** | idem |
| `lastOrder` | `Order` | nee | ja — `{id, name}`; `null` bij een klant zonder orders |
| `image` | `Image!` | mogelijk | alleen `id` (gemeten `null`) |
| `firstName` | `String` | **JA** | **NEE — bewust niet opgehaald** |
| `lastName` | `String` | **JA** | **NEE** |
| `displayName` | `String!` | **JA** | **NEE** |
| `defaultEmailAddress` | `CustomerEmailAddress` | **JA** | **NEE** |
| `defaultPhoneNumber` | `CustomerPhoneNumber` | **JA** | **NEE** |
| `note` | `String` | **JA** (vrije tekst) | **NEE** |
| `multipassIdentifier` | `String` | **JA** | **NEE** |
| `metafield` / `metafields` | object | mogelijk | **NEE** |
| `orders` | `OrderConnection!` | n.v.t. | **NEE** — via `orders` zelf |
| `events`, `paymentMethods`, `storeCreditAccounts`, `subscriptionContracts`, `companyContactProfiles`, `identityProviderSubjects`, `mergeable`, `statistics`, `taxSettings`, `dataSaleOptOut` | diverse | deels | **NEE** — buiten scope |

**Sample JSON** — een **echt** record van 28-08-2026, opgehaald met een selectie die geen enkel
persoonsgegeven bevat; alleen de identificerende GID's zijn nadien geredigeerd:

```json
{
  "id": "gid://shopify/Customer/REDACTED",
  "legacyResourceId": "REDACTED — numeriek klant-id",
  "createdAt": "2026-08-01T09:27:24Z",
  "updatedAt": "2026-08-01T09:27:26Z",
  "state": "DISABLED",
  "verifiedEmail": true,
  "taxExempt": false,
  "taxExemptions": [],
  "tags": [],
  "locale": "nl-NL",
  "numberOfOrders": "1",
  "lifetimeDuration": "27 days",
  "canDelete": false,
  "productSubscriberStatus": "NEVER_SUBSCRIBED",
  "amountSpent": { "amount": "16.48", "currencyCode": "EUR" },
  "emailMarketingConsent": {
    "marketingState": "NOT_SUBSCRIBED",
    "marketingOptInLevel": "SINGLE_OPT_IN",
    "consentUpdatedAt": null
  },
  "smsMarketingConsent": null,
  "defaultAddress": {
    "id": "gid://shopify/MailingAddress/REDACTED?model_name=CustomerAddress",
    "countryCodeV2": "NL",
    "provinceCode": null
  },
  "addressesV2": {
    "nodes": [
      {
        "id": "gid://shopify/MailingAddress/REDACTED?model_name=CustomerAddress",
        "countryCodeV2": "NL",
        "provinceCode": null
      }
    ]
  },
  "lastOrder": { "id": "gid://shopify/Order/8015359377735", "name": "#24348" },
  "image": { "id": null }
}
```

> Let op de vorm van het adres-GID: `gid://shopify/MailingAddress/<n>?model_name=CustomerAddress`.
> De querystring hoort bij het id en is geen artefact — een parser die op `/` splitst, houdt hem er
> bij.

## Belangrijkste datakenmerken per entiteit

Alle volumes gemeten op **28-08-2026** met `limit` boven het verwachte totaal, dus
`precision: EXACT`, en onafhankelijk bevestigd door de REST-`count`-endpoints.

### orders

- **Natuurlijke primaire sleutel:** `id` (GID); alternatief `legacyResourceId` (numeriek).
  `name` (`#24364`) is **niet** gegarandeerd uniek over de tijd en ongeschikt als sleutel.
- **Last-modified veld:** `updatedAt` (UTC, secondeprecisie).
- **Ondersteunt de API incrementeel ophalen?** **Ja** — `query: "updated_at:>='<start>'"` met
  `sortKey: UPDATED_AT`. Gemeten inclusief en exact op de seconde.
- **Geeft de API updates op bestaande records?** **Ja.** Een order wordt bij betaling, fulfilment,
  annulering en retour opnieuw aangeraakt; `updatedAt` schuift dan mee. Gemeten voorbeeld:
  aangemaakt `2026-08-02T08:17:13Z`, laatst gewijzigd `2026-08-03T04:03:50Z` — bijna 20 uur later.
- **Volledige periode nodig voor verwijderdetectie?** **Ja**, tenzij `events` wordt ingezet. Orders
  worden zelden hard verwijderd (meestal geannuleerd — zichtbaar via `cancelledAt`), dus de behoefte
  is beperkt.
- **Datavolume:** **23.770** orders totaal. Per aanmaakjaar: 2023 (vanaf juni) **3.281**,
  2024 **6.849**, 2025 **9.131**, 2026 t/m 28 augustus **4.509**. Gewijzigd in de laatste 7 dagen:
  **116** → ongeveer **17 orders per dag**. Oudste order `#1001` (`2023-06-08T12:09:52Z`).
- **Partitiekandidaat:** `createdAt` op jaar of maand.

### order_line_items

- **Natuurlijke primaire sleutel:** `id` (GID van de LineItem).
- **Last-modified veld:** **geen eigen veld** — een orderregel erft de `updatedAt` van de order.
- **Incrementeel:** alleen via de bovenliggende order.
- **Datavolume:** **schatting circa 56.000** regels (23.770 orders × 2,38 gemiddeld, gemeten over de
  100 recentst gewijzigde orders). Dit is een **schatting, geen telling** — er bestaat geen
  count-endpoint voor orderregels en geen top-level query om er een te bouwen.
- **Partitiekandidaat:** `createdAt` van de bovenliggende order.

### products

- **Natuurlijke primaire sleutel:** `id` (GID). `handle` is uniek binnen de winkel maar **kan
  wijzigen**; `sku` staat op de variant, niet op het product.
- **Last-modified veld:** `updatedAt`.
- **Incrementeel:** **ja**, zelfde patroon als orders.
- **Geeft de API updates?** **Ja** — gemeten product aangemaakt `2025-12-12`, laatst gewijzigd
  `2026-08-02`. In de laatste 7 dagen wijzigden **316** van de 765 producten (41%), wat wijst op een
  proces dat producten en masse aanraakt (prijs- of voorraadsynchronisatie).
- **Volledige periode nodig voor verwijderdetectie?** **Ja.** Met 765 records is een volledige
  herlading goedkoop (4 pagina's) — eenvoudiger dan de `events`-route.
- **Datavolume:** **765** producten.
- **Partitiekandidaat:** geen — te klein om te partitioneren.

### product_variants

- **Natuurlijke primaire sleutel:** `id` (GID). **Niet `sku`** — die kan `""` zijn.
- **Last-modified veld:** `updatedAt`, **eigen aan de variant**, los van het product.
- **Incrementeel:** **ja**, via de top-level `productVariants`-query. Gemeten: 53 varianten
  gewijzigd in één dag.
- **Verificatie van de delta:** **niet met `productVariantsCount`** — dat veld negeert het filter.
- **Datavolume:** **948** varianten (v1.0 had dit als UNKNOWN staan met een schatting van 800–1.500;
  nu exact gemeten).
- **Partitiekandidaat:** geen.

### customers

- **Natuurlijke primaire sleutel:** `id` (GID).
- **Last-modified veld:** `updatedAt`.
- **Incrementeel:** **ja**, zelfde patroon. Gewijzigd in de laatste 7 dagen: **153**.
- **Geeft de API updates?** **Ja** — gemeten record aangemaakt om `09:27:24` en 2 seconden later
  gewijzigd; het `emailMarketingConsent`-blok is de gebruikelijke aanleiding.
- **Volledige periode nodig voor verwijderdetectie?** **Ja** — en hier is dat duur: 983 pagina's.
  Voor deze entiteit is de `events`-route (`verb:destroy`, `subjectType`) de aantrekkelijkste
  optie. Klantverwijdering is bovendien een AVG-relevante gebeurtenis: een in de bron gewiste klant
  moet ook stroomafwaarts verdwijnen.
- **Datavolume:** **245.503** klanten. Per aanmaakjaar: 2023 **3.630**, 2024 **7.536**,
  2025 **230.094**, 2026 t/m 28 augustus **4.243**.
  > **Opvallend en belangrijk voor de planning:** 2025 kent een instroom van 230.094 klanten —
  > **94% van het totale bestand in één jaar**, tegen enkele duizenden in de jaren ervoor en erna.
  > Dat patroon past niet bij organische groei en wijst op een **eenmalige bulkimport**. In de
  > `events`-feed is een integratie-app van derden zichtbaar die records aanmaakt en verwijdert, wat
  > die richting op wijst. Dit is **niet bevestigd** en verdient bevestiging bij de eigenaar van de
  > winkel vóór de historische load: het bepaalt of die 230.094 records daadwerkelijk gewenste
  > klantdata zijn.
- **Partitiekandidaat:** `createdAt` op jaar geeft met deze verdeling een sterk scheve partitie
  (één partitie met 94% van de data). `updatedAt` op maand is waarschijnlijk beter.

## Validatie tegen de general-notebooks

Deze sectie toetst de gemeten bron tegen wat de generieke ingestienotebook aankan. **Het rapport
schrijft geen config voor** — het stelt alleen vast of er een gat zit tussen bron en framework.

| Wat de bron vraagt | Wat het framework heeft | Oordeel |
|---|---|---|
| POST met een GraphQL-body | `Details.StrategyDetails.Method = "POST"` met `json_body` | **past** |
| genest antwoordpad (`data.orders.nodes`) | `Output.RecordKey`, `Pagination.MarkerResponseKey` en `MoreDataKey` accepteren een dotted path | **past** |
| cursor + filter op élke pagina | `GraphQL.CursorVar` en `GraphQL.FilterVar`/`FilterTemplate` gaan samen in `variables` | **past** |
| cursor mag niet over runs heen bewaard worden | `Pagination.CursorResetPerRun` | **past** |
| watermark uit een datakolom (`updatedAt`) | `WatermarkDetails.Source = "data_column"` | **past** |
| `THROTTLED` binnen een HTTP 200 | eigen tak in `_request()` die `errors[].extensions.code` leest en wacht op basis van `extensions.cost` | **past — en is met deze meting bevestigd** |
| `MAX_COST_EXCEEDED` | eigen logregel; geen retry, want de kosten zijn een eigenschap van de query | **past** |
| eigen auth-header in plaats van `Authorization` | `AuthDetails.AuthHeaderName` — de credential gaat als **kale waarde** in die header | **past** |

**Geen gaten gevonden; geen user story nodig.** Wel drie kanttekeningen die het rapport moet
achterlaten:

1. **Dit is nog steeds ongevalideerde code.** De GraphQL-extractor is geschreven en compileert,
   maar heeft nog nooit tegen een echte GraphQL-bron gedraaid en staat in geen enkele Fabric-
   workspace. Dit rapport bewijst dat de **bron** zich gedraagt zoals de code aanneemt; het bewijst
   niet dat de code werkt. Dat blijft aan een end-to-end test.
2. **De veldnamen die de statusbeschrijving als onbevestigd markeerde, zijn nu bevestigd** — met
   één documentatiecorrectie op het pad van de foutcode. Zie
   [De vier aannames van het framework](#de-vier-aannames-van-het-framework-afgevinkt-tegen-deze-meting).
3. **De REST-terugvaloptie past maar gedeeltelijk op het framework.** `Details.ExtraParams` wordt
   aan élke pagina toegevoegd, en Shopify's REST verbiedt filterparameters zodra er een cursor in
   het spel is. Een REST-config werkt dus alleen voor delta's die in één pagina van 250 passen. Dat
   is een eigenschap van bron én framework samen, niet van één van beide.

### Wat er sinds v1.0 aan het framework is veranderd

v1.0 beschreef een omweg die inmiddels niet meer nodig is, en die informatie zou anders in een
config terechtkomen die niemand meer wil.

**Vervallen bevinding uit v1.0.** Toen bouwde `_get_headers()` **altijd** een `Authorization`-header
op, waardoor Shopify alleen bereikbaar was door het token een tweede keer mee te sturen via
`ApiHeaders` + per-entiteit `Details.ExtraHeaders`. Gevolg: dezelfde secretnaam tweemaal in de
config, en HTTP 401 voor elke entiteit die `ExtraHeaders` vergat.

**Wat er nu staat.** Er is een optioneel veld `AuthDetails.AuthHeaderName` bijgekomen. Staat het er
niet, dan is het gedrag als voorheen (`Authorization` met `AuthScheme` als prefix). Staat het er
wel, dan gaat het credential als kale waarde in die header. De configtemplate noemt Shopify
inmiddels expliciet als het voorbeeld hiervoor.

**Gevolg voor wie dit rapport leest:** gebruik `AuthDetails.AuthHeaderName`. De
dubbele-secret-omweg uit v1.0 is **niet langer het advies**; hij werkt technisch nog (Shopify
negeert de overbodige `Authorization`-header — opnieuw gemeten op 28-08-2026), maar er is geen reden
meer voor.

## Persoonsgegevens

`customers` bevat persoonsgegevens, en `orders` bevat ze indirect (klantkoppeling, verzendadres,
contact-e-mailadres).

**Aanpak in dit onderzoek: uitgesloten bij het ophalen, niet achteraf geredigeerd.** Dat is een
bewuste keuze: dit rapport landt in twee git-repositories, en in git blijft een eerdere versie
terugvindbaar. Wat nooit is opgehaald, kan ook nooit teruggehaald worden.

GraphQL maakt dit eenvoudiger dan REST, en dat is een van de sterkste argumenten voor GraphQL bij
deze bron. Bij REST bepaalt de server wat je krijgt — `GET /customers.json` levert ongevraagd
`first_name`, `last_name`, `email`, `phone` en volledige adressen. Bij GraphQL bepaalt **de query**
wat er terugkomt: door die velden niet te selecteren komen ze nooit over de lijn. Dat is het
equivalent van een `excludeContactInfo`-schakelaar aan de API-kant, en dan sterker: het werkt per
veld in plaats van per aanroep.

**Concreet niet opgehaald bij `customers`:** `firstName`, `lastName`, `displayName`,
`defaultEmailAddress`, `defaultPhoneNumber`, `note`, `multipassIdentifier`, `metafields`, en van
adressen alleen `id` + `countryCodeV2` + `provinceCode` — dus geen straat, huisnummer, postcode,
plaats of naam.

**Concreet niet opgehaald bij `orders`:** alle klantvelden behalve `customer.id`; van
`shippingAddress` alleen land en provincie; geen `email`, `phone`, `note`, `billingAddress` of
`customerJourney`.

De veldtabel voor `customers` in dit rapport is daarom opgebouwd uit **GraphQL-introspectie** —
veldnamen en types uit het schema, zonder ooit een waarde op te halen. Zo weet de config-builder
precies welke velden bestaan en welke bewust zijn overgeslagen.

**Aanbeveling voor de bouwfase:** de vraag *welke* klantvelden naar Bronze mogen, is een functionele
en AVG-beslissing, geen technische. Leg die expliciet voor voordat de query in sectie 06 wordt
vastgelegd. Het bronmodel dwingt niets af — de query bepaalt alles, en die keuze is achteraf lastig
terug te draaien zodra de data in Bronze staat.

**Credentialhygiëne in dit onderzoek:** de tokenwaarde is server-side uit de Key Vault gelezen,
nooit afgedrukt, nooit gelogd, en staat in geen enkel voorbeeldcommando in dit rapport. De
secretnaam en de Key Vault-URL horen in de klantconfig en staan daarom **niet** in dit rapport.

## Wat er ten opzichte van v1.0 is veranderd

v1.0 (21-08-2026) is integraal opnieuw nagelopen. De onderstaande tabel is de volledige
verschillenlijst; alles wat er niet in staat, is ongewijzigd bevestigd.

### Correcties — v1.1 gaat voor

| Onderwerp | v1.0 zei | v1.1 meet | Gevolg |
|---|---|---|---|
| Exacte tellingen via GraphQL | GraphQL `*Count` geeft `AT_LEAST`; gebruik de REST-`count`-endpoints | met `limit` boven het totaal geeft GraphQL **`EXACT`**, en dezelfde getallen als REST | REST is voor tellen **niet meer nodig** |
| Pad van de throttle-foutcode | *(impliciet als `extensions.code` overgenomen uit de statusbeschrijving)* | de code staat in **`errors[].extensions.code`**; er is géén `code` in het top-level `extensions` | documentatiecorrectie; de notebookcode was al goed |
| Auth-omweg | secretnaam tweemaal in de config via `ApiHeaders` + `ExtraHeaders`, anders 401 | het framework heeft nu `AuthDetails.AuthHeaderName` | de omweg is **vervallen** |
| Aantal orderregels per order | gemiddeld 2,1 | gemiddeld **2,38** (min 1, max 13, 0 afgekapt) | schatting orderregels bijgesteld naar ~56.000 |
| `Retry-After`-headernaam | `Retry-After` | op de lijn **`retry-after`** (kleine letters, HTTP/2) | alleen relevant voor hoofdlettergevoelige lookups |

### Nieuwe bevindingen in v1.1

| Onderwerp | Bevinding |
|---|---|
| `productVariantsCount` negeert `query` | Geeft altijd het totaal met `precision: EXACT`, ook bij een filter op een datum in de toekomst. Enige signaal: een `invalid_field`-waarschuwing in `extensions.search`. **Nooit gebruiken om een delta te verifiëren.** |
| Belasting van de kostenemmer | De emmer wordt belast met `actualQueryCost`, niet met `requestedQueryCost`; de geschatte waarde bepaalt alleen de toelating |
| REST-terugvaloptie preciezer afgebakend | Zonder `Link`-header is er geen cursor, dus mag het filter mee: een delta die in één pagina van 250 past, kán via REST. Gemeten met 116 records in één call |
| REST-orderregels | `GET /orders.json` levert `line_items[]` genest mee met 25 velden — de terugvaloptie voor orderregels is even goed als de GraphQL-route |
| Variant- versus productwatermark | Over de 250 varianten die in een venster van 7 dagen wijzigden, had **geen enkele** een product waarvan de `updatedAt` buiten dat venster viel |
| Exact aantal varianten | **948** (v1.0 had dit als UNKNOWN met schatting 800–1.500) |

### Bevestigd zonder wijziging

API-versie `2026-07` en het versiegedrag; de auth-headermatrix; 17 lees-scopes inclusief
`read_all_orders`; de oudste order `#1001` uit juni 2023; `first`/`limit` maximum 250; cursor +
filter samen in GraphQL; de REST-cursor/filterbotsing met identieke foutboodschap; het verplichte
aanhalingsteken in het datumfilter en de kapotte parse zonder; UTC in GraphQL versus lokale offset
in REST; `tags` als array versus komma-string; de deprecation-headers op Products en Variants en de
afwezigheid van `Sunset`; emmer 4000 / herstel 200 per seconde; per-query maximum 1000;
REST-emmer 80 / 4 requests per seconde; `Retry-After` als `"4.0"` en de afwezigheid van de
call-limit-header op een 429; de afwezigheid van een top-level `lineItems`-query; het bestaan van de
`events`-feed met `subjectId`/`subjectType`.

### Gemeten volumeverschil (7 dagen groei)

| Entiteit | 21-08-2026 | 28-08-2026 |
|---|---|---|
| orders | 23.670 | **23.770** |
| products | 762 | **765** |
| product_variants | *(niet gemeten)* | **948** |
| customers | 245.409 | **245.503** |

## Openstaande vragen / UNKNOWNs

| # | Vraag | Status |
|---|---|---|
| 1 | Is de klantinstroom van 230.094 records in 2025 een bulkimport, en hoort die data in het datawarehouse? | **UNKNOWN — bevestiging bij de eigenaar van de winkel nodig.** De `events`-feed toont een integratie-app van derden die records aanmaakt en verwijdert; het verband is niet bevestigd. Bepalend voor de omvang van de historische load. |
| 2 | Komen variantwijzigingen voor zónder dat `products.updatedAt` meebeweegt? | **GEDEELTELIJK BEANTWOORD, niet sluitend.** Over 250 varianten in een venster van 7 dagen: 0 gevallen. Dat is één winkel en één venster — geen algemene garantie. Wie het risico niet wil lopen, geeft `product_variants` een eigen watermark; dat kan, want de top-level query filtert correct. |
| 3 | Concrete sunset-datum voor de REST-endpoints van Products/Variants | **UNKNOWN.** Geen `Sunset`-header waargenomen en geen datum in de geraadpleegde documentatie. Een externe bron meldde dat `products/count.json` in `2025-10` verwijderd zou zijn; **dat is weerlegd** (HTTP 200 op 28-08-2026). Beschouw externe datums als onbevestigd. |
| 4 | Verwijderdetectie via `events` end-to-end | **Technisch haalbaar, niet uitgewerkt.** `subjectId` en `subjectType` zijn gemeten op `BasicEvent`. **Niet gemeten:** de bewaartermijn van de feed, de dekking per entiteitstype, het pagineringsgedrag van `events` en of `verb:destroy` alle verwijderroutes vangt. |
| 5 | Gedrag van Shopify's Bulk Operations API | **Niet onderzocht.** `bulkOperation` bestaat op de `QueryRoot` en Shopify beveelt het aan voor grote exports; Shopify's eigen foutboodschappen bij `first > 250` en bij `MAX_COST_EXCEEDED` wijzen er allebei naar. Het framework ondersteunt dit patroon vandaag niet. Voor 983 pagina's klanten is de normale route toereikend, maar dit is de aangewezen route als dat ooit knelt. |
| 6 | Rate limits op andere Shopify-plannen | **ONBEVESTIGD.** Alleen `Advanced` is gemeten (4000 punten / 200 per seconde, REST 80 / 4 per seconde). De verhouding tot Standard, Plus en Enterprise komt uit documentatie, niet uit waarneming, en is niet te meten zonder een winkel op dat plan. |
| 7 | Gedrag bij een planwijziging tijdens productie | **Niet te meten.** Bij afschaling halveren de limieten en loopt een op 200/s afgestemde config vast. Dit volgt uit de plan-gebondenheid, niet uit een waarneming. |
| 8 | Bestaat er een niet-productiewinkel om tegen te testen? | **UNKNOWN.** Alle metingen zijn tegen productie gedaan, uitsluitend lezend. Er is één token gemeten en dat wijst naar een productiewinkel. |
| 9 | Waarom raakt iets 41% van de producten in 7 dagen aan? | **UNKNOWN — niet onderzocht.** 316 van de 765 producten wijzigden in een week. Waarschijnlijk een prijs- of voorraadsynchronisatie. Relevant omdat het bepaalt hoe groot een dagelijkse productdelta werkelijk is. |
| 10 | Andere `*Count`-velden met hetzelfde filterprobleem als `productVariantsCount` | **UNKNOWN.** Getoetst en in orde: `ordersCount`, `productsCount`, `customersCount`. De overige count-velden op de `QueryRoot` zijn **niet** getoetst. Controleer bij elk nieuw count-veld eerst `extensions.search` op een `invalid_field`-waarschuwing. |
