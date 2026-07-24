# Visionplanner API Research

> Researched 2026-07-23. **Desk research only** — no tenant/credentials were available, so
> nothing below was exercised against a live Visionplanner administration. The strongest
> primary source is Visionplanner's own published API-portal landing text (server-rendered
> from the Stoplight docs site and quoted verbatim here). The concrete OpenAPI reference
> (endpoints, scopes, payloads) is served **client-side only** by a Stoplight SPA and the
> public data routes are locked down (see *Access barrier* below), so the entity-level
> detail is **largely UNVERIFIED** and flagged as such. Per the DoD: a short honest report,
> not invented endpoints.
>
> **Headline for the framework:** Visionplanner *does* publish a public REST API, but its
> confirmed surface is **Authentication + Digital Signing + Webhooks around dossiers and
> reports** — an *outbound/event* API for advisers and signing portals. It is **not**
> advertised as a ledger/annual-accounts *extraction* API. In fact Visionplanner is
> primarily a **consumer** of grootboek/begroting data (it imports from e-Boekhouden,
> SnelStart, Exact, or Excel). Whether the three target entities (jaarrekening / grootboek /
> budget-prognose) are reachable as *read* endpoints on the public API is **unconfirmed and
> looks doubtful** on current evidence.

## TypeSource
- Inferred: **`api`** (REST/JSON). Visionplanner states the public APIs are REST and follow
  the JSON:API spec (`https://jsonapi.org/`) — source: portal landing text at
  https://visionplanner.stoplight.io/ ("The Visionplanner Public API's are based on the
  JSON Open API specification … Visionplanner is providing public REST API's").
- **Not** `soap` / `logicapps` / `sql`.
- Auth pattern (section-1 contract): **Pattern B/C-like OAuth2 bearer** (`AuthScheme:"bearer"`,
  `Method:"oauth2"`) — but the exact grant type is **UNVERIFIED** (see Auth).

## Overview

Visionplanner (visionplanner.com) is a Dutch financial-reporting / consolidation / annual-
accounts (jaarrekening) SaaS used by accountancy firms ("Advisers") for their clients. The
domain model is **Adviser → Adviser-Clients → dossiers → reports** (confirmed from the
portal text below).

**Public API portal:** https://visionplanner.stoplight.io/ — a Stoplight-hosted docs site.
The API project lives at
https://visionplanner.stoplight.io/docs/visionplanner-public-api-s .
Workspace slug `visionplanner` (Stoplight workspace id 203866; multi-tenant Stoplight
instance). Verified reachable 2026-07-23.

Verbatim from the portal landing page (VP's own words — primary source,
https://visionplanner.stoplight.io/):

> "Visionplanner is providing public REST API's to promote innovation, collaboration, and
> integration … The Visionplanner Public API's are based on the JSON Open API specification,
> for more details, see: https://jsonapi.org/. … Security is key … Each API call requires an
> access token to validate the authentication and the authorizations of the calling users.
> The access token can only be obtained by a login on a user account. The access token is
> always related to a known user within the Visionplanner platform … Authorizations can be
> linked to the Adviser, Adviser-Clients, the role assignments and the dossier specific role
> assignments. Access tokens do expire, therefore token renewal is supported as well. The
> Visionplanner platform contains a hybrid identity management platform (VPAuth) which is
> used to issue the access tokens…"

The portal groups the public API into **three families** (primary source, same page):
1. **Authentication API's** — issue/renew access tokens via **VPAuth**.
2. **Digital Signing API's** — notify a registered signing portal when reports are ready,
   exchange signing status, and receive signed reports back into the dossier.
3. **Webhook API's** — event-notification model; the Adviser admin registers a callback URL
   when a third-party app is registered into the Adviser tenant.

### Access barrier (why entity detail is unverified)
The Stoplight docs render the OpenAPI reference **client-side** (React/Overmind SPA); the
server-rendered HTML contains only the workspace landing text, no operations. The only
public data route that responds is
`GET /api/v1/projects/visionplanner/visionplanner-public-api-s/nodes/{uri}`, which requires
the exact git node path of a file; every other route (`/table-of-contents`, `/tree`,
`/search`, project metadata) returns 404 / "route does not exist". Without the table-of-
contents the individual node URIs (the OpenAPI file, the operation slugs) could not be
enumerated, and a curated brute-force of plausible finance-domain filenames
(`authentication.yaml`, `signing.yaml`, `webhook.yaml`, `ledger.yaml`, `dossier.yaml`, …)
returned no hits. Wayback Machine has only the root archived. **To finish this research a
human must open https://visionplanner.stoplight.io/docs/visionplanner-public-api-s in a
browser (JS enabled) and read the reference, or Visionplanner partner onboarding must supply
the OpenAPI file.**

## Auth
- Model: **OAuth2-style bearer token issued by VPAuth** (VP's "hybrid identity management
  platform"). Every call carries a per-user access token; tokens **expire** and **renewal is
  supported**. Authorization is scoped to Adviser / Adviser-Client / role / dossier-role.
  — primary source: https://visionplanner.stoplight.io/ (quoted above).
- **UNVERIFIED — assumption**: the exact grant type. "The access token can only be obtained
  by a login on a user account" reads like **Authorization Code (with a user login)** rather
  than pure `client_credentials`; "token renewal is supported" implies a **refresh_token**.
  If confirmed, the framework mapping is **Pattern C (OAuth2 refresh_token)** with
  `AuthScheme:"bearer"`, `Method:"oauth2"`, `GrantType:"refresh_token"`. This is an
  inference, not documented fact.
- **UNVERIFIED**: authorize endpoint URL, token endpoint URL, scope names, token TTL,
  redirect model. None were retrievable (SPA barrier). Do **not** hardcode these — get them
  from the VPAuth section of the reference or from partner onboarding.
- **UNVERIFIED**: whether a non-interactive machine credential exists. Because tokens are
  "related to a known user", a headless framework ingestion may need a **service/technical
  user** per Adviser tenant, or a `client_credentials` variant that the docs may or may not
  expose. This is a **material open question** for unattended nightly ingestion.
- Registration/onboarding: a third-party integration is **registered into the Adviser's
  tenant by the Adviser admin** (primary source, portal text). So credentials are
  provisioned **per Adviser**, not globally — relevant to multi-tenant secret layout.
- Non-OAuth alternative: **none documented**. No static-API-key path was found; the portal is
  explicit that every call needs a VPAuth access token.

## Connection
- BaseUrl: **UNVERIFIED / not found.** `api.visionplanner.com`, `app.visionplanner.com`,
  `*.visionplannercloud.com`, `auth/vpauth/login/identity.visionplanner.com` all return
  **NXDOMAIN** (checked 2026-07-23), so the API is **not** at the obvious host. Only
  `hs.visionplanner.com` / `support.visionplanner.com` resolve (marketing/support). The real
  API + VPAuth base URLs live in the OpenAPI `servers` block, which could not be read. Must
  be obtained from the reference / onboarding.
- KeyVaultUrl: n/a (per-client Fabric config).
- RateLimitDelay: **UNVERIFIED** — no published limit found; pick a conservative default
  (e.g. ≥0.5 s) until a real limit is confirmed.
- ApiHeaders: JSON:API typically wants `Accept: application/vnd.api+json` — **UNVERIFIED** for
  Visionplanner specifically; confirm from the reference.

## Entity Inventory

**Confirmed API families** (primary source — portal, https://visionplanner.stoplight.io/):

| Family | Purpose | Read/extract source? | Framework relevance |
|---|---|---|---|
| Authentication (VPAuth) | issue/renew access tokens | no (auth plumbing) | required for every call |
| Digital Signing | report-ready events, signing status, signed-report exchange | partial (report metadata/status) | event-driven, not a bulk table |
| Webhooks | register callback URL, receive event notifications | push, not pull | not a batch-ingest entity |

**Target entities — mapping to concrete endpoints:**

| Target entity | Concrete endpoint | Status |
|---|---|---|
| **jaarrekening** (annual accounts) | — | **NOT FOUND in the reachable docs.** The dossier/report + Digital-Signing surface *touches* jaarrekening as a **report/document** (VP notifies when a jaarrekening report is ready to sign — primary source, Digital Signing text), so *report-level metadata / the signed PDF* is plausibly reachable, but a structured "annual-accounts figures" endpoint is **UNVERIFIED**. Note VP's own KB creates a "dossier jaarrekening" internally (https://hs.visionplanner.com/nl/dossier-jaarrekening-aanmaken), confirming the concept exists in the data model. |
| **grootboek** (general ledger) | — | **NOT FOUND, and likely not a public read endpoint.** Grootboek data flows *into* Visionplanner from the bookkeeping system (VP maps grootboekrekeningen onto its reporting structure — https://hs.visionplanner.com/nl/grootboekrekeningen-koppelen-aan-de-rapportage-structuur; import connectors e.g. e-Boekhouden https://support.visionplanner.com/e-boekhouden.nl , SnelStart https://www.snelstart.nl/koppelingen/visionplanner). The general ledger *originates upstream*; extracting grootboek from VP's public API is **UNVERIFIED and architecturally questionable** — the upstream accounting system is usually the better source. |
| **budget / prognose** (budget/forecast) | — | **NOT FOUND.** Same pattern: budgets are **imported into** VP (https://support.visionplanner.com/import-begroting , https://hs.visionplanner.com/nl/begroting-importeren , incl. an Excel template https://support.visionplanner.com/downloaden-en-invullen-excel-sjabloon-financi%C3%ABle-gegevens). VP *produces* forecasts/consolidations as reports. A public *read* endpoint for budget/forecast figures is **UNVERIFIED**. |

Other likely entities (all **UNVERIFIED — assumptions** from the domain model, no endpoint
confirmed): `adviser`, `adviser_client` (administratie/klant), `dossier`, `report`,
`signing_request` / `signing_status`, `webhook_subscription`, `user`/`role_assignment`.

> **Sample payload shape:** none can be given without fabrication — no operation JSON was
> retrievable. JSON:API responses would be shaped `{"data":[{"type","id","attributes",
> "relationships"}], "links":{...}, "meta":{...}}` per the spec VP cites, but the concrete
> Visionplanner attributes are **UNVERIFIED**.

## Pagination & Ingestion
- **UNVERIFIED.** VP cites JSON:API (https://jsonapi.org/), whose **standard pagination** is
  `page[number]`/`page[size]` or `page[offset]`/`page[limit]` with `links.next`/`links.prev`
  cursors in the response. If VP follows the spec (it says "where applicable"), expect
  **page-based pagination with `links.next`** → framework `marker` strategy with
  `MarkerResponseKey="links.next"`. This is an **inference from the cited standard**, not
  confirmed against Visionplanner.
- Incremental / changed-since: **UNVERIFIED.** No delta/`filter[updatedSince]` parameter was
  confirmable. The **Webhook API is the intended change-feed** (event-driven), which suggests
  VP expects consumers to react to events rather than poll a `?since=` endpoint — a
  meaningful signal for incremental design (see Framework fit).

## Rate Limits
- **UNVERIFIED / not published in the reachable material.** No requests-per-window,
  throttling code, or `Retry-After` behaviour could be confirmed. Assume a limit exists;
  treat 429 defensively and keep `RateLimitDelay` conservative until measured.

## Framework Fit Assessment

- **TypeSource:** `api` (REST/JSON:API). Confident.
- **Auth mapping:** OAuth2 bearer via VPAuth. **Best-guess = Pattern C (refresh_token)** given
  "login on a user account" + "token renewal is supported", with per-**Adviser** credential
  provisioning. Confidence: medium. `client_credentials` (Pattern B) only if VP exposes a
  machine/service user — **must confirm before build**, because unattended nightly ingestion
  needs a non-interactive token path, and the documented flow is user-login-based.
- **Incremental strategy:** **Unclear and a real risk.** Two candidates: (a) JSON:API
  page-cursor full pulls with a client-side watermark on an `updated`/`modified` attribute
  (UNVERIFIED that such a field exists); (b) **webhook-driven** ingestion, which does not fit
  the framework's poll-and-watermark model at all and would need a Logic Apps / push bridge
  (`logicapps` TypeSource) landing events in OneLake. Decide only after seeing the reference.
- **Multi-administratie / multi-tenant:** Maps cleanly to the framework's
  `PossibleEnvironments` / `EnvironmentColumnName`. The natural tenant axis is **Adviser** (or
  **Adviser-Client / administratie**). Because auth is provisioned per Adviser and tokens are
  user-scoped, a per-environment secret template
  (`visionplanner-{environment}-refresh-token`, etc.) fits Pattern C. The Silver environment
  column would be something like `AdviserId` / `AdviserClientId` — **UNVERIFIED field name.**

### Gotchas
1. **Direction mismatch (biggest one).** VP mostly *ingests* grootboek/begroting/jaarrekening
   *from* accounting systems and *produces* reports. The public API is oriented to
   **advisers, signing portals and webhooks**, not to bulk financial-figure extraction. The
   three target entities may simply **not exist as read endpoints** — for grootboek/budget the
   upstream source system (e-Boekhouden, SnelStart, Exact) is likely the correct connector,
   not Visionplanner.
2. **User-scoped tokens.** "The access token is always related to a known user" — headless
   ingestion needs a dedicated technical user per Adviser (or a machine-credential path VP may
   not offer). Confirm before committing to a nightly unattended job.
3. **Per-Adviser onboarding.** Integrations are registered into each Adviser's tenant by that
   Adviser's admin — there is no single global app credential; secret sprawl scales with the
   number of Adviser tenants.
4. **Webhook-first change model.** If VP's only "delta" mechanism is webhooks, the
   framework's pull/watermark pattern is a poor fit and a push bridge is required.
5. **JSON:API `Accept` header** (`application/vnd.api+json`) may be mandatory — a plain
   `application/json` request can be rejected by strict JSON:API servers. Verify.
6. **No published rate limits or base URL** — both must come from partner onboarding; do not
   hardcode guesses.

## Open Questions / UNVERIFIED (must resolve before any config-build)
1. OpenAPI reference contents: exact endpoints, operation list, `servers` base URLs. *(SPA
   barrier — read in a browser at .../docs/visionplanner-public-api-s.)*
2. VPAuth: grant type, authorize + token endpoint URLs, scope list, token TTL, refresh flow,
   and **whether a non-interactive/service credential exists**.
3. Do **jaarrekening / grootboek / budget-prognose** exist as *read* endpoints at all, or only
   as report documents / signing artefacts? (Current evidence: doubtful.)
4. Pagination + incremental/changed-since support (JSON:API page cursors vs webhook-only).
5. Rate limits + throttling behaviour.
6. Real API + VPAuth hostnames (not on any `*.visionplanner.com` subdomain that resolves
   today).
7. Multi-tenant identifiers: exact field names for Adviser / Adviser-Client / dossier to use
   as the Silver `EnvironmentColumnName`.

## Sources (primary first)
- Visionplanner public API portal (landing text = VP's own words): https://visionplanner.stoplight.io/
- API project (client-rendered reference): https://visionplanner.stoplight.io/docs/visionplanner-public-api-s
- JSON:API spec VP builds on: https://jsonapi.org/
- VP KB — grootboek onto reporting structure: https://hs.visionplanner.com/nl/grootboekrekeningen-koppelen-aan-de-rapportage-structuur
- VP KB — dossier jaarrekening: https://hs.visionplanner.com/nl/dossier-jaarrekening-aanmaken
- VP support — begroting import: https://support.visionplanner.com/import-begroting ; https://hs.visionplanner.com/nl/begroting-importeren
- VP support — e-Boekhouden inbound coupling: https://support.visionplanner.com/e-boekhouden.nl
- VP support — Excel financial-data template (inbound): https://support.visionplanner.com/downloaden-en-invullen-excel-sjabloon-financi%C3%ABle-gegevens
- SnelStart integration (VP consumes ledger data): https://www.snelstart.nl/koppelingen/visionplanner
- Third-party confirmation the API uses OAuth2/API-key auth (secondary): https://peliqan.io/connector/VisionPlanner/ ; https://apitracker.io/a/visionplanner
