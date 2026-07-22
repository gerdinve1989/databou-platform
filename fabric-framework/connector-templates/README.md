# connector-templates

This directory contains **framework-level example configs** â€” one subdirectory per supported data source. They are the canonical reference for how each connector type (`api`, `soap`, `logicapps`) is structured.

## Purpose

These files are **not client-specific**. They show:
- The correct structure and allowed values for each config section
- Representative entities, auth patterns, and extraction strategies per source
- The authoritative example a `config-builder` agent uses when generating a new client-config

Client-specific configs (sections 3/4) live in `{client-repo}/client-configs/` in the client GitHub repo. Sections 1/2/5 are stored in Supabase (`source_configs`, `source_entity_ingestion_configs`, `source_entity_process_configs`).

## File layout per source

Each source subdirectory holds **only the two PySpark sections** â€” sections 1/2/5
live in Supabase (see below), not as files here:

| File | Edited by | Contains |
|---|---|---|
| `03_schema.py` | Agents | PySpark `StructType` schemas for nested/complex Bronze entities |
| `04_transforms.py` | Agents | PySpark transform functions + `entity_transform_config` mapping |

> Taxi has no meaningful schema in `03_schema.py` â€” SQL sources are schema-on-read at runtime.

**Sections 1/2/5 are stored in Supabase**, not as files here:

| Section | Supabase table |
|---|---|
| 1 â€” `source_config` (connection, auth, entities, environments) | `connector_templates` + `connector_template_connections` |
| 2 â€” `entity_ingestion_config` (paths, watermarks, pagination) | `connector_template_entity_ingestion_configs` |
| 5 â€” `entity_process_config` (target tables, keys, SCD) | `connector_template_entity_process_configs` |

Each `connector_templates` row points at the two files above via
`schema_content_ref` / `transforms_content_ref` (relative to the framework repo,
resolved through `platform_config.github_repo`).

## Sources

| Directory | Source | TypeSource |
|---|---|---|
| `dip/` | DIP | `api` |
| `dyflexis/` | Dyflexis Planning.nu | `api` |
| `eijsink/` | Eijsink (booqcloud) | `api` |
| `renh/` | R&H Retailkassa | `soap` |
| `taxi/` | NYC Taxi | `sql` |
| `ticketcounter/` | Ticketcounter | `api` |
| `tomm/` | TOMM | `logicapps` |

## Standard placeholders

Framework configs use these placeholders for client-specific values:

| Placeholder | Meaning | Appears in TypeSource |
|---|---|---|
| `<keyvault_url>` | Azure Key Vault URL | All |
| `<connection_id>` | Fabric SQL connection GUID | `sql` |
| `<sql_server>` | Azure SQL server hostname | `sql` |
| `<database_name>` | Azure SQL database name | `sql` |
| `<database>` | Database identifier for secret naming | `sql` |
| `<tenant>` | Client tenant identifier in multi-tenant SaaS URLs | `api` |

### Secret naming patterns

- **API sources:** `{source}-{field}` or `{source}-{environment}-{field}`
- **SQL sources:** `<database>-{role}-{credential}`
- **SOAP sources:** `{source}-{environment}-{field}`

The `{environment}` placeholder is replaced at runtime by the framework based on `PossibleEnvironments`.

## Adding a new source

A new source template must be added here **before** any client can be onboarded to that source:

1. **Intake** infers the TypeSource (`api` / `soap` / `logicapps`) and verifies template coverage.
2. **Research** confirms auth, endpoints, entities and records findings in `fabric-framework/source-research/{source}_research.md`.
3. **config-builder** creates the template's sections 1/2/5 as rows in the `connector_templates*` Supabase tables, and the `{source}/03_schema.py` + `04_transforms.py` files here, following the confirmed TypeSource and template structure.
4. Grant the client access to the new template: add a `client_allowed_templates` row (`client_id` + `template_slug`). This is a governance change â€” a human does it via `deploy_client.py` (the `allowed_templates` list in the client's onboarding YAML), never an agent.

## Relation to templates

`templates/canonical-configs/` documents the **schema and allowed values** for each config section. These connector-templates are the **concrete examples** that implement those templates.
