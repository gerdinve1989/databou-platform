# Social Deal API Research

## TypeSource
- Confirmed: `UNKNOWN — needs confirmation` (geen API aangetroffen om te confirmeren; zie Overview)
- Orchestrator inferred: niet van toepassing — deze bron is nog niet gerouteerd met een vermoede TypeSource; de opdracht was puur de vraag of een API bestaat.

## Overview

Social Deal is een actie-/dealplatform (Benelux + omliggende landen) waarop consumenten
vouchers kopen voor horeca, wellness, uitjes en overnachtingen tegen een afgeprijsde waarde.
Een aanbieder (de ondernemer die de deal levert) krijgt toegang tot een **Social Deal
Partner Portal** (web) en een **Social Deal Partner-app** (iOS/Android), waarin volgens
publieke bronnen statistieken staan over verkochte vouchers, omzet en reviews, en waarin
vouchers gescand kunnen worden bij inwisseling.

**Kernvraag van dit onderzoek: biedt Social Deal een publieke, partner- of reseller-API aan
waarmee per verkochte deal/voucher de betaalde prijs is op te vragen?**

**Bevinding: nee — niet aantoonbaar.** Op geen van de onderzochte plekken is een
gedocumenteerde, publiek toegankelijke API gevonden waarmee een derde partij (zoals een
afnemer) kan authenticeren en per verkochte voucher de betaalde prijs, deal, datum en
voucher-/klantreferentie kan uitlezen. Wat wél is aangetroffen:

- Een **Partner Portal** en **Partner-app** — beide zijn mens-gerichte UI's (login met
  gebruikersnaam/wachtwoord), geen API. Of deze een CSV-/bulk-export van transacties bieden
  is niet vast te stellen zonder een testaccount; publieke documentatie hierover ontbreekt.
- Integraties tussen Social Deal en **reserveringssystemen van derden** (Zenchef, Nostium,
  Booking Experts, GoTable e.d.). Deze integraties lopen in de richting
  Social Deal → reserveringssysteem: Social Deal roept de API van het reserveringssysteem
  aan om beschikbaarheid op te vragen en reserveringen te plaatsen/bijwerken. Dit is geen
  kanaal waarmee een aanbieder of een extern systeem bij Social Deal zélf transactie-
  of omzetdata kan opvragen.
- Een GitHub-organisatie `socialdeal` (geverifieerd domeinbezit van `socialdeal.nl`) met
  drie repositories: `.github` (profiel), een fork van `Valinor` (PHP-mapping-library) en
  een fork van `i18n` (Nuxt-vertaalmodule). Geen van deze repositories is een publieke
  API-SDK of API-specificatie.
- Een aggregator (`apitracker.io`) vermeldt een "Social Deal API"-profiel, maar elk veld
  daarin (API-stijl, authenticatie, OpenAPI-spec, endpoints, rate limits) staat op `-`
  (geen gegevens). Deze pagina is een lege sjabloonpagina van de aggregator zelf en bevat
  geen verifieerbare informatie — niet gebruikt als bron voor dit rapport.
- Diverse koppelbureaus (bijv. Brixxs) bieden aan een **maatwerk**-koppeling met Social Deal
  te bouwen "indien het systeem REST ondersteunt", wat er juist op wijst dat er geen
  standaard, gedocumenteerde partner-API bestaat — anders zou een maatwerktraject niet nodig
  zijn.

Er is geen bewijs gevonden van een publieke developer-portal, API-referentie, OpenAPI/Swagger-
specificatie, sandbox-omgeving of partner-API-documentatie bij `socialdeal.nl`, `socialdeal.be`
of een onderliggende developer-/api-subdomein.

## Auth
- Pattern (A / B / C from 01_source_config.template.md): `n.v.t.` — geen API gevonden om een
  authenticatiepatroon aan toe te kennen.
- AuthScheme / Method: `UNKNOWN — needs confirmation`
- Secret name(s) in KeyVault: `n.v.t.`
- Token endpoint (if OAuth2): `n.v.t.`

## Connection
- BaseUrl: `UNKNOWN — needs confirmation`
- RateLimitDelay (recommended): `n.v.t.`
- ApiHeaders (if any): `n.v.t.`

## Entity Inventory
| Entity | Endpoint path | In scope | Parent entity | Notes |
|---|---|---|---|---|
| (geen) | — | — | — | Geen endpoints aantoonbaar; niets om te inventariseren |

## Pagination & Ingestion per Entity
Niet van toepassing — er is geen endpoint gevonden om te bevragen.

## Rate Limits
Niet van toepassing.

## Response Shape per Entity
Niet van toepassing — geen enkele aanroep kon worden gedaan; er is geen URL, geen
authenticatieschema en geen testomgeving bekend.

## General-Notebooks Extensions Needed
Niet van toepassing — er is geen API-patroon om tegen de generieke notebooks te toetsen.

## Open Questions / UNKNOWNs

1. **Bestaat er een niet-publieke partner-/reseller-API?** Veel actieplatforms houden een
   partner-API achter een accountmanager of een NDA, zonder publieke documentatie. Dit is
   niet uit te sluiten op basis van alleen openbare bronnen. **Aanbevolen vervolgstap:** de
   klant vraagt zijn Social Deal-accountmanager rechtstreeks naar (a) het bestaan van een
   partner-/reporting-API, en (b) of de Partner Portal een bulk- of CSV-export biedt van
   verkochte vouchers met betaalde prijs, dealnaam, verkoopdatum en voucher-/
   ordernummer. Dat antwoord verandert de vorm van dit onderzoek fundamenteel (van "geen
   bron" naar "nieuwe te onderzoeken API/bestandsbron") en hoort daarom niet in een aanname
   te worden opgelost.
2. **Biedt de Partner Portal/Partner-app een export-/downloadfunctie?** Publieke bronnen
   noemen alleen "statistieken en rapportages" in de UI; een exportknop (CSV/Excel) is noch
   bevestigd noch uitgesloten. Dit is alleen vast te stellen met een echt partneraccount
   (buiten de scope van publiek onderzoek).
3. **Is er een affiliate-/dealfeed-API** (zoals sommige actieplatforms aanbieden aan
   prijsvergelijkers) die wél per deal prijsinformatie teruggeeft, maar dan de
   *verkoopprijs van de deal* in het algemeen — niet per individuele transactie van de
   klant van de aanbieder? Niet aangetroffen in dit onderzoek; zou sowieso niet de betaalde
   prijs per specifieke voucher opleveren.
4. **Zijn de integraties met Zenchef/Nostium/Booking Experts/GoTable ooit bevraagbaar
   vanuit de andere richting** (dus: kan een aanbieder via zijn eigen reserveringssysteem bij
   Social Deal informatie ophalen in plaats van andersom)? Op basis van de beschikbare
   documentatie (Zenchef-helpcentrum, Nostium-integratiepagina) lopen deze koppelingen
   richting het reserveringssysteem (beschikbaarheid doorgeven, reservering plaatsen), niet
   richting het uitlezen van transactie- of omzetdata. Bevestiging vereist navraag bij de
   leverancier van het eigen reserveringssysteem, indien van toepassing.

**Conclusie voor dit moment:** op basis van publiek onderzoek biedt Social Deal **geen
aantoonbare, programmatisch bevraagbare API** waarmee het platform zelfstandig per voucher de
betaalde prijs kan ophalen. Zolang punt 1 hierboven niet is uitgevraagd bij Social Deal zelf,
kan dit researchrapport niet worden omgezet in een connectorconfig (secties 1–2): er is geen
adres, geen authenticatieschema en geen endpoint om op te bouwen.
