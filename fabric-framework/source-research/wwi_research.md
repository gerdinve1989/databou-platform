# WideWorldImporters SQL Database Research

> Gemeten op 18-09-2026 met `scripts/source_sql_probe.py`, alle zes secties, tegen de live
> database. Alles in dit rapport komt uit die meting, tenzij er expliciet `UNKNOWN` staat.

## TypeSource
- Bevestigd: `sql`

## Overview

WideWorldImporters is de voorbeelddatabase van Microsoft voor een groothandel in
levensmiddelen en huishoudartikelen. De database is opgezet als operationeel systeem — het is
geen datawarehouse — en bevat de volledige keten van inkoop tot verkoop, plus magazijnbeheer en
sensortelemetrie.

De database telt **48 tabellen en 3 views**, verdeeld over vijf schema's:

| Schema | Rol |
|---|---|
| `Application` | stamgegevens die de rest van de database deelt: personen, geografie, betaal- en leveringswijzen, transactiesoorten |
| `Purchasing` | de inkoopkant: leveranciers, inkooporders, leverancierstransacties |
| `Sales` | de verkoopkant: klanten, orders, facturen, klanttransacties |
| `Warehouse` | artikelen, voorraadposities, voorraadmutaties en temperatuurmetingen |
| `Website` | drie views die als presentatielaag dienen; ze bevatten geen eigen gegevens |

**De vorm van de database wordt door twee dingen bepaald, en beide hebben gevolgen voor de
inrichting:**

1. **Zestien tabellen zijn historietabellen.** Elke tabel met een naam op `_Archive` hoort bij
   een basistabel, heeft dezelfde kolommen en types, en heeft **geen sleutel en geen enkele
   constraint**. De basistabellen dragen `ValidFrom` en `ValidTo`; in elke gemeten basisrij
   staat `ValidTo` op `9999-12-31 23:59:59.9999999`, in de archieftabellen staan afgesloten
   perioden. Dat is het gedrag van systeem-geversioneerde tabellen, waarbij de database de
   historie zelf bijhoudt.

   **Dit is waargenomen gedrag, geen gelezen eigenschap.** De meting rapporteert niet of een
   tabel systeem-geversioneerd is en welke historietabel erbij hoort; het patroon volgt uit de
   naamgeving, de identieke kolomlijsten, het ontbreken van sleutels en de waarden in
   `ValidTo`. Behandel de koppeling als zeer waarschijnlijk maar onbevestigd — zie *Open
   Questions*.

2. **Er zijn twee soorten wijzigingsstempels en ze sluiten elkaar uit.** Een tabel draagt
   `ValidFrom`/`ValidTo` (met historie) óf `LastEditedWhen` (zonder historie), nooit allebei.
   Beide zijn in elke gemeten tabel 0% leeg. Dat maakt per tabel één kolom vanzelfsprekend voor
   het oppikken van wijzigingen — zie *Watermark Candidates*.

Daarnaast staat er in vrijwel elke tabel een `LastEditedBy` die naar `Application.People`
verwijst. Dat verklaart waarom die ene tabel 41 inkomende foreign keys heeft: het is de
gebruikerstabel van het bronsysteem, niet alleen een dimensie.

## Ingestion Route Consideration

- **Mirrorbaar door Fabric?** Ja — dit is een Azure SQL Database, en dat is een van de brontypen
  die Fabric kan mirroren (Azure SQL / SQL Server / PostgreSQL / MySQL / Cosmos DB / Snowflake /
  BigQuery / Oracle).
- **Observatie:** de meting wijst twee kanten op. Vóór mirroring pleit de historie: 16 van de 48
  tabellen zijn archieftabellen die de bron zelf bijhoudt (het `_Archive`-patroon met
  `ValidFrom`/`ValidTo`), dus die historie bestaat al aan de bronkant en hoeft in de laadlaag niet
  te worden nagebouwd. Vóór de kopieerroute met Bronze en Silver pleit de veldselectie: er staan
  nog open vragen over persoonsgegevens, bankgegevens en `geography`-kolommen (zie *Open Questions
  / UNKNOWNs*, punten 5, 6 en 8), en die vragen om transformatie of uitsluiting van kolommen —
  werk dat in een transformatiestap thuishoort en niet in een één-op-één-kopie van de bron.
- Zie `data-agents/skills/data-ingestion/config-mirror/SKILL.md` voor de afweging en de werkwijze.
  **Deze sectie beslist niets:** ze zet de waarnemingen naast elkaar; de keuze tussen mirroring en
  de kopieerroute maakt config-builder samen met de klant.

## Connection

| | |
|---|---|
| Server | Azure SQL Database, serverless (staat in de klantconfig) |
| Database | WideWorldImporters |
| Auth method | SQL-login (gebruikersnaam + wachtwoord), gelezen uit de Key Vault van de klant |
| KeyVaultUrl | staat in de klantconfig, niet in dit rapport |
| UsernameSecret | volgens de conventie `{source}-username` |
| PasswordSecret | volgens de conventie `{source}-password` |

**Drie eigenschappen van deze bron die het ophalen raken, en die geen van drieën uit het
datamodel volgen:**

- **De database is serverless en pauzeert na 60 minuten inactiviteit.** De eerste verbinding na
  een stille periode faalt met SQL-fout 40613 (*database is not currently available*) terwijl de
  database opstart, en slaagt daarna. Het opstarten duurde bij de meting ongeveer een minuut.
  Een ophaalproces dat één keer probeert en dan opgeeft, faalt op een bron die verder prima
  werkt — dit vraagt om opnieuw proberen, niet om een foutmelding.
- **De server staat achter een IP-firewall.** Toegang werkt alleen vanaf een adres dat expliciet
  is toegelaten. Dat is een beheerhandeling aan de kant van de bron en geen instelling in de
  config.
- **De meting vraagt meer rechten dan alleen lezen.** Naast `SELECT` en `VIEW DEFINITION` heeft
  `source_sql_probe.py` het recht nodig om de statistiek-DMV's te lezen
  (`VIEW DATABASE PERFORMANCE STATE`, op oudere servers `VIEW DATABASE STATE`). Zonder dat recht
  draait geen enkele sectie van de meting, ook niet de secties die alleen metadata lezen. Voor
  het ophalen van data zelf is dat recht niet nodig — alleen voor het onderzoeken van de bron.

## Table / View Inventory

Measured 2026-09-18 with `source_sql_probe.py` section 1. Row counts come from partition
statistics, not from a `COUNT(*)`. 48 tables and 3 views.

| Schema | Name | Type | Row count | In scope | Notes |
|---|---|---|---|---|---|
| Application | Cities | TABLE | 37.940 | yes | 5,05 MB; PK `CityID`; carries `ValidFrom`/`ValidTo` |
| Application | Cities_Archive | TABLE | 43 | yes | 0,02 MB; no PK, no constraints; history of `Cities` |
| Application | Countries | TABLE | 190 | yes | 1,78 MB; PK `CountryID`; UNIQUE on `CountryName`, `FormalName` |
| Application | Countries_Archive | TABLE | 54 | yes | 0,68 MB; no PK; history of `Countries` |
| Application | DeliveryMethods | TABLE | 10 | yes | PK `DeliveryMethodID`; UNIQUE on `DeliveryMethodName` |
| Application | DeliveryMethods_Archive | TABLE | 1 | yes | no PK; history of `DeliveryMethods` |
| Application | PaymentMethods | TABLE | 4 | yes | PK `PaymentMethodID`; UNIQUE on `PaymentMethodName` |
| Application | PaymentMethods_Archive | TABLE | 1 | yes | no PK; history of `PaymentMethods` |
| Application | People | TABLE | 1.112 | yes | PK `PersonID`; 41 incoming foreign keys — the most referenced table in the database |
| Application | People_Archive | TABLE | 968 | yes | no PK; history of `People` |
| Application | StateProvinces | TABLE | 53 | yes | PK `StateProvinceID`; UNIQUE on `StateProvinceName` |
| Application | StateProvinces_Archive | TABLE | 114 | yes | no PK; history of `StateProvinces` |
| Application | SystemParameters | TABLE | 1 | yes | single-row settings table; `LastEditedWhen`, no `ValidFrom` |
| Application | TransactionTypes | TABLE | 13 | yes | PK `TransactionTypeID`; UNIQUE on `TransactionTypeName` |
| Application | TransactionTypes_Archive | TABLE | 1 | yes | no PK; history of `TransactionTypes` |
| Purchasing | PurchaseOrderLines | TABLE | 8.513 | yes | 2,63 MB; PK `PurchaseOrderLineID`; `LastEditedWhen` |
| Purchasing | PurchaseOrders | TABLE | 2.110 | yes | PK `PurchaseOrderID`; `LastEditedWhen` |
| Purchasing | SupplierCategories | TABLE | 9 | yes | PK `SupplierCategoryID`; UNIQUE on name |
| Purchasing | SupplierCategories_Archive | TABLE | 1 | yes | no PK; history of `SupplierCategories` |
| Purchasing | Suppliers | TABLE | 13 | yes | PK `SupplierID`; UNIQUE on `SupplierName`; carries bank account fields |
| Purchasing | Suppliers_Archive | TABLE | 13 | yes | no PK; history of `Suppliers` |
| Purchasing | SupplierTransactions | TABLE | 2.478 | yes | PK `SupplierTransactionID`; `LastEditedWhen` |
| Sales | BuyingGroups | TABLE | 2 | yes | PK `BuyingGroupID`; UNIQUE on name |
| Sales | BuyingGroups_Archive | TABLE | 0 | yes | empty; no PK; history of `BuyingGroups` |
| Sales | CustomerCategories | TABLE | 8 | yes | PK `CustomerCategoryID`; UNIQUE on name |
| Sales | CustomerCategories_Archive | TABLE | 1 | yes | no PK; history of `CustomerCategories` |
| Sales | Customers | TABLE | 664 | yes | PK `CustomerID`; UNIQUE on `CustomerName`; self-reference `BillToCustomerID` |
| Sales | Customers_Archive | TABLE | 70 | yes | no PK; history of `Customers` |
| Sales | CustomerTransactions | TABLE | 98.890 | yes | 23,29 MB; PK `CustomerTransactionID`; `LastEditedWhen` |
| Sales | InvoiceLines | TABLE | 232.447 | yes | 64,33 MB; PK `InvoiceLineID`; `LastEditedWhen` |
| Sales | Invoices | TABLE | 71.756 | yes | 88,48 MB — the largest table by size; PK `InvoiceID`; `LastEditedWhen` |
| Sales | OrderLines | TABLE | 235.737 | yes | 85,94 MB — the largest table by row count outside telemetry; PK `OrderLineID` |
| Sales | Orders | TABLE | 74.968 | yes | 19,38 MB; PK `OrderID`; self-reference `BackorderOrderID` |
| Sales | SpecialDeals | TABLE | 2 | yes | PK `SpecialDealID`; two CHECK constraints govern which discount field is filled |
| Warehouse | ColdRoomTemperatures | TABLE | 3 | ⚠ decision | sensor telemetry; identity PK; only 3 current rows against 4 million in its history table |
| Warehouse | ColdRoomTemperatures_Archive | TABLE | 4.076.195 | ⚠ decision | 294,66 MB — by far the largest object in the database; history of `ColdRoomTemperatures` |
| Warehouse | Colors | TABLE | 36 | yes | PK `ColorID`; UNIQUE on `ColorName` |
| Warehouse | Colors_Archive | TABLE | 1 | yes | no PK; history of `Colors` |
| Warehouse | PackageTypes | TABLE | 14 | yes | PK `PackageTypeID`; UNIQUE on name |
| Warehouse | PackageTypes_Archive | TABLE | 0 | yes | empty; no PK; history of `PackageTypes` |
| Warehouse | StockGroups | TABLE | 10 | yes | PK `StockGroupID`; UNIQUE on name |
| Warehouse | StockGroups_Archive | TABLE | 1 | yes | no PK; history of `StockGroups` |
| Warehouse | StockItemHoldings | TABLE | 227 | yes | PK `StockItemID` is also a foreign key — one holding row per stock item; current stock levels |
| Warehouse | StockItems | TABLE | 227 | yes | PK `StockItemID`; UNIQUE on `StockItemName` |
| Warehouse | StockItems_Archive | TABLE | 444 | yes | no PK; history of `StockItems` |
| Warehouse | StockItemStockGroups | TABLE | 442 | yes | link table; two UNIQUE constraints over the same pair of columns |
| Warehouse | StockItemTransactions | TABLE | 240.986 | yes | 65,66 MB; PK `StockItemTransactionID`; the stock movement ledger |
| Warehouse | VehicleTemperatures | TABLE | 74.710 | ⚠ decision | 34,50 MB; sensor telemetry; identity PK; no history table |
| Website | Customers | VIEW | 664 | no | presentation layer over `Sales.Customers` plus lookups |
| Website | Suppliers | VIEW | 13 | no | presentation layer over `Purchasing.Suppliers` plus lookups |
| Website | VehicleTemperatures | VIEW | 74.710 | no | presentation layer over `Warehouse.VehicleTemperatures` |

## Columns per Table

Measured with `source_sql_probe.py` section 2 (557 table columns) and section 4 (98 foreign
keys). `FK →` names the referenced table.

**How the history tables are written down here.** Each `*_Archive` table was measured and
carries exactly the same column list, in the same order, with the same declared types as its
base table — with one difference that holds for all sixteen of them: no primary key, no foreign
keys and no constraints of any kind. Rather than repeat sixteen identical column lists, each
history table below points at its base table and states that difference. Their measured *shape*
is listed separately and in full under *Column Shape*, because that does differ.

### Application.Cities
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| CityID | int | no | yes | | has a DEFAULT constraint |
| CityName | nvarchar(50) | no | | | |
| StateProvinceID | int | no | | Application.StateProvinces | |
| Location | geography | yes | | | not sampled by the measurement |
| LatestRecordedPopulation | bigint | yes | | | |
| LastEditedBy | int | no | | Application.People | |
| ValidFrom | datetime2(7) | no | | | period start |
| ValidTo | datetime2(7) | no | | | period end |

### Application.Cities_Archive
Same 8 columns and types as `Application.Cities`; no PK, no FK, no constraints.

### Application.Countries
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| CountryID | int | no | yes | | has a DEFAULT constraint |
| CountryName | nvarchar(60) | no | | | UNIQUE |
| FormalName | nvarchar(60) | no | | | UNIQUE |
| IsoAlpha3Code | nvarchar(3) | yes | | | |
| IsoNumericCode | int | yes | | | |
| CountryType | nvarchar(20) | yes | | | |
| LatestRecordedPopulation | bigint | yes | | | |
| Continent | nvarchar(30) | no | | | |
| Region | nvarchar(30) | no | | | |
| Subregion | nvarchar(30) | no | | | |
| Border | geography | yes | | | not sampled |
| LastEditedBy | int | no | | Application.People | |
| ValidFrom | datetime2(7) | no | | | period start |
| ValidTo | datetime2(7) | no | | | period end |

### Application.Countries_Archive
Same 14 columns and types as `Application.Countries`; no PK, no FK, no constraints.

### Application.DeliveryMethods
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| DeliveryMethodID | int | no | yes | | has a DEFAULT constraint |
| DeliveryMethodName | nvarchar(50) | no | | | UNIQUE |
| LastEditedBy | int | no | | Application.People | |
| ValidFrom | datetime2(7) | no | | | period start |
| ValidTo | datetime2(7) | no | | | period end |

### Application.DeliveryMethods_Archive
Same 5 columns and types as `Application.DeliveryMethods`; no PK, no FK, no constraints.

### Application.PaymentMethods
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| PaymentMethodID | int | no | yes | | has a DEFAULT constraint |
| PaymentMethodName | nvarchar(50) | no | | | UNIQUE |
| LastEditedBy | int | no | | Application.People | |
| ValidFrom | datetime2(7) | no | | | period start |
| ValidTo | datetime2(7) | no | | | period end |

### Application.PaymentMethods_Archive
Same 5 columns and types as `Application.PaymentMethods`; no PK, no FK, no constraints.

### Application.People
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| PersonID | int | no | yes | | has a DEFAULT constraint; referenced by 41 foreign keys |
| FullName | nvarchar(50) | no | | | personal data |
| PreferredName | nvarchar(50) | no | | | personal data |
| SearchName | nvarchar(101) | no | | | personal data |
| IsPermittedToLogon | bit | no | | | |
| LogonName | nvarchar(50) | yes | | | personal data |
| IsExternalLogonProvider | bit | no | | | |
| HashedPassword | varbinary(max) | yes | | | **credential material — exclude from ingestion** |
| IsSystemUser | bit | no | | | |
| IsEmployee | bit | no | | | |
| IsSalesperson | bit | no | | | |
| UserPreferences | nvarchar(max) | yes | | | JSON |
| PhoneNumber | nvarchar(20) | yes | | | personal data |
| FaxNumber | nvarchar(20) | yes | | | personal data |
| EmailAddress | nvarchar(256) | yes | | | personal data |
| Photo | varbinary(max) | yes | | | 100% empty in the sample |
| CustomFields | nvarchar(max) | yes | | | JSON |
| OtherLanguages | nvarchar(max) | yes | | | JSON |
| LastEditedBy | int | no | | Application.People | self-reference |
| ValidFrom | datetime2(7) | no | | | period start |
| ValidTo | datetime2(7) | no | | | period end |

### Application.People_Archive
Same 21 columns and types as `Application.People`; no PK, no FK, no constraints. Carries the
same personal data and the same `HashedPassword` column.

### Application.StateProvinces
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| StateProvinceID | int | no | yes | | has a DEFAULT constraint |
| StateProvinceCode | nvarchar(5) | no | | | |
| StateProvinceName | nvarchar(50) | no | | | UNIQUE |
| CountryID | int | no | | Application.Countries | |
| SalesTerritory | nvarchar(50) | no | | | |
| Border | geography | yes | | | not sampled |
| LatestRecordedPopulation | bigint | yes | | | |
| LastEditedBy | int | no | | Application.People | |
| ValidFrom | datetime2(7) | no | | | period start |
| ValidTo | datetime2(7) | no | | | period end |

### Application.StateProvinces_Archive
Same 10 columns and types as `Application.StateProvinces`; no PK, no FK, no constraints.

### Application.SystemParameters
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| SystemParameterID | int | no | yes | | has a DEFAULT constraint |
| DeliveryAddressLine1 | nvarchar(60) | no | | | |
| DeliveryAddressLine2 | nvarchar(60) | yes | | | |
| DeliveryCityID | int | no | | Application.Cities | |
| DeliveryPostalCode | nvarchar(10) | no | | | |
| DeliveryLocation | geography | no | | | not sampled |
| PostalAddressLine1 | nvarchar(60) | no | | | |
| PostalAddressLine2 | nvarchar(60) | yes | | | |
| PostalCityID | int | no | | Application.Cities | |
| PostalPostalCode | nvarchar(10) | no | | | |
| ApplicationSettings | nvarchar(max) | no | | | JSON, 3.298 characters in the single row |
| LastEditedBy | int | no | | Application.People | |
| LastEditedWhen | datetime2(7) | no | | | has a DEFAULT constraint; no `ValidFrom`/`ValidTo` |

### Application.TransactionTypes
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| TransactionTypeID | int | no | yes | | has a DEFAULT constraint |
| TransactionTypeName | nvarchar(50) | no | | | UNIQUE |
| LastEditedBy | int | no | | Application.People | |
| ValidFrom | datetime2(7) | no | | | period start |
| ValidTo | datetime2(7) | no | | | period end |

### Application.TransactionTypes_Archive
Same 5 columns and types as `Application.TransactionTypes`; no PK, no FK, no constraints.

### Purchasing.PurchaseOrderLines
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| PurchaseOrderLineID | int | no | yes | | has a DEFAULT constraint |
| PurchaseOrderID | int | no | | Purchasing.PurchaseOrders | |
| StockItemID | int | no | | Warehouse.StockItems | |
| OrderedOuters | int | no | | | |
| Description | nvarchar(100) | no | | | |
| ReceivedOuters | int | no | | | running total — see *state or event* |
| PackageTypeID | int | no | | Warehouse.PackageTypes | |
| ExpectedUnitPricePerOuter | decimal(18,2) | yes | | | |
| LastReceiptDate | date | yes | | | |
| IsOrderLineFinalized | bit | no | | | |
| LastEditedBy | int | no | | Application.People | |
| LastEditedWhen | datetime2(7) | no | | | has a DEFAULT constraint; change stamp |

### Purchasing.PurchaseOrders
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| PurchaseOrderID | int | no | yes | | has a DEFAULT constraint |
| SupplierID | int | no | | Purchasing.Suppliers | |
| OrderDate | date | no | | | business date |
| DeliveryMethodID | int | no | | Application.DeliveryMethods | |
| ContactPersonID | int | no | | Application.People | |
| ExpectedDeliveryDate | date | yes | | | |
| SupplierReference | nvarchar(20) | yes | | | |
| IsOrderFinalized | bit | no | | | |
| Comments | nvarchar(max) | yes | | | 100% empty in the sample |
| InternalComments | nvarchar(max) | yes | | | 100% empty in the sample |
| LastEditedBy | int | no | | Application.People | |
| LastEditedWhen | datetime2(7) | no | | | has a DEFAULT constraint; change stamp |

### Purchasing.SupplierCategories
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| SupplierCategoryID | int | no | yes | | has a DEFAULT constraint |
| SupplierCategoryName | nvarchar(50) | no | | | UNIQUE |
| LastEditedBy | int | no | | Application.People | |
| ValidFrom | datetime2(7) | no | | | period start |
| ValidTo | datetime2(7) | no | | | period end |

### Purchasing.SupplierCategories_Archive
Same 5 columns and types as `Purchasing.SupplierCategories`; no PK, no FK, no constraints.

### Purchasing.Suppliers
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| SupplierID | int | no | yes | | has a DEFAULT constraint |
| SupplierName | nvarchar(100) | no | | | UNIQUE |
| SupplierCategoryID | int | no | | Purchasing.SupplierCategories | |
| PrimaryContactPersonID | int | no | | Application.People | |
| AlternateContactPersonID | int | no | | Application.People | |
| DeliveryMethodID | int | yes | | Application.DeliveryMethods | |
| DeliveryCityID | int | no | | Application.Cities | |
| PostalCityID | int | no | | Application.Cities | |
| SupplierReference | nvarchar(20) | yes | | | |
| BankAccountName | nvarchar(50) | yes | | | **bank details — confirm before ingesting** |
| BankAccountBranch | nvarchar(50) | yes | | | **bank details** |
| BankAccountCode | nvarchar(20) | yes | | | **bank details** |
| BankAccountNumber | nvarchar(20) | yes | | | **bank details** |
| BankInternationalCode | nvarchar(20) | yes | | | **bank details** |
| PaymentDays | int | no | | | |
| InternalComments | nvarchar(max) | yes | | | |
| PhoneNumber | nvarchar(20) | no | | | |
| FaxNumber | nvarchar(20) | no | | | |
| WebsiteURL | nvarchar(256) | no | | | |
| DeliveryAddressLine1 | nvarchar(60) | no | | | |
| DeliveryAddressLine2 | nvarchar(60) | yes | | | |
| DeliveryPostalCode | nvarchar(10) | no | | | |
| DeliveryLocation | geography | yes | | | not sampled |
| PostalAddressLine1 | nvarchar(60) | no | | | |
| PostalAddressLine2 | nvarchar(60) | yes | | | |
| PostalPostalCode | nvarchar(10) | no | | | |
| LastEditedBy | int | no | | Application.People | |
| ValidFrom | datetime2(7) | no | | | period start |
| ValidTo | datetime2(7) | no | | | period end |

### Purchasing.Suppliers_Archive
Same 29 columns and types as `Purchasing.Suppliers`; no PK, no FK, no constraints. Carries the
same bank detail columns.

### Purchasing.SupplierTransactions
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| SupplierTransactionID | int | no | yes | | has a DEFAULT constraint |
| SupplierID | int | no | | Purchasing.Suppliers | |
| TransactionTypeID | int | no | | Application.TransactionTypes | |
| PurchaseOrderID | int | yes | | Purchasing.PurchaseOrders | |
| PaymentMethodID | int | yes | | Application.PaymentMethods | |
| SupplierInvoiceNumber | nvarchar(20) | yes | | | |
| TransactionDate | date | no | | | business date |
| AmountExcludingTax | decimal(18,2) | no | | | |
| TaxAmount | decimal(18,2) | no | | | |
| TransactionAmount | decimal(18,2) | no | | | can be negative |
| OutstandingBalance | decimal(18,2) | no | | | balance — see *state or event* |
| FinalizationDate | date | yes | | | |
| IsFinalized | bit | yes | | | |
| LastEditedBy | int | no | | Application.People | |
| LastEditedWhen | datetime2(7) | no | | | has a DEFAULT constraint; change stamp |

### Sales.BuyingGroups
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| BuyingGroupID | int | no | yes | | has a DEFAULT constraint |
| BuyingGroupName | nvarchar(50) | no | | | UNIQUE |
| LastEditedBy | int | no | | Application.People | |
| ValidFrom | datetime2(7) | no | | | period start |
| ValidTo | datetime2(7) | no | | | period end |

### Sales.BuyingGroups_Archive
Same 5 columns and types as `Sales.BuyingGroups`; no PK, no FK, no constraints. The table is
empty.

### Sales.CustomerCategories
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| CustomerCategoryID | int | no | yes | | has a DEFAULT constraint |
| CustomerCategoryName | nvarchar(50) | no | | | UNIQUE |
| LastEditedBy | int | no | | Application.People | |
| ValidFrom | datetime2(7) | no | | | period start |
| ValidTo | datetime2(7) | no | | | period end |

### Sales.CustomerCategories_Archive
Same 5 columns and types as `Sales.CustomerCategories`; no PK, no FK, no constraints.

### Sales.Customers
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| CustomerID | int | no | yes | | has a DEFAULT constraint |
| CustomerName | nvarchar(100) | no | | | UNIQUE |
| BillToCustomerID | int | no | | Sales.Customers | self-reference: the invoiced party |
| CustomerCategoryID | int | no | | Sales.CustomerCategories | |
| BuyingGroupID | int | yes | | Sales.BuyingGroups | |
| PrimaryContactPersonID | int | no | | Application.People | |
| AlternateContactPersonID | int | yes | | Application.People | |
| DeliveryMethodID | int | no | | Application.DeliveryMethods | |
| DeliveryCityID | int | no | | Application.Cities | |
| PostalCityID | int | no | | Application.Cities | |
| CreditLimit | decimal(18,2) | yes | | | limit — see *state or event* |
| AccountOpenedDate | date | no | | | |
| StandardDiscountPercentage | decimal(18,3) | no | | | |
| IsStatementSent | bit | no | | | |
| IsOnCreditHold | bit | no | | | status the source overwrites |
| PaymentDays | int | no | | | |
| PhoneNumber | nvarchar(20) | no | | | |
| FaxNumber | nvarchar(20) | no | | | |
| DeliveryRun | nvarchar(5) | yes | | | mostly blank rather than null |
| RunPosition | nvarchar(5) | yes | | | mostly blank rather than null |
| WebsiteURL | nvarchar(256) | no | | | |
| DeliveryAddressLine1 | nvarchar(60) | no | | | |
| DeliveryAddressLine2 | nvarchar(60) | yes | | | |
| DeliveryPostalCode | nvarchar(10) | no | | | |
| DeliveryLocation | geography | yes | | | not sampled |
| PostalAddressLine1 | nvarchar(60) | no | | | |
| PostalAddressLine2 | nvarchar(60) | yes | | | |
| PostalPostalCode | nvarchar(10) | no | | | |
| LastEditedBy | int | no | | Application.People | |
| ValidFrom | datetime2(7) | no | | | period start |
| ValidTo | datetime2(7) | no | | | period end |

### Sales.Customers_Archive
Same 31 columns and types as `Sales.Customers`; no PK, no FK, no constraints.

### Sales.CustomerTransactions
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| CustomerTransactionID | int | no | yes | | has a DEFAULT constraint |
| CustomerID | int | no | | Sales.Customers | |
| TransactionTypeID | int | no | | Application.TransactionTypes | |
| InvoiceID | int | yes | | Sales.Invoices | |
| PaymentMethodID | int | yes | | Application.PaymentMethods | 76% empty in the sample |
| TransactionDate | date | no | | | business date |
| AmountExcludingTax | decimal(18,2) | no | | | |
| TaxAmount | decimal(18,2) | no | | | |
| TransactionAmount | decimal(18,2) | no | | | can be negative |
| OutstandingBalance | decimal(18,2) | no | | | balance — see *state or event* |
| FinalizationDate | date | yes | | | |
| IsFinalized | bit | yes | | | |
| LastEditedBy | int | no | | Application.People | |
| LastEditedWhen | datetime2(7) | no | | | has a DEFAULT constraint; change stamp |

### Sales.InvoiceLines
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| InvoiceLineID | int | no | yes | | has a DEFAULT constraint |
| InvoiceID | int | no | | Sales.Invoices | |
| StockItemID | int | no | | Warehouse.StockItems | |
| Description | nvarchar(100) | no | | | |
| PackageTypeID | int | no | | Warehouse.PackageTypes | |
| Quantity | int | no | | | |
| UnitPrice | decimal(18,2) | yes | | | |
| TaxRate | decimal(18,3) | no | | | |
| TaxAmount | decimal(18,2) | no | | | |
| LineProfit | decimal(18,2) | no | | | can be negative |
| ExtendedPrice | decimal(18,2) | no | | | |
| LastEditedBy | int | no | | Application.People | |
| LastEditedWhen | datetime2(7) | no | | | has a DEFAULT constraint; change stamp |

### Sales.Invoices
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| InvoiceID | int | no | yes | | has a DEFAULT constraint |
| CustomerID | int | no | | Sales.Customers | |
| BillToCustomerID | int | no | | Sales.Customers | |
| OrderID | int | yes | | Sales.Orders | one invoice per order in the sample |
| DeliveryMethodID | int | no | | Application.DeliveryMethods | |
| ContactPersonID | int | no | | Application.People | |
| AccountsPersonID | int | no | | Application.People | |
| SalespersonPersonID | int | no | | Application.People | |
| PackedByPersonID | int | no | | Application.People | |
| InvoiceDate | date | no | | | business date |
| CustomerPurchaseOrderNumber | nvarchar(20) | yes | | | |
| IsCreditNote | bit | no | | | |
| CreditNoteReason | nvarchar(max) | yes | | | 100% empty in the sample |
| Comments | nvarchar(max) | yes | | | 100% empty in the sample |
| DeliveryInstructions | nvarchar(max) | yes | | | |
| InternalComments | nvarchar(max) | yes | | | 100% empty in the sample |
| TotalDryItems | int | no | | | |
| TotalChillerItems | int | no | | | |
| DeliveryRun | nvarchar(5) | yes | | | 100% blank in the sample |
| RunPosition | nvarchar(5) | yes | | | 100% blank in the sample |
| ReturnedDeliveryData | nvarchar(max) | yes | | | JSON; a CHECK constraint enforces valid JSON |
| ConfirmedDeliveryTime | datetime2(7) | yes | | | |
| ConfirmedReceivedBy | nvarchar(4000) | yes | | | personal data — a name |
| LastEditedBy | int | no | | Application.People | |
| LastEditedWhen | datetime2(7) | no | | | has a DEFAULT constraint; change stamp |

### Sales.OrderLines
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| OrderLineID | int | no | yes | | has a DEFAULT constraint |
| OrderID | int | no | | Sales.Orders | |
| StockItemID | int | no | | Warehouse.StockItems | |
| Description | nvarchar(100) | no | | | |
| PackageTypeID | int | no | | Warehouse.PackageTypes | |
| Quantity | int | no | | | |
| UnitPrice | decimal(18,2) | yes | | | |
| TaxRate | decimal(18,3) | no | | | |
| PickedQuantity | int | no | | | running total — see *state or event* |
| PickingCompletedWhen | datetime2(7) | yes | | | |
| LastEditedBy | int | no | | Application.People | |
| LastEditedWhen | datetime2(7) | no | | | has a DEFAULT constraint; change stamp |

### Sales.Orders
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| OrderID | int | no | yes | | has a DEFAULT constraint |
| CustomerID | int | no | | Sales.Customers | |
| SalespersonPersonID | int | no | | Application.People | |
| PickedByPersonID | int | yes | | Application.People | |
| ContactPersonID | int | no | | Application.People | |
| BackorderOrderID | int | yes | | Sales.Orders | self-reference |
| OrderDate | date | no | | | business date |
| ExpectedDeliveryDate | date | no | | | |
| CustomerPurchaseOrderNumber | nvarchar(20) | yes | | | |
| IsUndersupplyBackordered | bit | no | | | |
| Comments | nvarchar(max) | yes | | | 100% empty in the sample |
| DeliveryInstructions | nvarchar(max) | yes | | | 100% empty in the sample |
| InternalComments | nvarchar(max) | yes | | | 100% empty in the sample |
| PickingCompletedWhen | datetime2(7) | yes | | | |
| LastEditedBy | int | no | | Application.People | |
| LastEditedWhen | datetime2(7) | no | | | has a DEFAULT constraint; change stamp |

### Sales.SpecialDeals
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| SpecialDealID | int | no | yes | | has a DEFAULT constraint |
| StockItemID | int | yes | | Warehouse.StockItems | |
| CustomerID | int | yes | | Sales.Customers | |
| BuyingGroupID | int | yes | | Sales.BuyingGroups | |
| CustomerCategoryID | int | yes | | Sales.CustomerCategories | |
| StockGroupID | int | yes | | Warehouse.StockGroups | |
| DealDescription | nvarchar(30) | no | | | |
| StartDate | date | no | | | |
| EndDate | date | no | | | |
| DiscountAmount | decimal(18,2) | yes | | | a CHECK constraint allows exactly one of the three discount forms |
| DiscountPercentage | decimal(18,3) | yes | | | |
| UnitPrice | decimal(18,2) | yes | | | |
| LastEditedBy | int | no | | Application.People | |
| LastEditedWhen | datetime2(7) | no | | | has a DEFAULT constraint; change stamp |

### Warehouse.ColdRoomTemperatures
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| ColdRoomTemperatureID | bigint | no | yes | | identity column |
| ColdRoomSensorNumber | int | no | | | |
| RecordedWhen | datetime2(7) | no | | | measurement moment |
| Temperature | decimal(10,2) | no | | | |
| ValidFrom | datetime2(7) | no | | | period start |
| ValidTo | datetime2(7) | no | | | period end |

### Warehouse.ColdRoomTemperatures_Archive
Same 6 columns and types as `Warehouse.ColdRoomTemperatures`; no PK, no FK, no constraints.
4.076.195 rows — the largest object in the database.

### Warehouse.Colors
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| ColorID | int | no | yes | | has a DEFAULT constraint |
| ColorName | nvarchar(20) | no | | | UNIQUE |
| LastEditedBy | int | no | | Application.People | |
| ValidFrom | datetime2(7) | no | | | period start |
| ValidTo | datetime2(7) | no | | | period end |

### Warehouse.Colors_Archive
Same 5 columns and types as `Warehouse.Colors`; no PK, no FK, no constraints.

### Warehouse.PackageTypes
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| PackageTypeID | int | no | yes | | has a DEFAULT constraint |
| PackageTypeName | nvarchar(50) | no | | | UNIQUE |
| LastEditedBy | int | no | | Application.People | |
| ValidFrom | datetime2(7) | no | | | period start |
| ValidTo | datetime2(7) | no | | | period end |

### Warehouse.PackageTypes_Archive
Same 5 columns and types as `Warehouse.PackageTypes`; no PK, no FK, no constraints. The table
is empty.

### Warehouse.StockGroups
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| StockGroupID | int | no | yes | | has a DEFAULT constraint |
| StockGroupName | nvarchar(50) | no | | | UNIQUE |
| LastEditedBy | int | no | | Application.People | |
| ValidFrom | datetime2(7) | no | | | period start |
| ValidTo | datetime2(7) | no | | | period end |

### Warehouse.StockGroups_Archive
Same 5 columns and types as `Warehouse.StockGroups`; no PK, no FK, no constraints.

### Warehouse.StockItemHoldings
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| StockItemID | int | no | yes | Warehouse.StockItems | the PK is itself the foreign key: one row per stock item |
| QuantityOnHand | int | no | | | stock level — see *state or event* |
| BinLocation | nvarchar(20) | no | | | |
| LastStocktakeQuantity | int | no | | | |
| LastCostPrice | decimal(18,2) | no | | | |
| ReorderLevel | int | no | | | |
| TargetStockLevel | int | no | | | |
| LastEditedBy | int | no | | Application.People | |
| LastEditedWhen | datetime2(7) | no | | | has a DEFAULT constraint; change stamp |

### Warehouse.StockItems
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| StockItemID | int | no | yes | | has a DEFAULT constraint |
| StockItemName | nvarchar(100) | no | | | UNIQUE |
| SupplierID | int | no | | Purchasing.Suppliers | |
| ColorID | int | yes | | Warehouse.Colors | |
| UnitPackageID | int | no | | Warehouse.PackageTypes | |
| OuterPackageID | int | no | | Warehouse.PackageTypes | |
| Brand | nvarchar(50) | yes | | | 92% empty in the sample |
| Size | nvarchar(20) | yes | | | |
| LeadTimeDays | int | no | | | |
| QuantityPerOuter | int | no | | | |
| IsChillerStock | bit | no | | | |
| Barcode | nvarchar(50) | yes | | | 97% empty in the sample |
| TaxRate | decimal(18,3) | no | | | |
| UnitPrice | decimal(18,2) | no | | | current price — see *state or event* |
| RecommendedRetailPrice | decimal(18,2) | yes | | | |
| TypicalWeightPerUnit | decimal(18,3) | no | | | |
| MarketingComments | nvarchar(max) | yes | | | |
| InternalComments | nvarchar(max) | yes | | | 100% empty in the sample |
| Photo | varbinary(max) | yes | | | 100% empty in the sample |
| CustomFields | nvarchar(max) | yes | | | JSON |
| Tags | nvarchar(max) | yes | | | JSON |
| SearchDetails | nvarchar(max) | no | | | |
| LastEditedBy | int | no | | Application.People | |
| ValidFrom | datetime2(7) | no | | | period start |
| ValidTo | datetime2(7) | no | | | period end |

### Warehouse.StockItems_Archive
Same 25 columns and types as `Warehouse.StockItems`; no PK, no FK, no constraints.

### Warehouse.StockItemStockGroups
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| StockItemStockGroupID | int | no | yes | | has a DEFAULT constraint |
| StockItemID | int | no | | Warehouse.StockItems | |
| StockGroupID | int | no | | Warehouse.StockGroups | |
| LastEditedBy | int | no | | Application.People | |
| LastEditedWhen | datetime2(7) | no | | | has a DEFAULT constraint; change stamp |

Two UNIQUE constraints cover the same pair of columns in opposite order
(`StockGroupID, StockItemID` and `StockItemID, StockGroupID`). The natural key is the pair.

### Warehouse.StockItemTransactions
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| StockItemTransactionID | int | no | yes | | has a DEFAULT constraint |
| StockItemID | int | no | | Warehouse.StockItems | |
| TransactionTypeID | int | no | | Application.TransactionTypes | |
| CustomerID | int | yes | | Sales.Customers | filled on outbound movements |
| InvoiceID | int | yes | | Sales.Invoices | filled on outbound movements |
| SupplierID | int | yes | | Purchasing.Suppliers | filled on inbound movements |
| PurchaseOrderID | int | yes | | Purchasing.PurchaseOrders | filled on inbound movements |
| TransactionOccurredWhen | datetime2(7) | no | | | the movement moment |
| Quantity | decimal(18,3) | no | | | movement, can be negative |
| LastEditedBy | int | no | | Application.People | |
| LastEditedWhen | datetime2(7) | no | | | has a DEFAULT constraint; change stamp |

### Warehouse.VehicleTemperatures
| Column | Data type | Nullable | PK | FK → | Notes |
|---|---|---|---|---|---|
| VehicleTemperatureID | bigint | no | yes | | identity column |
| VehicleRegistration | nvarchar(20) | no | | | |
| ChillerSensorNumber | int | no | | | |
| RecordedWhen | datetime2(7) | no | | | measurement moment |
| Temperature | decimal(10,2) | no | | | |
| IsCompressed | bit | no | | | |
| FullSensorData | nvarchar(1000) | yes | | | JSON payload per measurement |
| CompressedSensorData | varbinary(max) | yes | | | 100% empty in the sample |

### The three views in Website
Measured separately. They carry no keys, no indexes and no constraints of their own — the
measurement reports zero for all three sections. They are presentation layers over tables that
are already in scope.

| View | Columns | Rows | Built over |
|---|---|---|---|
| Website.Customers | 14 | 664 | `Sales.Customers` plus category, contact, buying group, delivery method and city lookups |
| Website.Suppliers | 12 | 13 | `Purchasing.Suppliers` plus category, contact, delivery method and city lookups |
| Website.VehicleTemperatures | 6 | 74.710 | `Warehouse.VehicleTemperatures`, without the compressed payload column |

## Column Shape

Measured with `source_sql_probe.py` section 6. No value is read back out of the source: per
column this is counts, lengths, and — for numbers, dates and bit only — the range. `Min` and
`Max` stay empty for text, binary, uniqueidentifier and xml by design; there a minimum or a
maximum would be a value rather than a measure, and `Min len` / `Max len` answer the width
question instead.

> **Read the range as the shape of the sample, not of the table.** The measurement reads the
> first 1000 rows per object without sorting. For every table with more than 1000 rows the
> range shown below is therefore the range of those first rows — `Sales.Orders` reads
> `2013-01-01` to `2013-01-18` while the table holds 74.968 rows. It is not the range of the
> table, and it must not be used to size a load window. The true maximum per table is listed as
> `UNKNOWN` under *Watermark Candidates*.

Eleven `geography` columns are skipped by the measurement; they appear below without figures
and carry the measurement's own remark.

### Application.Cities
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| CityID | 1000 | 0,0 | 0 | 1000 | yes | 1 | 4 | 1 | 1002 |
| CityName | 1000 | 0,0 | 0 | 574 | no | 3 | 21 | | |
| StateProvinceID | 1000 | 0,0 | 0 | 49 | no | 1 | 2 | 1 | 53 |
| Location | | | | | no | | | | not sampled (geography) |
| LatestRecordedPopulation | 1000 | 28,9 | 0 | 618 | no | 1 | 6 | 0 | 545852 |
| LastEditedBy | 1000 | 0,0 | 0 | 2 | no | 1 | 2 | 1 | 15 |
| ValidFrom | 1000 | 0,0 | 0 | 2 | no | 19 | 19 | 2013-01-01T00:00:00 | 2015-07-01T16:00:00 |
| ValidTo | 1000 | 0,0 | 0 | 1 | no | 27 | 27 | 9999-12-31T23:59:59.9999999 | 9999-12-31T23:59:59.9999999 |

### Application.Cities_Archive
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| CityID | 43 | 0,0 | 0 | 43 | yes | 3 | 5 | 164 | 37442 |
| CityName | 43 | 0,0 | 0 | 43 | yes | 4 | 16 | | |
| StateProvinceID | 43 | 0,0 | 0 | 30 | no | 1 | 2 | 4 | 52 |
| Location | | | | | no | | | | not sampled (geography) |
| LatestRecordedPopulation | 43 | 41,9 | 0 | 25 | no | 2 | 5 | 42 | 36812 |
| LastEditedBy | 43 | 0,0 | 0 | 1 | no | 1 | 1 | 1 | 1 |
| ValidFrom | 43 | 0,0 | 0 | 1 | no | 19 | 19 | 2013-01-01T00:00:00 | 2013-01-01T00:00:00 |
| ValidTo | 43 | 0,0 | 0 | 4 | no | 19 | 19 | 2013-07-01T16:00:00 | 2026-07-01T16:00:00 |

### Application.Countries
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| CountryID | 190 | 0,0 | 0 | 190 | yes | 1 | 3 | 1 | 241 |
| CountryName | 190 | 0,0 | 0 | 190 | yes | 4 | 21 | | |
| FormalName | 190 | 0,0 | 0 | 190 | yes | 5 | 52 | | |
| IsoAlpha3Code | 190 | 0,0 | 0 | 190 | yes | 3 | 3 | | |
| IsoNumericCode | 190 | 0,0 | 0 | 190 | yes | 1 | 3 | 4 | 894 |
| CountryType | 190 | 0,0 | 0 | 1 | no | 15 | 15 | | |
| LatestRecordedPopulation | 190 | 0,0 | 0 | 190 | yes | 5 | 10 | 14019 | 1447843787 |
| Continent | 190 | 0,0 | 0 | 7 | no | 4 | 23 | | |
| Region | 190 | 0,0 | 0 | 5 | no | 4 | 8 | | |
| Subregion | 190 | 0,0 | 0 | 22 | no | 9 | 25 | | |
| Border | | | | | no | | | | not sampled (geography) |
| LastEditedBy | 190 | 0,0 | 0 | 5 | no | 1 | 2 | 1 | 20 |
| ValidFrom | 190 | 0,0 | 0 | 6 | no | 19 | 27 | 2013-01-01T00:00:00 | 2026-07-01T16:00:00 |
| ValidTo | 190 | 0,0 | 0 | 1 | no | 27 | 27 | 9999-12-31T23:59:59.9999999 | 9999-12-31T23:59:59.9999999 |

### Application.Countries_Archive
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| CountryID | 54 | 0,0 | 0 | 50 | no | 1 | 3 | 3 | 229 |
| CountryName | 54 | 0,0 | 0 | 50 | no | 4 | 18 | | |
| FormalName | 54 | 0,0 | 0 | 50 | no | 5 | 52 | | |
| IsoAlpha3Code | 54 | 0,0 | 0 | 50 | no | 3 | 3 | | |
| IsoNumericCode | 54 | 0,0 | 0 | 50 | no | 1 | 3 | 8 | 882 |
| CountryType | 54 | 0,0 | 0 | 1 | no | 15 | 15 | | |
| LatestRecordedPopulation | 54 | 0,0 | 0 | 54 | yes | 5 | 10 | 20796 | 1392157488 |
| Continent | 54 | 0,0 | 0 | 6 | no | 4 | 13 | | |
| Region | 54 | 0,0 | 0 | 5 | no | 4 | 8 | | |
| Subregion | 54 | 0,0 | 0 | 22 | no | 9 | 25 | | |
| Border | | | | | no | | | | not sampled (geography) |
| LastEditedBy | 54 | 0,0 | 0 | 4 | no | 1 | 2 | 1 | 20 |
| ValidFrom | 54 | 0,0 | 0 | 4 | no | 19 | 19 | 2013-01-01T00:00:00 | 2015-07-01T16:00:00 |
| ValidTo | 54 | 0,0 | 0 | 5 | no | 19 | 27 | 2013-07-01T16:00:00 | 2026-07-01T16:00:00 |

### Application.DeliveryMethods
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| DeliveryMethodID | 10 | 0,0 | 0 | 10 | yes | 1 | 2 | 1 | 10 |
| DeliveryMethodName | 10 | 0,0 | 0 | 10 | yes | 4 | 27 | | |
| LastEditedBy | 10 | 0,0 | 0 | 2 | no | 1 | 2 | 1 | 16 |
| ValidFrom | 10 | 0,0 | 0 | 2 | no | 19 | 19 | 2013-01-01T00:00:00 | 2015-01-01T16:00:00 |
| ValidTo | 10 | 0,0 | 0 | 1 | no | 27 | 27 | 9999-12-31T23:59:59.9999999 | 9999-12-31T23:59:59.9999999 |

### Application.DeliveryMethods_Archive
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| DeliveryMethodID | 1 | 0,0 | 0 | 1 | yes | 1 | 1 | 5 | 5 |
| DeliveryMethodName | 1 | 0,0 | 0 | 1 | yes | 16 | 16 | | |
| LastEditedBy | 1 | 0,0 | 0 | 1 | yes | 1 | 1 | 1 | 1 |
| ValidFrom | 1 | 0,0 | 0 | 1 | yes | 19 | 19 | 2013-01-01T00:00:00 | 2013-01-01T00:00:00 |
| ValidTo | 1 | 0,0 | 0 | 1 | yes | 19 | 19 | 2015-01-01T16:00:00 | 2015-01-01T16:00:00 |

### Application.PaymentMethods
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| PaymentMethodID | 4 | 0,0 | 0 | 4 | yes | 1 | 1 | 1 | 4 |
| PaymentMethodName | 4 | 0,0 | 0 | 4 | yes | 3 | 11 | | |
| LastEditedBy | 4 | 0,0 | 0 | 2 | no | 1 | 1 | 1 | 9 |
| ValidFrom | 4 | 0,0 | 0 | 2 | no | 19 | 19 | 2013-01-01T00:00:00 | 2016-01-01T16:00:00 |
| ValidTo | 4 | 0,0 | 0 | 1 | no | 27 | 27 | 9999-12-31T23:59:59.9999999 | 9999-12-31T23:59:59.9999999 |

### Application.PaymentMethods_Archive
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| PaymentMethodID | 1 | 0,0 | 0 | 1 | yes | 1 | 1 | 3 | 3 |
| PaymentMethodName | 1 | 0,0 | 0 | 1 | yes | 11 | 11 | | |
| LastEditedBy | 1 | 0,0 | 0 | 1 | yes | 1 | 1 | 1 | 1 |
| ValidFrom | 1 | 0,0 | 0 | 1 | yes | 19 | 19 | 2013-01-01T00:00:00 | 2013-01-01T00:00:00 |
| ValidTo | 1 | 0,0 | 0 | 1 | yes | 19 | 19 | 2016-01-01T16:00:00 | 2016-01-01T16:00:00 |

### Application.People
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| PersonID | 1000 | 0,0 | 0 | 1000 | yes | 1 | 4 | 1 | 3150 |
| FullName | 1000 | 0,0 | 0 | 1000 | yes | 5 | 29 | | |
| PreferredName | 1000 | 0,0 | 0 | 809 | no | 2 | 20 | | |
| SearchName | 1000 | 0,0 | 0 | 1000 | yes | 8 | 46 | | |
| IsPermittedToLogon | 1000 | 0,0 | 0 | 2 | no | 1 | 1 | 0 | 1 |
| LogonName | 1000 | 0,0 | 0 | 143 | no | 8 | 32 | | |
| IsExternalLogonProvider | 1000 | 0,0 | 0 | 1 | no | 1 | 1 | 0 | 0 |
| HashedPassword | 1000 | 85,7 | 0 | 143 | no | 66 | 66 | | |
| IsSystemUser | 1000 | 0,0 | 0 | 2 | no | 1 | 1 | 0 | 1 |
| IsEmployee | 1000 | 0,0 | 0 | 2 | no | 1 | 1 | 0 | 1 |
| IsSalesperson | 1000 | 0,0 | 0 | 2 | no | 1 | 1 | 0 | 1 |
| UserPreferences | 1000 | 83,2 | 0 | 59 | no | 136 | 154 | | |
| PhoneNumber | 1000 | 0,1 | 0 | 71 | no | 14 | 14 | | |
| FaxNumber | 1000 | 0,1 | 0 | 61 | no | 14 | 14 | | |
| EmailAddress | 1000 | 0,1 | 0 | 929 | no | 15 | 33 | | |
| Photo | 1000 | 100,0 | 0 | 0 | no | | | | |
| CustomFields | 1000 | 98,1 | 0 | 19 | no | 83 | 166 | | |
| OtherLanguages | 1000 | 98,1 | 0 | 17 | no | 2 | 32 | | |
| LastEditedBy | 1000 | 0,0 | 0 | 1 | no | 1 | 1 | 1 | 1 |
| ValidFrom | 1000 | 0,0 | 0 | 7 | no | 19 | 19 | 2013-01-01T00:00:00 | 2026-06-29T08:00:00 |
| ValidTo | 1000 | 0,0 | 0 | 1 | no | 27 | 27 | 9999-12-31T23:59:59.9999999 | 9999-12-31T23:59:59.9999999 |

### Application.People_Archive
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| PersonID | 968 | 0,0 | 0 | 184 | no | 1 | 4 | 1 | 3254 |
| FullName | 968 | 0,0 | 0 | 184 | no | 7 | 23 | | |
| PreferredName | 968 | 0,0 | 0 | 173 | no | 2 | 20 | | |
| SearchName | 968 | 0,0 | 0 | 184 | no | 10 | 41 | | |
| IsPermittedToLogon | 968 | 0,0 | 0 | 2 | no | 1 | 1 | 0 | 1 |
| LogonName | 968 | 0,0 | 0 | 156 | no | 8 | 32 | | |
| IsExternalLogonProvider | 968 | 0,0 | 0 | 1 | no | 1 | 1 | 0 | 0 |
| HashedPassword | 968 | 17,0 | 0 | 174 | no | 66 | 66 | | |
| IsSystemUser | 968 | 0,0 | 0 | 2 | no | 1 | 1 | 0 | 1 |
| IsEmployee | 968 | 0,0 | 0 | 2 | no | 1 | 1 | 0 | 1 |
| IsSalesperson | 968 | 0,0 | 0 | 2 | no | 1 | 1 | 0 | 1 |
| UserPreferences | 968 | 14,3 | 0 | 6 | no | 127 | 148 | | |
| PhoneNumber | 968 | 0,1 | 0 | 65 | no | 14 | 14 | | |
| FaxNumber | 968 | 0,1 | 0 | 55 | no | 14 | 14 | | |
| EmailAddress | 968 | 0,1 | 0 | 181 | no | 14 | 33 | | |
| Photo | 968 | 100,0 | 0 | 0 | no | | | | |
| CustomFields | 968 | 98,0 | 0 | 19 | no | 83 | 166 | | |
| OtherLanguages | 968 | 98,0 | 0 | 17 | no | 2 | 32 | | |
| LastEditedBy | 968 | 0,0 | 0 | 1 | no | 1 | 1 | 1 | 1 |
| ValidFrom | 968 | 0,0 | 0 | 622 | no | 19 | 19 | 2013-01-01T00:00:00 | 2016-05-31T23:14:00 |
| ValidTo | 968 | 0,0 | 0 | 622 | no | 19 | 19 | 2013-01-01T08:00:00 | 2026-06-29T08:00:00 |

### Application.StateProvinces
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| StateProvinceID | 53 | 0,0 | 0 | 53 | yes | 1 | 2 | 1 | 53 |
| StateProvinceCode | 53 | 0,0 | 0 | 53 | yes | 2 | 2 | | |
| StateProvinceName | 53 | 0,0 | 0 | 53 | yes | 4 | 29 | | |
| CountryID | 53 | 0,0 | 0 | 1 | no | 3 | 3 | 230 | 230 |
| SalesTerritory | 53 | 0,0 | 0 | 9 | no | 6 | 14 | | |
| Border | | | | | no | | | | not sampled (geography) |
| LatestRecordedPopulation | 53 | 0,0 | 0 | 53 | yes | 6 | 8 | 104737 | 41460453 |
| LastEditedBy | 53 | 0,0 | 0 | 5 | no | 1 | 2 | 1 | 20 |
| ValidFrom | 53 | 0,0 | 0 | 10 | no | 19 | 19 | 2013-01-01T00:00:00 | 2026-07-01T16:00:00 |
| ValidTo | 53 | 0,0 | 0 | 1 | no | 27 | 27 | 9999-12-31T23:59:59.9999999 | 9999-12-31T23:59:59.9999999 |

### Application.StateProvinces_Archive
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| StateProvinceID | 114 | 0,0 | 0 | 52 | no | 1 | 2 | 1 | 53 |
| StateProvinceCode | 114 | 0,0 | 0 | 52 | no | 2 | 2 | | |
| StateProvinceName | 114 | 0,0 | 0 | 52 | no | 4 | 26 | | |
| CountryID | 114 | 0,0 | 0 | 1 | no | 3 | 3 | 230 | 230 |
| SalesTerritory | 114 | 0,0 | 0 | 9 | no | 6 | 14 | | |
| Border | | | | | no | | | | not sampled (geography) |
| LatestRecordedPopulation | 114 | 0,0 | 0 | 77 | no | 6 | 8 | 582658 | 39865821 |
| LastEditedBy | 114 | 0,0 | 0 | 5 | no | 1 | 2 | 1 | 20 |
| ValidFrom | 114 | 0,0 | 0 | 10 | no | 19 | 19 | 2013-01-01T00:00:00 | 2026-07-01T16:00:00 |
| ValidTo | 114 | 0,0 | 0 | 9 | no | 19 | 19 | 2013-01-01T00:01:00 | 2026-07-01T16:00:00 |

### Application.SystemParameters
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| SystemParameterID | 1 | 0,0 | 0 | 1 | yes | 1 | 1 | 1 | 1 |
| DeliveryAddressLine1 | 1 | 0,0 | 0 | 1 | yes | 8 | 8 | | |
| DeliveryAddressLine2 | 1 | 0,0 | 0 | 1 | yes | 36 | 36 | | |
| DeliveryCityID | 1 | 0,0 | 0 | 1 | yes | 5 | 5 | 30378 | 30378 |
| DeliveryPostalCode | 1 | 0,0 | 0 | 1 | yes | 5 | 5 | | |
| DeliveryLocation | | | | | no | | | | not sampled (geography) |
| PostalAddressLine1 | 1 | 0,0 | 0 | 1 | yes | 13 | 13 | | |
| PostalAddressLine2 | 1 | 0,0 | 0 | 1 | yes | 16 | 16 | | |
| PostalCityID | 1 | 0,0 | 0 | 1 | yes | 5 | 5 | 30378 | 30378 |
| PostalPostalCode | 1 | 0,0 | 0 | 1 | yes | 5 | 5 | | |
| ApplicationSettings | 1 | 0,0 | 0 | 1 | yes | 3298 | 3298 | | |
| LastEditedBy | 1 | 0,0 | 0 | 1 | yes | 1 | 1 | 1 | 1 |
| LastEditedWhen | 1 | 0,0 | 0 | 1 | yes | 19 | 19 | 2013-01-01T00:00:00 | 2013-01-01T00:00:00 |

### Application.TransactionTypes
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| TransactionTypeID | 13 | 0,0 | 0 | 13 | yes | 1 | 2 | 1 | 13 |
| TransactionTypeName | 13 | 0,0 | 0 | 13 | yes | 11 | 29 | | |
| LastEditedBy | 13 | 0,0 | 0 | 2 | no | 1 | 1 | 1 | 9 |
| ValidFrom | 13 | 0,0 | 0 | 2 | no | 19 | 19 | 2013-01-01T00:00:00 | 2016-01-01T16:05:00 |
| ValidTo | 13 | 0,0 | 0 | 1 | no | 27 | 27 | 9999-12-31T23:59:59.9999999 | 9999-12-31T23:59:59.9999999 |

### Application.TransactionTypes_Archive
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| TransactionTypeID | 1 | 0,0 | 0 | 1 | yes | 2 | 2 | 13 | 13 |
| TransactionTypeName | 1 | 0,0 | 0 | 1 | yes | 6 | 6 | | |
| LastEditedBy | 1 | 0,0 | 0 | 1 | yes | 1 | 1 | 9 | 9 |
| ValidFrom | 1 | 0,0 | 0 | 1 | yes | 19 | 19 | 2016-01-01T16:00:00 | 2016-01-01T16:00:00 |
| ValidTo | 1 | 0,0 | 0 | 1 | yes | 19 | 19 | 2016-01-01T16:05:00 | 2016-01-01T16:05:00 |

### Purchasing.PurchaseOrderLines
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| PurchaseOrderLineID | 1000 | 0,0 | 0 | 1000 | yes | 1 | 4 | 1 | 1000 |
| PurchaseOrderID | 1000 | 0,0 | 0 | 248 | no | 1 | 3 | 1 | 248 |
| StockItemID | 1000 | 0,0 | 0 | 219 | no | 1 | 3 | 1 | 219 |
| OrderedOuters | 1000 | 0,0 | 0 | 277 | no | 1 | 3 | 1 | 479 |
| Description | 1000 | 0,0 | 0 | 219 | no | 20 | 85 | | |
| ReceivedOuters | 1000 | 0,0 | 0 | 277 | no | 1 | 3 | 1 | 479 |
| PackageTypeID | 1000 | 0,0 | 0 | 3 | no | 1 | 1 | 6 | 9 |
| ExpectedUnitPricePerOuter | 1000 | 0,0 | 0 | 71 | no | 4 | 7 | 4.50 | 1140.00 |
| LastReceiptDate | 1000 | 0,0 | 0 | 106 | no | 10 | 10 | 2013-01-02 | 2013-05-29 |
| IsOrderLineFinalized | 1000 | 0,0 | 0 | 1 | no | 1 | 1 | 1 | 1 |
| LastEditedBy | 1000 | 0,0 | 0 | 19 | no | 1 | 2 | 2 | 20 |
| LastEditedWhen | 1000 | 0,0 | 0 | 106 | no | 19 | 19 | 2013-01-02T07:00:00 | 2013-05-29T07:00:00 |

### Purchasing.PurchaseOrders
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| PurchaseOrderID | 1000 | 0,0 | 0 | 1000 | yes | 1 | 4 | 1 | 1000 |
| SupplierID | 1000 | 0,0 | 0 | 6 | no | 1 | 2 | 2 | 12 |
| OrderDate | 1000 | 0,0 | 0 | 517 | no | 10 | 10 | 2013-01-01 | 2014-08-29 |
| DeliveryMethodID | 1000 | 0,0 | 0 | 5 | no | 1 | 2 | 2 | 10 |
| ContactPersonID | 1000 | 0,0 | 0 | 1 | no | 1 | 1 | 2 | 2 |
| ExpectedDeliveryDate | 1000 | 0,0 | 0 | 498 | no | 10 | 10 | 2013-01-15 | 2014-09-18 |
| SupplierReference | 1000 | 0,0 | 0 | 6 | no | 6 | 9 | | |
| IsOrderFinalized | 1000 | 0,0 | 0 | 1 | no | 1 | 1 | 1 | 1 |
| Comments | 1000 | 100,0 | 0 | 0 | no | | | | |
| InternalComments | 1000 | 100,0 | 0 | 0 | no | | | | |
| LastEditedBy | 1000 | 0,0 | 0 | 19 | no | 1 | 2 | 2 | 20 |
| LastEditedWhen | 1000 | 0,0 | 0 | 434 | no | 19 | 19 | 2013-01-02T07:00:00 | 2014-09-01T07:00:00 |

### Purchasing.SupplierCategories
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| SupplierCategoryID | 9 | 0,0 | 0 | 9 | yes | 1 | 1 | 1 | 9 |
| SupplierCategoryName | 9 | 0,0 | 0 | 9 | yes | 12 | 27 | | |
| LastEditedBy | 9 | 0,0 | 0 | 2 | no | 1 | 2 | 1 | 16 |
| ValidFrom | 9 | 0,0 | 0 | 2 | no | 19 | 19 | 2013-01-01T00:00:00 | 2015-01-01T16:00:00 |
| ValidTo | 9 | 0,0 | 0 | 1 | no | 27 | 27 | 9999-12-31T23:59:59.9999999 | 9999-12-31T23:59:59.9999999 |

### Purchasing.SupplierCategories_Archive
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| SupplierCategoryID | 1 | 0,0 | 0 | 1 | yes | 1 | 1 | 6 | 6 |
| SupplierCategoryName | 1 | 0,0 | 0 | 1 | yes | 7 | 7 | | |
| LastEditedBy | 1 | 0,0 | 0 | 1 | yes | 1 | 1 | 1 | 1 |
| ValidFrom | 1 | 0,0 | 0 | 1 | yes | 19 | 19 | 2013-01-01T00:00:00 | 2013-01-01T00:00:00 |
| ValidTo | 1 | 0,0 | 0 | 1 | yes | 19 | 19 | 2015-01-01T16:00:00 | 2015-01-01T16:00:00 |

### Purchasing.Suppliers
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| SupplierID | 13 | 0,0 | 0 | 13 | yes | 1 | 2 | 1 | 13 |
| SupplierName | 13 | 0,0 | 0 | 13 | yes | 13 | 24 | | |
| SupplierCategoryID | 13 | 0,0 | 0 | 8 | no | 1 | 1 | 2 | 9 |
| PrimaryContactPersonID | 13 | 0,0 | 0 | 13 | yes | 2 | 2 | 21 | 45 |
| AlternateContactPersonID | 13 | 0,0 | 0 | 13 | yes | 2 | 2 | 22 | 46 |
| DeliveryMethodID | 13 | 30,8 | 0 | 5 | no | 1 | 2 | 2 | 10 |
| DeliveryCityID | 13 | 0,0 | 0 | 12 | no | 4 | 5 | 7899 | 38171 |
| PostalCityID | 13 | 0,0 | 0 | 12 | no | 4 | 5 | 7899 | 38171 |
| SupplierReference | 13 | 0,0 | 0 | 13 | yes | 6 | 11 | | |
| BankAccountName | 13 | 0,0 | 0 | 1 | no | 4 | 4 | | |
| BankAccountBranch | 13 | 0,0 | 0 | 1 | no | 4 | 4 | | |
| BankAccountCode | 13 | 0,0 | 0 | 1 | no | 4 | 4 | | |
| BankAccountNumber | 13 | 0,0 | 0 | 1 | no | 4 | 4 | | |
| BankInternationalCode | 13 | 0,0 | 0 | 1 | no | 4 | 4 | | |
| PaymentDays | 13 | 0,0 | 0 | 3 | no | 1 | 2 | 7 | 30 |
| InternalComments | 13 | 84,6 | 0 | 2 | no | 27 | 54 | | |
| PhoneNumber | 13 | 0,0 | 0 | 13 | yes | 14 | 14 | | |
| FaxNumber | 13 | 0,0 | 0 | 13 | yes | 14 | 14 | | |
| WebsiteURL | 13 | 0,0 | 0 | 13 | yes | 21 | 37 | | |
| DeliveryAddressLine1 | 13 | 0,0 | 4 | 9 | no | 0 | 8 | | |
| DeliveryAddressLine2 | 13 | 0,0 | 0 | 13 | yes | 11 | 26 | | |
| DeliveryPostalCode | 13 | 0,0 | 0 | 12 | no | 5 | 5 | | |
| DeliveryLocation | | | | | no | | | | not sampled (geography) |
| PostalAddressLine1 | 13 | 0,0 | 0 | 13 | yes | 10 | 12 | | |
| PostalAddressLine2 | 13 | 0,0 | 0 | 13 | yes | 6 | 10 | | |
| PostalPostalCode | 13 | 0,0 | 0 | 12 | no | 5 | 5 | | |
| LastEditedBy | 13 | 0,0 | 0 | 1 | no | 1 | 1 | 1 | 1 |
| ValidFrom | 13 | 0,0 | 0 | 1 | no | 19 | 19 | 2013-01-01T00:05:00 | 2013-01-01T00:05:00 |
| ValidTo | 13 | 0,0 | 0 | 1 | no | 27 | 27 | 9999-12-31T23:59:59.9999999 | 9999-12-31T23:59:59.9999999 |

### Purchasing.Suppliers_Archive
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| SupplierID | 13 | 0,0 | 0 | 13 | yes | 1 | 2 | 1 | 13 |
| SupplierName | 13 | 0,0 | 0 | 13 | yes | 13 | 24 | | |
| SupplierCategoryID | 13 | 0,0 | 0 | 8 | no | 1 | 1 | 2 | 9 |
| PrimaryContactPersonID | 13 | 0,0 | 0 | 13 | yes | 2 | 2 | 21 | 45 |
| AlternateContactPersonID | 13 | 0,0 | 0 | 13 | yes | 2 | 2 | 22 | 46 |
| DeliveryMethodID | 13 | 30,8 | 0 | 5 | no | 1 | 2 | 2 | 10 |
| DeliveryCityID | 13 | 0,0 | 0 | 12 | no | 4 | 5 | 7899 | 38171 |
| PostalCityID | 13 | 0,0 | 0 | 12 | no | 4 | 5 | 7899 | 38171 |
| SupplierReference | 13 | 0,0 | 0 | 13 | yes | 6 | 11 | | |
| BankAccountName | 13 | 0,0 | 0 | 1 | no | 4 | 4 | | |
| BankAccountBranch | 13 | 0,0 | 0 | 1 | no | 4 | 4 | | |
| BankAccountCode | 13 | 0,0 | 0 | 1 | no | 4 | 4 | | |
| BankAccountNumber | 13 | 0,0 | 0 | 1 | no | 4 | 4 | | |
| BankInternationalCode | 13 | 0,0 | 0 | 1 | no | 4 | 4 | | |
| PaymentDays | 13 | 0,0 | 0 | 3 | no | 1 | 2 | 7 | 30 |
| InternalComments | 13 | 84,6 | 0 | 2 | no | 27 | 54 | | |
| PhoneNumber | 13 | 0,0 | 0 | 13 | yes | 14 | 14 | | |
| FaxNumber | 13 | 0,0 | 0 | 13 | yes | 14 | 14 | | |
| WebsiteURL | 13 | 0,0 | 0 | 13 | yes | 21 | 37 | | |
| DeliveryAddressLine1 | 13 | 0,0 | 4 | 9 | no | 0 | 8 | | |
| DeliveryAddressLine2 | 13 | 0,0 | 0 | 13 | yes | 11 | 26 | | |
| DeliveryPostalCode | 13 | 0,0 | 0 | 12 | no | 5 | 5 | | |
| DeliveryLocation | | | | | no | | | | not sampled (geography) |
| PostalAddressLine1 | 13 | 0,0 | 0 | 13 | yes | 10 | 12 | | |
| PostalAddressLine2 | 13 | 0,0 | 0 | 13 | yes | 6 | 10 | | |
| PostalPostalCode | 13 | 0,0 | 0 | 12 | no | 5 | 5 | | |
| LastEditedBy | 13 | 0,0 | 0 | 1 | no | 1 | 1 | 1 | 1 |
| ValidFrom | 13 | 0,0 | 0 | 1 | no | 19 | 19 | 2013-01-01T00:00:00 | 2013-01-01T00:00:00 |
| ValidTo | 13 | 0,0 | 0 | 1 | no | 19 | 19 | 2013-01-01T00:05:00 | 2013-01-01T00:05:00 |

### Purchasing.SupplierTransactions
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| SupplierTransactionID | 1000 | 0,0 | 0 | 1000 | yes | 3 | 6 | 134 | 127478 |
| SupplierID | 1000 | 0,0 | 0 | 6 | no | 1 | 2 | 2 | 12 |
| TransactionTypeID | 1000 | 0,0 | 0 | 2 | no | 1 | 1 | 5 | 7 |
| PurchaseOrderID | 1000 | 15,4 | 0 | 846 | no | 1 | 3 | 1 | 846 |
| PaymentMethodID | 1000 | 0,0 | 0 | 1 | no | 1 | 1 | 4 | 4 |
| SupplierInvoiceNumber | 1000 | 15,4 | 0 | 805 | no | 1 | 4 | | |
| TransactionDate | 1000 | 0,0 | 0 | 366 | no | 10 | 10 | 2013-01-02 | 2014-05-28 |
| AmountExcludingTax | 1000 | 0,0 | 0 | 805 | no | 4 | 9 | 0.00 | 591084.00 |
| TaxAmount | 1000 | 0,0 | 0 | 806 | no | 4 | 8 | 0.00 | 88662.60 |
| TransactionAmount | 1000 | 0,0 | 0 | 959 | no | 5 | 11 | -3370601.70 | 679746.60 |
| OutstandingBalance | 1000 | 0,0 | 0 | 1 | no | 4 | 4 | 0.00 | 0.00 |
| FinalizationDate | 1000 | 0,0 | 0 | 74 | no | 10 | 10 | 2013-01-07 | 2014-06-02 |
| IsFinalized | 1000 | 0,0 | 0 | 1 | no | 1 | 1 | 1 | 1 |
| LastEditedBy | 1000 | 0,0 | 0 | 18 | no | 1 | 2 | 2 | 19 |
| LastEditedWhen | 1000 | 0,0 | 0 | 74 | no | 19 | 19 | 2013-01-07T09:00:00 | 2014-06-02T09:00:00 |

### Sales.BuyingGroups
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| BuyingGroupID | 2 | 0,0 | 0 | 2 | yes | 1 | 1 | 1 | 2 |
| BuyingGroupName | 2 | 0,0 | 0 | 2 | yes | 12 | 13 | | |
| LastEditedBy | 2 | 0,0 | 0 | 1 | no | 1 | 1 | 1 | 1 |
| ValidFrom | 2 | 0,0 | 0 | 1 | no | 19 | 19 | 2013-01-01T00:00:00 | 2013-01-01T00:00:00 |
| ValidTo | 2 | 0,0 | 0 | 1 | no | 27 | 27 | 9999-12-31T23:59:59.9999999 | 9999-12-31T23:59:59.9999999 |

### Sales.BuyingGroups_Archive
The table is empty: the measurement sampled 0 rows, so all five columns return no figures.
That is a measured emptiness, not a failed measurement.

### Sales.CustomerCategories
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| CustomerCategoryID | 8 | 0,0 | 0 | 8 | yes | 1 | 1 | 1 | 8 |
| CustomerCategoryName | 8 | 0,0 | 0 | 8 | yes | 5 | 16 | | |
| LastEditedBy | 8 | 0,0 | 0 | 2 | no | 1 | 1 | 1 | 9 |
| ValidFrom | 8 | 0,0 | 0 | 2 | no | 19 | 19 | 2013-01-01T00:00:00 | 2014-01-01T16:15:00 |
| ValidTo | 8 | 0,0 | 0 | 1 | no | 27 | 27 | 9999-12-31T23:59:59.9999999 | 9999-12-31T23:59:59.9999999 |

### Sales.CustomerCategories_Archive
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| CustomerCategoryID | 1 | 0,0 | 0 | 1 | yes | 1 | 1 | 8 | 8 |
| CustomerCategoryName | 1 | 0,0 | 0 | 1 | yes | 8 | 8 | | |
| LastEditedBy | 1 | 0,0 | 0 | 1 | yes | 1 | 1 | 1 | 1 |
| ValidFrom | 1 | 0,0 | 0 | 1 | yes | 19 | 19 | 2014-01-01T16:00:00 | 2014-01-01T16:00:00 |
| ValidTo | 1 | 0,0 | 0 | 1 | yes | 19 | 19 | 2014-01-01T16:15:00 | 2014-01-01T16:15:00 |

### Sales.Customers
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| CustomerID | 664 | 0,0 | 0 | 664 | yes | 1 | 4 | 1 | 1062 |
| CustomerName | 664 | 0,0 | 0 | 664 | yes | 6 | 38 | | |
| BillToCustomerID | 664 | 0,0 | 0 | 264 | no | 1 | 4 | 1 | 1062 |
| CustomerCategoryID | 664 | 0,0 | 0 | 5 | no | 1 | 1 | 3 | 7 |
| BuyingGroupID | 664 | 39,5 | 0 | 2 | no | 1 | 1 | 1 | 2 |
| PrimaryContactPersonID | 664 | 0,0 | 0 | 664 | yes | 4 | 4 | 1001 | 3262 |
| AlternateContactPersonID | 664 | 39,5 | 0 | 402 | no | 4 | 4 | 1002 | 2402 |
| DeliveryMethodID | 664 | 0,0 | 0 | 1 | no | 1 | 1 | 3 | 3 |
| DeliveryCityID | 664 | 0,0 | 0 | 656 | no | 2 | 5 | 15 | 38184 |
| PostalCityID | 664 | 0,0 | 0 | 656 | no | 2 | 5 | 15 | 38184 |
| CreditLimit | 664 | 60,5 | 0 | 61 | no | 7 | 7 | 1100.00 | 4630.50 |
| AccountOpenedDate | 664 | 0,0 | 0 | 63 | no | 10 | 10 | 2013-01-01 | 2026-06-18 |
| StandardDiscountPercentage | 664 | 0,0 | 0 | 1 | no | 5 | 5 | 0.000 | 0.000 |
| IsStatementSent | 664 | 0,0 | 0 | 1 | no | 1 | 1 | 0 | 0 |
| IsOnCreditHold | 664 | 0,0 | 0 | 1 | no | 1 | 1 | 0 | 0 |
| PaymentDays | 664 | 0,0 | 0 | 1 | no | 1 | 1 | 7 | 7 |
| PhoneNumber | 664 | 0,0 | 0 | 49 | no | 14 | 14 | | |
| FaxNumber | 664 | 0,0 | 0 | 49 | no | 14 | 14 | | |
| DeliveryRun | 664 | 9,3 | 602 | 1 | no | 0 | 0 | | |
| RunPosition | 664 | 9,3 | 602 | 1 | no | 0 | 0 | | |
| WebsiteURL | 664 | 0,0 | 0 | 603 | no | 25 | 52 | | |
| DeliveryAddressLine1 | 664 | 0,0 | 0 | 363 | no | 6 | 9 | | |
| DeliveryAddressLine2 | 664 | 0,0 | 0 | 664 | yes | 11 | 26 | | |
| DeliveryPostalCode | 664 | 0,0 | 0 | 454 | no | 5 | 5 | | |
| DeliveryLocation | | | | | no | | | | not sampled (geography) |
| PostalAddressLine1 | 664 | 0,0 | 0 | 645 | no | 9 | 11 | | |
| PostalAddressLine2 | 664 | 0,0 | 0 | 453 | no | 7 | 21 | | |
| PostalPostalCode | 664 | 0,0 | 0 | 454 | no | 5 | 5 | | |
| LastEditedBy | 664 | 0,0 | 0 | 5 | no | 1 | 2 | 1 | 20 |
| ValidFrom | 664 | 0,0 | 0 | 56 | no | 19 | 19 | 2013-01-01T00:00:00 | 2026-07-01T16:00:00 |
| ValidTo | 664 | 0,0 | 0 | 1 | no | 27 | 27 | 9999-12-31T23:59:59.9999999 | 9999-12-31T23:59:59.9999999 |

### Sales.Customers_Archive
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| CustomerID | 70 | 0,0 | 0 | 62 | no | 3 | 4 | 802 | 1055 |
| CustomerName | 70 | 0,0 | 0 | 62 | no | 7 | 23 | | |
| BillToCustomerID | 70 | 0,0 | 0 | 62 | no | 3 | 4 | 802 | 1055 |
| CustomerCategoryID | 70 | 0,0 | 0 | 5 | no | 1 | 1 | 3 | 7 |
| BuyingGroupID | 70 | 100,0 | 0 | 0 | no | | | | |
| PrimaryContactPersonID | 70 | 0,0 | 0 | 62 | no | 4 | 4 | 3002 | 3255 |
| AlternateContactPersonID | 70 | 100,0 | 0 | 0 | no | | | | |
| DeliveryMethodID | 70 | 0,0 | 0 | 1 | no | 1 | 1 | 3 | 3 |
| DeliveryCityID | 70 | 0,0 | 0 | 62 | no | 3 | 5 | 242 | 37884 |
| PostalCityID | 70 | 0,0 | 0 | 62 | no | 3 | 5 | 242 | 37884 |
| CreditLimit | 70 | 0,0 | 0 | 33 | no | 7 | 7 | 1100.00 | 4410.00 |
| AccountOpenedDate | 70 | 0,0 | 0 | 12 | no | 10 | 10 | 2013-01-01 | 2015-11-30 |
| StandardDiscountPercentage | 70 | 0,0 | 0 | 1 | no | 5 | 5 | 0.000 | 0.000 |
| IsStatementSent | 70 | 0,0 | 0 | 1 | no | 1 | 1 | 0 | 0 |
| IsOnCreditHold | 70 | 0,0 | 0 | 1 | no | 1 | 1 | 0 | 0 |
| PaymentDays | 70 | 0,0 | 0 | 1 | no | 1 | 1 | 7 | 7 |
| PhoneNumber | 70 | 0,0 | 0 | 34 | no | 14 | 14 | | |
| FaxNumber | 70 | 0,0 | 0 | 34 | no | 14 | 14 | | |
| DeliveryRun | 70 | 15,7 | 59 | 1 | no | 0 | 0 | | |
| RunPosition | 70 | 15,7 | 59 | 1 | no | 0 | 0 | | |
| WebsiteURL | 70 | 0,0 | 0 | 52 | no | 25 | 48 | | |
| DeliveryAddressLine1 | 70 | 0,0 | 0 | 46 | no | 6 | 8 | | |
| DeliveryAddressLine2 | 70 | 0,0 | 0 | 62 | no | 13 | 25 | | |
| DeliveryPostalCode | 70 | 0,0 | 0 | 59 | no | 5 | 5 | | |
| DeliveryLocation | | | | | no | | | | not sampled (geography) |
| PostalAddressLine1 | 70 | 0,0 | 0 | 62 | no | 9 | 11 | | |
| PostalAddressLine2 | 70 | 0,0 | 0 | 59 | no | 7 | 17 | | |
| PostalPostalCode | 70 | 0,0 | 0 | 59 | no | 5 | 5 | | |
| LastEditedBy | 70 | 0,0 | 0 | 4 | no | 1 | 2 | 1 | 20 |
| ValidFrom | 70 | 0,0 | 0 | 15 | no | 19 | 19 | 2013-01-01T00:00:00 | 2026-07-01T16:00:00 |
| ValidTo | 70 | 0,0 | 0 | 4 | no | 19 | 19 | 2013-07-01T16:00:00 | 2026-07-01T16:00:00 |

### Sales.CustomerTransactions
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| CustomerTransactionID | 1000 | 0,0 | 0 | 1000 | yes | 1 | 4 | 2 | 3581 |
| CustomerID | 1000 | 0,0 | 0 | 126 | no | 1 | 4 | 1 | 1000 |
| TransactionTypeID | 1000 | 0,0 | 0 | 2 | no | 1 | 1 | 1 | 3 |
| InvoiceID | 1000 | 24,0 | 0 | 760 | no | 1 | 3 | 1 | 760 |
| PaymentMethodID | 1000 | 76,0 | 0 | 1 | no | 1 | 1 | 4 | 4 |
| TransactionDate | 1000 | 0,0 | 0 | 15 | no | 10 | 10 | 2013-01-01 | 2013-01-15 |
| AmountExcludingTax | 1000 | 0,0 | 0 | 667 | no | 4 | 8 | 0.00 | 20223.00 |
| TaxAmount | 1000 | 0,0 | 0 | 667 | no | 4 | 7 | 0.00 | 3033.45 |
| TransactionAmount | 1000 | 0,0 | 0 | 897 | no | 5 | 10 | -109813.11 | 23256.45 |
| OutstandingBalance | 1000 | 0,0 | 0 | 1 | no | 4 | 4 | 0.00 | 0.00 |
| FinalizationDate | 1000 | 0,0 | 0 | 12 | no | 10 | 10 | 2013-01-02 | 2013-01-15 |
| IsFinalized | 1000 | 0,0 | 0 | 1 | no | 1 | 1 | 1 | 1 |
| LastEditedBy | 1000 | 0,0 | 0 | 12 | no | 1 | 2 | 2 | 20 |
| LastEditedWhen | 1000 | 0,0 | 0 | 12 | no | 19 | 19 | 2013-01-02T11:30:00 | 2013-01-15T11:30:00 |

### Sales.InvoiceLines
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| InvoiceLineID | 1000 | 0,0 | 0 | 1000 | yes | 1 | 4 | 1 | 1000 |
| InvoiceID | 1000 | 0,0 | 0 | 388 | no | 1 | 3 | 1 | 388 |
| StockItemID | 1000 | 0,0 | 0 | 216 | no | 1 | 3 | 1 | 219 |
| Description | 1000 | 0,0 | 0 | 216 | no | 20 | 85 | | |
| PackageTypeID | 1000 | 0,0 | 0 | 3 | no | 1 | 2 | 7 | 10 |
| Quantity | 1000 | 0,0 | 0 | 52 | no | 1 | 3 | 1 | 288 |
| UnitPrice | 1000 | 0,0 | 0 | 54 | no | 4 | 6 | 0.66 | 345.00 |
| TaxRate | 1000 | 0,0 | 0 | 1 | no | 6 | 6 | 15.000 | 15.000 |
| TaxAmount | 1000 | 0,0 | 0 | 262 | no | 4 | 7 | 1.42 | 1620.00 |
| LineProfit | 1000 | 0,0 | 0 | 285 | no | 4 | 7 | -120.00 | 9200.00 |
| ExtendedPrice | 1000 | 0,0 | 0 | 262 | no | 5 | 8 | 10.87 | 12420.00 |
| LastEditedBy | 1000 | 0,0 | 0 | 6 | no | 1 | 2 | 2 | 20 |
| LastEditedWhen | 1000 | 0,0 | 0 | 6 | no | 19 | 19 | 2013-01-01T12:00:00 | 2013-01-07T12:00:00 |

### Sales.Invoices
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| InvoiceID | 1000 | 0,0 | 0 | 1000 | yes | 1 | 4 | 1 | 1000 |
| CustomerID | 1000 | 0,0 | 0 | 454 | no | 1 | 4 | 2 | 1000 |
| BillToCustomerID | 1000 | 0,0 | 0 | 144 | no | 1 | 4 | 1 | 1000 |
| OrderID | 1000 | 0,0 | 0 | 1000 | yes | 1 | 4 | 1 | 1011 |
| DeliveryMethodID | 1000 | 0,0 | 0 | 1 | no | 1 | 1 | 3 | 3 |
| ContactPersonID | 1000 | 0,0 | 0 | 454 | no | 4 | 4 | 1003 | 3200 |
| AccountsPersonID | 1000 | 0,0 | 0 | 144 | no | 4 | 4 | 1001 | 3200 |
| SalespersonPersonID | 1000 | 0,0 | 0 | 10 | no | 1 | 2 | 2 | 20 |
| PackedByPersonID | 1000 | 0,0 | 0 | 13 | no | 1 | 2 | 2 | 20 |
| InvoiceDate | 1000 | 0,0 | 0 | 16 | no | 10 | 10 | 2013-01-01 | 2013-01-18 |
| CustomerPurchaseOrderNumber | 1000 | 0,0 | 0 | 831 | no | 5 | 5 | | |
| IsCreditNote | 1000 | 0,0 | 0 | 1 | no | 1 | 1 | 0 | 0 |
| CreditNoteReason | 1000 | 100,0 | 0 | 0 | no | | | | |
| Comments | 1000 | 100,0 | 0 | 0 | no | | | | |
| DeliveryInstructions | 1000 | 0,0 | 0 | 454 | no | 21 | 36 | | |
| InternalComments | 1000 | 100,0 | 0 | 0 | no | | | | |
| TotalDryItems | 1000 | 0,0 | 0 | 5 | no | 1 | 1 | 1 | 5 |
| TotalChillerItems | 1000 | 0,0 | 0 | 1 | no | 1 | 1 | 0 | 0 |
| DeliveryRun | 1000 | 0,0 | 1000 | 1 | no | 0 | 0 | | |
| RunPosition | 1000 | 0,0 | 1000 | 1 | no | 0 | 0 | | |
| ReturnedDeliveryData | 1000 | 0,0 | 0 | 1000 | yes | 334 | 367 | | |
| ConfirmedDeliveryTime | 1000 | 0,0 | 0 | 1000 | yes | 19 | 19 | 2013-01-02T07:05:00 | 2013-01-19T11:30:00 |
| ConfirmedReceivedBy | 1000 | 0,0 | 0 | 454 | no | 5 | 27 | | |
| LastEditedBy | 1000 | 0,0 | 0 | 14 | no | 1 | 2 | 3 | 18 |
| LastEditedWhen | 1000 | 0,0 | 0 | 16 | no | 19 | 19 | 2013-01-02T07:00:00 | 2013-01-19T07:00:00 |

### Sales.OrderLines
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| OrderLineID | 1000 | 0,0 | 0 | 1000 | yes | 1 | 4 | 1 | 1000 |
| OrderID | 1000 | 0,0 | 0 | 392 | no | 1 | 3 | 1 | 425 |
| StockItemID | 1000 | 0,0 | 0 | 216 | no | 1 | 3 | 1 | 219 |
| Description | 1000 | 0,0 | 0 | 216 | no | 20 | 85 | | |
| PackageTypeID | 1000 | 0,0 | 0 | 3 | no | 1 | 2 | 7 | 10 |
| Quantity | 1000 | 0,0 | 0 | 52 | no | 1 | 3 | 1 | 288 |
| UnitPrice | 1000 | 0,0 | 0 | 54 | no | 4 | 6 | 0.66 | 345.00 |
| TaxRate | 1000 | 0,0 | 0 | 1 | no | 6 | 6 | 15.000 | 15.000 |
| PickedQuantity | 1000 | 0,0 | 0 | 52 | no | 1 | 3 | 1 | 288 |
| PickingCompletedWhen | 1000 | 0,0 | 0 | 8 | no | 19 | 19 | 2013-01-01T11:00:00 | 2013-01-09T11:00:00 |
| LastEditedBy | 1000 | 0,0 | 0 | 6 | no | 1 | 2 | 3 | 17 |
| LastEditedWhen | 1000 | 0,0 | 0 | 8 | no | 19 | 19 | 2013-01-01T11:00:00 | 2013-01-09T11:00:00 |

### Sales.Orders
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| OrderID | 1000 | 0,0 | 0 | 1000 | yes | 1 | 4 | 1 | 1000 |
| CustomerID | 1000 | 0,0 | 0 | 452 | no | 1 | 4 | 2 | 1000 |
| SalespersonPersonID | 1000 | 0,0 | 0 | 10 | no | 1 | 2 | 2 | 20 |
| PickedByPersonID | 1000 | 15,0 | 0 | 12 | no | 1 | 2 | 3 | 20 |
| ContactPersonID | 1000 | 0,0 | 0 | 452 | no | 4 | 4 | 1003 | 3200 |
| BackorderOrderID | 1000 | 85,4 | 0 | 146 | no | 2 | 4 | 45 | 1037 |
| OrderDate | 1000 | 0,0 | 0 | 16 | no | 10 | 10 | 2013-01-01 | 2013-01-18 |
| ExpectedDeliveryDate | 1000 | 0,0 | 0 | 14 | no | 10 | 10 | 2013-01-02 | 2013-01-21 |
| CustomerPurchaseOrderNumber | 1000 | 0,0 | 0 | 822 | no | 5 | 5 | | |
| IsUndersupplyBackordered | 1000 | 0,0 | 0 | 1 | no | 1 | 1 | 1 | 1 |
| Comments | 1000 | 100,0 | 0 | 0 | no | | | | |
| DeliveryInstructions | 1000 | 100,0 | 0 | 0 | no | | | | |
| InternalComments | 1000 | 100,0 | 0 | 0 | no | | | | |
| PickingCompletedWhen | 1000 | 0,4 | 0 | 36 | no | 19 | 19 | 2013-01-01T11:00:00 | 2013-02-11T11:00:00 |
| LastEditedBy | 1000 | 0,0 | 0 | 16 | no | 1 | 2 | 2 | 20 |
| LastEditedWhen | 1000 | 0,0 | 0 | 36 | no | 19 | 19 | 2013-01-01T11:00:00 | 2013-02-11T11:00:00 |

### Sales.SpecialDeals
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| SpecialDealID | 2 | 0,0 | 0 | 2 | yes | 1 | 1 | 1 | 2 |
| StockItemID | 2 | 100,0 | 0 | 0 | no | | | | |
| CustomerID | 2 | 100,0 | 0 | 0 | no | | | | |
| BuyingGroupID | 2 | 0,0 | 0 | 2 | yes | 1 | 1 | 1 | 2 |
| CustomerCategoryID | 2 | 100,0 | 0 | 0 | no | | | | |
| StockGroupID | 2 | 0,0 | 0 | 1 | no | 1 | 1 | 7 | 7 |
| DealDescription | 2 | 0,0 | 0 | 2 | yes | 23 | 24 | | |
| StartDate | 2 | 0,0 | 0 | 2 | yes | 10 | 10 | 2016-01-01 | 2016-04-01 |
| EndDate | 2 | 0,0 | 0 | 2 | yes | 10 | 10 | 2016-03-31 | 2016-06-30 |
| DiscountAmount | 2 | 100,0 | 0 | 0 | no | | | | |
| DiscountPercentage | 2 | 0,0 | 0 | 2 | yes | 6 | 6 | 10.000 | 15.000 |
| UnitPrice | 2 | 100,0 | 0 | 0 | no | | | | |
| LastEditedBy | 2 | 0,0 | 0 | 1 | no | 1 | 1 | 2 | 2 |
| LastEditedWhen | 2 | 0,0 | 0 | 1 | no | 19 | 19 | 2015-12-31T16:00:00 | 2015-12-31T16:00:00 |

### Warehouse.ColdRoomTemperatures
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| ColdRoomTemperatureID | 3 | 0,0 | 0 | 3 | yes | 7 | 7 | 4076196 | 4076198 |
| ColdRoomSensorNumber | 3 | 0,0 | 0 | 3 | yes | 1 | 1 | 2 | 4 |
| RecordedWhen | 3 | 0,0 | 0 | 1 | no | 19 | 19 | 2026-07-01T14:48:12 | 2026-07-01T14:48:12 |
| Temperature | 3 | 0,0 | 0 | 3 | yes | 4 | 4 | 3.18 | 4.76 |
| ValidFrom | 3 | 0,0 | 0 | 1 | no | 19 | 19 | 2026-07-01T14:48:12 | 2026-07-01T14:48:12 |
| ValidTo | 3 | 0,0 | 0 | 1 | no | 27 | 27 | 9999-12-31T23:59:59.9999999 | 9999-12-31T23:59:59.9999999 |

The identity values run on from the history table: the three current rows carry 4.076.196 to
4.076.198 against 4.076.195 rows in the archive.

### Warehouse.ColdRoomTemperatures_Archive
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| ColdRoomTemperatureID | 1000 | 0,0 | 0 | 1000 | yes | 1 | 4 | 1 | 1000 |
| ColdRoomSensorNumber | 1000 | 0,0 | 0 | 4 | no | 1 | 1 | 1 | 4 |
| RecordedWhen | 1000 | 0,0 | 0 | 250 | no | 19 | 19 | 2015-12-20T00:00:00 | 2015-12-20T01:01:04 |
| Temperature | 1000 | 0,0 | 0 | 200 | no | 4 | 4 | 3.00 | 5.00 |
| ValidFrom | 1000 | 0,0 | 0 | 250 | no | 19 | 19 | 2015-12-20T00:00:00 | 2015-12-20T01:01:04 |
| ValidTo | 1000 | 0,0 | 0 | 250 | no | 19 | 19 | 2015-12-20T00:00:27 | 2015-12-20T01:01:15 |

The first 1000 rows cover 61 minutes of measurements from four sensors. Against 4.076.195 rows
that suggests a very high measurement frequency, but the period the table covers as a whole is
`UNKNOWN` — see the warning at the top of this section.

### Warehouse.Colors
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| ColorID | 36 | 0,0 | 0 | 36 | yes | 1 | 2 | 1 | 36 |
| ColorName | 36 | 0,0 | 0 | 36 | yes | 3 | 11 | | |
| LastEditedBy | 36 | 0,0 | 0 | 2 | no | 1 | 1 | 1 | 9 |
| ValidFrom | 36 | 0,0 | 0 | 2 | no | 19 | 19 | 2013-01-01T00:00:00 | 2016-01-01T16:00:00 |
| ValidTo | 36 | 0,0 | 0 | 1 | no | 27 | 27 | 9999-12-31T23:59:59.9999999 | 9999-12-31T23:59:59.9999999 |

### Warehouse.Colors_Archive
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| ColorID | 1 | 0,0 | 0 | 1 | yes | 2 | 2 | 12 | 12 |
| ColorName | 1 | 0,0 | 0 | 1 | yes | 4 | 4 | | |
| LastEditedBy | 1 | 0,0 | 0 | 1 | yes | 1 | 1 | 1 | 1 |
| ValidFrom | 1 | 0,0 | 0 | 1 | yes | 19 | 19 | 2013-01-01T00:00:00 | 2013-01-01T00:00:00 |
| ValidTo | 1 | 0,0 | 0 | 1 | yes | 19 | 19 | 2016-01-01T16:00:00 | 2016-01-01T16:00:00 |

### Warehouse.PackageTypes
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| PackageTypeID | 14 | 0,0 | 0 | 14 | yes | 1 | 2 | 1 | 14 |
| PackageTypeName | 14 | 0,0 | 0 | 14 | yes | 2 | 6 | | |
| LastEditedBy | 14 | 0,0 | 0 | 1 | no | 1 | 1 | 1 | 1 |
| ValidFrom | 14 | 0,0 | 0 | 1 | no | 19 | 19 | 2013-01-01T00:00:00 | 2013-01-01T00:00:00 |
| ValidTo | 14 | 0,0 | 0 | 1 | no | 27 | 27 | 9999-12-31T23:59:59.9999999 | 9999-12-31T23:59:59.9999999 |

### Warehouse.PackageTypes_Archive
The table is empty: the measurement sampled 0 rows, so all five columns return no figures.

### Warehouse.StockGroups
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| StockGroupID | 10 | 0,0 | 0 | 10 | yes | 1 | 2 | 1 | 10 |
| StockGroupName | 10 | 0,0 | 0 | 10 | yes | 4 | 19 | | |
| LastEditedBy | 10 | 0,0 | 0 | 2 | no | 1 | 1 | 1 | 9 |
| ValidFrom | 10 | 0,0 | 0 | 2 | no | 19 | 19 | 2013-01-01T00:00:00 | 2016-01-01T16:00:00 |
| ValidTo | 10 | 0,0 | 0 | 1 | no | 27 | 27 | 9999-12-31T23:59:59.9999999 | 9999-12-31T23:59:59.9999999 |

### Warehouse.StockGroups_Archive
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| StockGroupID | 1 | 0,0 | 0 | 1 | yes | 1 | 1 | 8 | 8 |
| StockGroupName | 1 | 0,0 | 0 | 1 | yes | 8 | 8 | | |
| LastEditedBy | 1 | 0,0 | 0 | 1 | yes | 1 | 1 | 1 | 1 |
| ValidFrom | 1 | 0,0 | 0 | 1 | yes | 19 | 19 | 2013-01-01T00:00:00 | 2013-01-01T00:00:00 |
| ValidTo | 1 | 0,0 | 0 | 1 | yes | 19 | 19 | 2016-01-01T16:00:00 | 2016-01-01T16:00:00 |

### Warehouse.StockItemHoldings
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| StockItemID | 227 | 0,0 | 0 | 227 | yes | 1 | 3 | 1 | 227 |
| QuantityOnHand | 227 | 0,0 | 0 | 226 | no | 1 | 7 | 0 | 1050769 |
| BinLocation | 227 | 0,0 | 0 | 31 | no | 3 | 4 | | |
| LastStocktakeQuantity | 227 | 0,0 | 0 | 226 | no | 1 | 7 | 1 | 1009444 |
| LastCostPrice | 227 | 0,0 | 0 | 63 | no | 4 | 7 | 0.36 | 1140.00 |
| ReorderLevel | 227 | 0,0 | 0 | 10 | no | 1 | 3 | 1 | 240 |
| TargetStockLevel | 227 | 0,0 | 0 | 13 | no | 1 | 3 | 2 | 500 |
| LastEditedBy | 227 | 0,0 | 0 | 2 | no | 2 | 2 | 18 | 19 |
| LastEditedWhen | 227 | 0,0 | 0 | 2 | no | 19 | 19 | 2026-07-01T07:00:00 | 2026-07-01T12:00:00 |

### Warehouse.StockItems
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| StockItemID | 227 | 0,0 | 0 | 227 | yes | 1 | 3 | 1 | 227 |
| StockItemName | 227 | 0,0 | 0 | 227 | yes | 20 | 85 | | |
| SupplierID | 227 | 0,0 | 0 | 7 | no | 1 | 2 | 1 | 12 |
| ColorID | 227 | 43,6 | 0 | 7 | no | 1 | 2 | 3 | 36 |
| UnitPackageID | 227 | 0,0 | 0 | 4 | no | 1 | 2 | 1 | 10 |
| OuterPackageID | 227 | 0,0 | 0 | 3 | no | 1 | 1 | 6 | 9 |
| Brand | 227 | 92,1 | 0 | 1 | no | 9 | 9 | | |
| Size | 227 | 28,2 | 0 | 43 | no | 1 | 13 | | |
| LeadTimeDays | 227 | 0,0 | 0 | 6 | no | 1 | 2 | 2 | 20 |
| QuantityPerOuter | 227 | 0,0 | 0 | 9 | no | 1 | 2 | 1 | 36 |
| IsChillerStock | 227 | 0,0 | 0 | 2 | no | 1 | 1 | 0 | 1 |
| Barcode | 227 | 96,5 | 0 | 8 | no | 13 | 13 | | |
| TaxRate | 227 | 0,0 | 0 | 2 | no | 6 | 6 | 10.000 | 15.000 |
| UnitPrice | 227 | 0,0 | 0 | 57 | no | 4 | 7 | 0.66 | 1899.00 |
| RecommendedRetailPrice | 227 | 0,0 | 0 | 57 | no | 4 | 7 | 0.99 | 2839.01 |
| TypicalWeightPerUnit | 227 | 0,0 | 0 | 23 | no | 5 | 6 | 0.050 | 21.000 |
| MarketingComments | 227 | 87,7 | 0 | 7 | no | 20 | 63 | | |
| InternalComments | 227 | 100,0 | 0 | 0 | no | | | | |
| Photo | 227 | 100,0 | 0 | 0 | no | | | | |
| CustomFields | 227 | 0,0 | 0 | 21 | no | 47 | 110 | | |
| Tags | 227 | 0,0 | 0 | 13 | no | 2 | 45 | | |
| SearchDetails | 227 | 0,0 | 0 | 227 | yes | 20 | 104 | | |
| LastEditedBy | 227 | 0,0 | 0 | 1 | no | 1 | 1 | 1 | 1 |
| ValidFrom | 227 | 0,0 | 0 | 10 | no | 19 | 19 | 2016-05-31T23:00:00 | 2016-05-31T23:12:00 |
| ValidTo | 227 | 0,0 | 0 | 1 | no | 27 | 27 | 9999-12-31T23:59:59.9999999 | 9999-12-31T23:59:59.9999999 |

### Warehouse.StockItems_Archive
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| StockItemID | 444 | 0,0 | 0 | 227 | no | 1 | 3 | 1 | 227 |
| StockItemName | 444 | 0,0 | 0 | 227 | no | 20 | 85 | | |
| SupplierID | 444 | 0,0 | 0 | 7 | no | 1 | 2 | 1 | 12 |
| ColorID | 444 | 47,7 | 0 | 7 | no | 1 | 2 | 3 | 36 |
| UnitPackageID | 444 | 0,0 | 0 | 4 | no | 1 | 2 | 1 | 10 |
| OuterPackageID | 444 | 0,0 | 0 | 3 | no | 1 | 1 | 6 | 9 |
| Brand | 444 | 89,0 | 0 | 1 | no | 9 | 9 | | |
| Size | 444 | 31,3 | 0 | 43 | no | 1 | 13 | | |
| LeadTimeDays | 444 | 0,0 | 0 | 6 | no | 1 | 2 | 2 | 20 |
| QuantityPerOuter | 444 | 0,0 | 0 | 9 | no | 1 | 2 | 1 | 36 |
| IsChillerStock | 444 | 0,0 | 0 | 2 | no | 1 | 1 | 0 | 1 |
| Barcode | 444 | 98,2 | 0 | 8 | no | 13 | 13 | | |
| TaxRate | 444 | 0,0 | 0 | 2 | no | 6 | 6 | 10.000 | 15.000 |
| UnitPrice | 444 | 0,0 | 0 | 57 | no | 4 | 7 | 0.66 | 1899.00 |
| RecommendedRetailPrice | 444 | 0,0 | 0 | 57 | no | 4 | 7 | 0.99 | 2839.01 |
| TypicalWeightPerUnit | 444 | 0,0 | 0 | 23 | no | 5 | 6 | 0.050 | 21.000 |
| MarketingComments | 444 | 87,2 | 0 | 7 | no | 20 | 63 | | |
| InternalComments | 444 | 100,0 | 0 | 0 | no | | | | |
| Photo | 444 | 100,0 | 0 | 0 | no | | | | |
| CustomFields | 444 | 51,1 | 0 | 14 | no | 47 | 100 | | |
| Tags | 444 | 51,1 | 0 | 7 | no | 2 | 35 | | |
| SearchDetails | 444 | 0,0 | 0 | 227 | no | 20 | 104 | | |
| LastEditedBy | 444 | 0,0 | 0 | 1 | no | 1 | 1 | 1 | 1 |
| ValidFrom | 444 | 0,0 | 0 | 11 | no | 19 | 19 | 2013-01-01T00:00:00 | 2016-05-31T23:09:00 |
| ValidTo | 444 | 0,0 | 0 | 13 | no | 19 | 19 | 2016-05-31T23:00:00 | 2016-05-31T23:12:00 |

### Warehouse.StockItemStockGroups
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| StockItemStockGroupID | 442 | 0,0 | 0 | 442 | yes | 1 | 3 | 1 | 442 |
| StockItemID | 442 | 0,0 | 0 | 227 | no | 1 | 3 | 1 | 227 |
| StockGroupID | 442 | 0,0 | 0 | 9 | no | 1 | 2 | 1 | 10 |
| LastEditedBy | 442 | 0,0 | 0 | 1 | no | 1 | 1 | 1 | 1 |
| LastEditedWhen | 442 | 0,0 | 0 | 5 | no | 19 | 19 | 2013-01-01T00:00:00 | 2016-01-05T00:00:00 |

### Warehouse.StockItemTransactions
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| StockItemTransactionID | 1000 | 0,0 | 0 | 1000 | yes | 1 | 4 | 1 | 1465 |
| StockItemID | 1000 | 0,0 | 0 | 217 | no | 1 | 3 | 1 | 219 |
| TransactionTypeID | 1000 | 0,0 | 0 | 2 | no | 2 | 2 | 10 | 11 |
| CustomerID | 1000 | 20,1 | 0 | 192 | no | 1 | 4 | 2 | 1000 |
| InvoiceID | 1000 | 20,1 | 0 | 319 | no | 1 | 3 | 1 | 319 |
| SupplierID | 1000 | 79,9 | 0 | 6 | no | 1 | 2 | 2 | 12 |
| PurchaseOrderID | 1000 | 79,9 | 0 | 25 | no | 1 | 2 | 1 | 25 |
| TransactionOccurredWhen | 1000 | 0,0 | 0 | 10 | no | 19 | 19 | 2013-01-01T12:00:00 | 2013-01-07T12:00:00 |
| Quantity | 1000 | 0,0 | 0 | 139 | no | 5 | 8 | -288.000 | 575.000 |
| LastEditedBy | 1000 | 0,0 | 0 | 9 | no | 1 | 2 | 2 | 20 |
| LastEditedWhen | 1000 | 0,0 | 0 | 10 | no | 19 | 19 | 2013-01-01T12:00:00 | 2013-01-07T12:00:00 |

The customer and supplier sides are complementary: `CustomerID` and `InvoiceID` are empty in
20,1% of the sample, `SupplierID` and `PurchaseOrderID` in 79,9% — together exactly 100%. Every
movement is either inbound or outbound, never both.

### Warehouse.VehicleTemperatures
| Column | Sampled | Null % | Blank | Distinct | Unique? | Min len | Max len | Min | Max |
|---|---|---|---|---|---|---|---|---|---|
| VehicleTemperatureID | 1000 | 0,0 | 0 | 1000 | yes | 1 | 4 | 1 | 1000 |
| VehicleRegistration | 1000 | 0,0 | 0 | 1 | no | 9 | 9 | | |
| ChillerSensorNumber | 1000 | 0,0 | 0 | 2 | no | 1 | 1 | 1 | 2 |
| RecordedWhen | 1000 | 0,0 | 0 | 500 | no | 19 | 19 | 2016-01-01T07:00:00 | 2016-01-03T10:04:30 |
| Temperature | 1000 | 0,0 | 0 | 200 | no | 4 | 4 | 3.00 | 5.00 |
| IsCompressed | 1000 | 0,0 | 0 | 1 | no | 1 | 1 | 0 | 0 |
| FullSensorData | 1000 | 0,0 | 0 | 1000 | yes | 195 | 196 | | |
| CompressedSensorData | 1000 | 100,0 | 0 | 0 | no | | | | |

`IsCompressed` is 0 throughout the sample and `CompressedSensorData` is entirely empty, while
`FullSensorData` is filled in every row. Whether that holds beyond the first 1000 rows is
`UNKNOWN`.

### The three views in Website
The measurement does not profile views by default; these were measured separately with the
view option switched on. Their columns are listed under *Columns per Table*. They carry no keys
and no constraints.

## Watermark Candidates

De keuze is per tabel bijna vanzelfsprekend, omdat elke tabel precies één wijzigingsstempel
draagt. Alle genoemde kolommen zijn in de meting 0% leeg.

| Tabel | Kolom | Type | Aanbeveling |
|---|---|---|---|
| Application.Cities | ValidFrom | datetime2(7) | geschikt |
| Application.Cities_Archive | ValidTo | datetime2(7) | geschikt — een archiefrij ontstaat op het moment dat de versie sluit |
| Application.Countries | ValidFrom | datetime2(7) | geschikt |
| Application.Countries_Archive | ValidTo | datetime2(7) | geschikt |
| Application.DeliveryMethods | ValidFrom | datetime2(7) | geschikt; tabel is klein genoeg voor een volledige verversing |
| Application.DeliveryMethods_Archive | ValidTo | datetime2(7) | geschikt; 1 rij |
| Application.PaymentMethods | ValidFrom | datetime2(7) | geschikt; 4 rijen |
| Application.PaymentMethods_Archive | ValidTo | datetime2(7) | geschikt; 1 rij |
| Application.People | ValidFrom | datetime2(7) | geschikt |
| Application.People_Archive | ValidTo | datetime2(7) | geschikt |
| Application.StateProvinces | ValidFrom | datetime2(7) | geschikt |
| Application.StateProvinces_Archive | ValidTo | datetime2(7) | geschikt |
| Application.SystemParameters | LastEditedWhen | datetime2(7) | geschikt; 1 rij, volledige verversing ligt meer voor de hand |
| Application.TransactionTypes | ValidFrom | datetime2(7) | geschikt; 13 rijen |
| Application.TransactionTypes_Archive | ValidTo | datetime2(7) | geschikt; 1 rij |
| Purchasing.PurchaseOrderLines | LastEditedWhen | datetime2(7) | geschikt |
| Purchasing.PurchaseOrders | LastEditedWhen | datetime2(7) | geschikt |
| Purchasing.SupplierCategories | ValidFrom | datetime2(7) | geschikt; 9 rijen |
| Purchasing.SupplierCategories_Archive | ValidTo | datetime2(7) | geschikt; 1 rij |
| Purchasing.Suppliers | ValidFrom | datetime2(7) | geschikt; 13 rijen |
| Purchasing.Suppliers_Archive | ValidTo | datetime2(7) | geschikt; 13 rijen |
| Purchasing.SupplierTransactions | LastEditedWhen | datetime2(7) | geschikt |
| Sales.BuyingGroups | ValidFrom | datetime2(7) | geschikt; 2 rijen |
| Sales.BuyingGroups_Archive | ValidTo | datetime2(7) | tabel is leeg; niets te bepalen |
| Sales.CustomerCategories | ValidFrom | datetime2(7) | geschikt; 8 rijen |
| Sales.CustomerCategories_Archive | ValidTo | datetime2(7) | geschikt; 1 rij |
| Sales.Customers | ValidFrom | datetime2(7) | geschikt |
| Sales.Customers_Archive | ValidTo | datetime2(7) | geschikt |
| Sales.CustomerTransactions | LastEditedWhen | datetime2(7) | geschikt |
| Sales.InvoiceLines | LastEditedWhen | datetime2(7) | geschikt |
| Sales.Invoices | LastEditedWhen | datetime2(7) | geschikt |
| Sales.OrderLines | LastEditedWhen | datetime2(7) | geschikt |
| Sales.Orders | LastEditedWhen | datetime2(7) | geschikt |
| Sales.SpecialDeals | LastEditedWhen | datetime2(7) | geschikt; 2 rijen |
| Warehouse.ColdRoomTemperatures | ValidFrom | datetime2(7) | geschikt; slechts 3 actuele rijen |
| Warehouse.ColdRoomTemperatures_Archive | ValidTo | datetime2(7) | geschikt, en noodzakelijk: 4 miljoen rijen zijn niet elke run volledig op te halen |
| Warehouse.Colors | ValidFrom | datetime2(7) | geschikt; 36 rijen |
| Warehouse.Colors_Archive | ValidTo | datetime2(7) | geschikt; 1 rij |
| Warehouse.PackageTypes | ValidFrom | datetime2(7) | geschikt; 14 rijen |
| Warehouse.PackageTypes_Archive | ValidTo | datetime2(7) | tabel is leeg; niets te bepalen |
| Warehouse.StockGroups | ValidFrom | datetime2(7) | geschikt; 10 rijen |
| Warehouse.StockGroups_Archive | ValidTo | datetime2(7) | geschikt; 1 rij |
| Warehouse.StockItemHoldings | LastEditedWhen | datetime2(7) | geschikt; 227 rijen, maar zie de waarschuwing bij *stand of gebeurtenis* |
| Warehouse.StockItems | ValidFrom | datetime2(7) | geschikt; 227 rijen |
| Warehouse.StockItems_Archive | ValidTo | datetime2(7) | geschikt |
| Warehouse.StockItemStockGroups | LastEditedWhen | datetime2(7) | geschikt; 442 rijen |
| Warehouse.StockItemTransactions | LastEditedWhen | datetime2(7) | geschikt; `TransactionOccurredWhen` is de gebeurtenisdatum en niet het wijzigingsmoment |
| Warehouse.VehicleTemperatures | RecordedWhen | datetime2(7) | enige kandidaat — deze tabel heeft geen `LastEditedWhen` en geen historietabel |

**Twee waarschuwingen bij deze tabel.**

**De bovengrens per kolom is niet gemeten.** De meting leest de eerste 1000 rijen per tabel
zonder sortering, dus de datums onder *Column Shape* zijn de vorm van die eerste rijen en niet
het bereik van de tabel. Voor elke tabel groter dan 1000 rijen is de werkelijke hoogste waarde
`UNKNOWN`. Dat raakt de inrichting: een startvenster dat op die getallen wordt gebaseerd, is
gebaseerd op een steekproef die er als een bereik uitziet. Bepaal het venster op de gelande
Bronze-data, niet op dit rapport.

**Let op het verschil tussen de gebeurtenisdatum en het wijzigingsmoment.** Tabellen dragen
vaak allebei: `Sales.Orders` heeft `OrderDate` (wanneer de order werd geplaatst) én
`LastEditedWhen` (wanneer de rij voor het laatst veranderde), `Warehouse.StockItemTransactions`
heeft `TransactionOccurredWhen` én `LastEditedWhen`. Voor het oppikken van wijzigingen is alleen
de tweede bruikbaar; de eerste hoort in het datamodel thuis als businessdatum.

## Key Data Characteristics

De 48 tabellen vallen in vier patronen. Per patroon geldt hetzelfde antwoord, dus die staan
hieronder één keer uitgeschreven; daarna volgt per tabel de specifieke invulling.

**Patroon A — basistabel met historie (16 tabellen).** Natuurlijke sleutel is de enkelvoudige
primaire sleutel. Watermark is `ValidFrom`. Incrementeel laden is mogelijk. Verwijderingen zijn
niet uit de tabel zelf af te leiden: een verwijderde rij verdwijnt uit de basistabel en de
laatste versie ervan verhuist naar de historietabel. Wie verwijderingen wil detecteren, kan dat
met een volledige verversing of door de historietabel te vergelijken.

**Patroon B — historietabel (16 tabellen).** Geen sleutel, geen constraints. Een rij is een
afgesloten versie van een rij uit de basistabel; de natuurlijke sleutel is de sleutel van de
basistabel plus `ValidFrom`. Rijen worden alleen toegevoegd, nooit gewijzigd, dus incrementeel
laden op `ValidTo` is veilig en een volledige verversing is niet nodig.

**Patroon C — transactietabel zonder historie (13 tabellen).** Enkelvoudige primaire sleutel,
`LastEditedWhen` als watermark. Rijen kunnen worden bijgewerkt na aanmaak, dus incrementeel
laden pikt zowel nieuwe als gewijzigde rijen op. Verwijderingen zijn niet detecteerbaar zonder
volledige verversing.

**Patroon D — telemetrie (3 tabellen).** `Warehouse.VehicleTemperatures` en de twee
`ColdRoomTemperatures`-tabellen. Metingen worden alleen toegevoegd; het volume is een orde van
grootte groter dan de rest van de database.

| Tabel | Patroon | Natuurlijke sleutel | Watermark | Incrementeel | Volledige verversing nodig voor verwijderingen |
|---|---|---|---|---|---|
| Application.Cities | A | CityID | ValidFrom | ja | ja |
| Application.Cities_Archive | B | CityID + ValidFrom | ValidTo | ja | nee |
| Application.Countries | A | CountryID | ValidFrom | ja | ja |
| Application.Countries_Archive | B | CountryID + ValidFrom | ValidTo | ja | nee |
| Application.DeliveryMethods | A | DeliveryMethodID | ValidFrom | onnodig — 10 rijen | ja |
| Application.DeliveryMethods_Archive | B | DeliveryMethodID + ValidFrom | ValidTo | onnodig | nee |
| Application.PaymentMethods | A | PaymentMethodID | ValidFrom | onnodig — 4 rijen | ja |
| Application.PaymentMethods_Archive | B | PaymentMethodID + ValidFrom | ValidTo | onnodig | nee |
| Application.People | A | PersonID | ValidFrom | ja | ja |
| Application.People_Archive | B | PersonID + ValidFrom | ValidTo | ja | nee |
| Application.StateProvinces | A | StateProvinceID | ValidFrom | onnodig — 53 rijen | ja |
| Application.StateProvinces_Archive | B | StateProvinceID + ValidFrom | ValidTo | onnodig | nee |
| Application.SystemParameters | C | SystemParameterID | LastEditedWhen | onnodig — 1 rij | n.v.t. |
| Application.TransactionTypes | A | TransactionTypeID | ValidFrom | onnodig — 13 rijen | ja |
| Application.TransactionTypes_Archive | B | TransactionTypeID + ValidFrom | ValidTo | onnodig | nee |
| Purchasing.PurchaseOrderLines | C | PurchaseOrderLineID | LastEditedWhen | ja | ja |
| Purchasing.PurchaseOrders | C | PurchaseOrderID | LastEditedWhen | ja | ja |
| Purchasing.SupplierCategories | A | SupplierCategoryID | ValidFrom | onnodig — 9 rijen | ja |
| Purchasing.SupplierCategories_Archive | B | SupplierCategoryID + ValidFrom | ValidTo | onnodig | nee |
| Purchasing.Suppliers | A | SupplierID | ValidFrom | onnodig — 13 rijen | ja |
| Purchasing.Suppliers_Archive | B | SupplierID + ValidFrom | ValidTo | onnodig | nee |
| Purchasing.SupplierTransactions | C | SupplierTransactionID | LastEditedWhen | ja | ja |
| Sales.BuyingGroups | A | BuyingGroupID | ValidFrom | onnodig — 2 rijen | ja |
| Sales.BuyingGroups_Archive | B | BuyingGroupID + ValidFrom | ValidTo | leeg | nee |
| Sales.CustomerCategories | A | CustomerCategoryID | ValidFrom | onnodig — 8 rijen | ja |
| Sales.CustomerCategories_Archive | B | CustomerCategoryID + ValidFrom | ValidTo | onnodig | nee |
| Sales.Customers | A | CustomerID | ValidFrom | ja | ja |
| Sales.Customers_Archive | B | CustomerID + ValidFrom | ValidTo | ja | nee |
| Sales.CustomerTransactions | C | CustomerTransactionID | LastEditedWhen | ja | ja |
| Sales.InvoiceLines | C | InvoiceLineID | LastEditedWhen | ja | ja |
| Sales.Invoices | C | InvoiceID | LastEditedWhen | ja | ja |
| Sales.OrderLines | C | OrderLineID | LastEditedWhen | ja | ja |
| Sales.Orders | C | OrderID | LastEditedWhen | ja | ja |
| Sales.SpecialDeals | C | SpecialDealID | LastEditedWhen | onnodig — 2 rijen | ja |
| Warehouse.ColdRoomTemperatures | D/A | ColdRoomTemperatureID | ValidFrom | onnodig — 3 rijen | nee |
| Warehouse.ColdRoomTemperatures_Archive | D/B | ColdRoomTemperatureID + ValidFrom | ValidTo | **ja, noodzakelijk** | nee |
| Warehouse.Colors | A | ColorID | ValidFrom | onnodig — 36 rijen | ja |
| Warehouse.Colors_Archive | B | ColorID + ValidFrom | ValidTo | onnodig | nee |
| Warehouse.PackageTypes | A | PackageTypeID | ValidFrom | onnodig — 14 rijen | ja |
| Warehouse.PackageTypes_Archive | B | PackageTypeID + ValidFrom | ValidTo | leeg | nee |
| Warehouse.StockGroups | A | StockGroupID | ValidFrom | onnodig — 10 rijen | ja |
| Warehouse.StockGroups_Archive | B | StockGroupID + ValidFrom | ValidTo | onnodig | nee |
| Warehouse.StockItemHoldings | C | StockItemID | LastEditedWhen | onnodig — 227 rijen | nee |
| Warehouse.StockItems | A | StockItemID | ValidFrom | onnodig — 227 rijen | ja |
| Warehouse.StockItems_Archive | B | StockItemID + ValidFrom | ValidTo | onnodig | nee |
| Warehouse.StockItemStockGroups | C | StockItemID + StockGroupID | LastEditedWhen | onnodig — 442 rijen | ja |
| Warehouse.StockItemTransactions | C | StockItemTransactionID | LastEditedWhen | ja | ja |
| Warehouse.VehicleTemperatures | D | VehicleTemperatureID | RecordedWhen | ja | nee |

### Geschat volume en groei

De meting geeft een momentopname, geen groei over tijd. Groei per dag is dus `UNKNOWN`. Wat wel
vaststaat is de verhouding: `Warehouse.ColdRoomTemperatures_Archive` is met 4.076.195 rijen en
295 MB groter dan alle andere 47 tabellen samen. De vier zwaarste tabellen daarnaast —
`Sales.OrderLines`, `Sales.InvoiceLines`, `Warehouse.StockItemTransactions` en
`Sales.CustomerTransactions` — liggen elk rond de 100.000 tot 240.000 rijen.

### Partitiekandidaten

Voor de vier grote transactietabellen ligt de businessdatum voor de hand
(`Sales.Orders.OrderDate`, `Sales.Invoices.InvoiceDate`,
`Warehouse.StockItemTransactions.TransactionOccurredWhen`,
`Sales.CustomerTransactions.TransactionDate`). Voor de telemetrie is dat `RecordedWhen`. De
overige tabellen zijn te klein om partitionering te rechtvaardigen. Dit is een aanwijzing op
basis van de vorm, geen meting van de spreiding — die is pas op Bronze te doen.

### Numerieke kolommen — stand of gebeurtenis

Dit is de vraag die de granulariteit van Silver bepaalt en die achteraf niet meer te corrigeren
is. Een stand overschrijft de bron; een gebeurtenis wordt één keer geschreven en verandert
daarna niet meer.

**Gebeurtenissen — geschreven bij het ontstaan van de rij, daarna ongewijzigd:**
`Sales.OrderLines.Quantity`, `UnitPrice`, `TaxRate`; `Sales.InvoiceLines.Quantity`,
`UnitPrice`, `TaxAmount`, `LineProfit`, `ExtendedPrice`;
`Warehouse.StockItemTransactions.Quantity` (een mutatie, positief of negatief);
`Sales.CustomerTransactions` en `Purchasing.SupplierTransactions` — `AmountExcludingTax`,
`TaxAmount`, `TransactionAmount`. Deze tellen op over rijen, niet over tijd.

**Standen — de bron overschrijft ze, en of de vorige waarde bewaard blijft verschilt per
tabel:**

| Kolom | Wat het is | Blijft de waardehistorie bewaard? |
|---|---|---|
| `Warehouse.StockItemHoldings.QuantityOnHand` | actuele voorraad per artikel | **Nee** — `StockItemHoldings` heeft geen historietabel. De waarde is wel te reconstrueren uit `Warehouse.StockItemTransactions`, dat elke mutatie vastlegt |
| `Warehouse.StockItemHoldings.LastStocktakeQuantity`, `LastCostPrice`, `ReorderLevel`, `TargetStockLevel` | instellingen en laatste telling per artikel | **Nee** — zelfde tabel, geen historie, en hiervoor bestaat geen mutatieadministratie |
| `Warehouse.StockItems.UnitPrice`, `RecommendedRetailPrice`, `TaxRate` | actuele prijzen | **Ja** — `StockItems_Archive` bewaart elke eerdere versie met haar geldigheidsperiode |
| `Sales.Customers.CreditLimit`, `IsOnCreditHold`, `PaymentDays`, `StandardDiscountPercentage` | kredietafspraken per klant | **Ja** — `Customers_Archive` bewaart elke eerdere versie |
| `Purchasing.Suppliers.PaymentDays` | betaaltermijn per leverancier | **Ja** — `Suppliers_Archive` |
| `Purchasing.PurchaseOrderLines.ReceivedOuters` | lopend totaal van wat er is ontvangen op deze regel | **Nee** — geen historietabel, en het is geen mutatie maar een bijgewerkt totaal. Wat er bij een eerdere deellevering stond, is weg |
| `Sales.OrderLines.PickedQuantity` | lopend totaal van wat er is gepickt | **Nee** — zelfde als hierboven |
| `Sales.CustomerTransactions.OutstandingBalance` en `Purchasing.SupplierTransactions.OutstandingBalance` | openstaand saldo per transactie | **Nee.** In de gemeten steekproef staat deze kolom overal op `0.00`; of dat in de hele tabel zo is, is `UNKNOWN` |

**De twee lopende totalen verdienen aandacht bij het modelleren.** `ReceivedOuters` en
`PickedQuantity` zien er in een kolommenlijst uit als aantallen, maar ze tellen op over de tijd
binnen dezelfde rij. Wie ze optelt over regels telt daarmee door de tijd heen op, en dat levert
een getal op dat nergens op slaat. `Warehouse.StockItemTransactions.Quantity` is het
tegenovergestelde: een echte mutatie die wél optelbaar is.

## Open Questions / UNKNOWNs

1. **Zijn de basistabellen daadwerkelijk systeem-geversioneerd, en is de koppeling naar de
   `_Archive`-tabel die wij aannemen ook de koppeling die de database kent?** Het patroon is
   sterk (identieke kolomlijsten, geen sleutels op de archieftabellen, `ValidTo` op de
   maximumwaarde in elke actuele rij), maar de meting leest die eigenschap niet uit. Te
   beantwoorden door de databasebeheerder, of door het systeemkenmerk alsnog uit te lezen.
2. **Wat is het werkelijke bereik van elke datumkolom?** Alles onder *Column Shape* komt uit de
   eerste 1000 rijen per tabel. Voor elke tabel groter dan dat is de hoogste waarde `UNKNOWN`.
   Te beantwoorden op de gelande Bronze-data.
3. **Hoe vaak verandert de bron, en hoe snel groeit hij?** Eén meting geeft geen groei. Hoe vaak
   er opgehaald moet worden is daarmee `UNKNOWN` en een afspraak met de klant, geen eigenschap
   van de database.
4. **Moet de temperatuurtelemetrie mee?** `Warehouse.ColdRoomTemperatures_Archive` (4 miljoen
   rijen, 295 MB) en `Warehouse.VehicleTemperatures` (74.710 rijen) zijn sensordata met een heel
   ander karakter en volume dan de rest. Ze meenemen vervijfvoudigt het volume van de bron.
   Dit is een vraag aan de klant.
5. **Mogen de persoonsgegevens in `Application.People` mee, en zo ja welke?** De tabel bevat
   naam, e-mailadres, telefoonnummer en `HashedPassword`. Dat laatste is inloggegevens en hoort
   niet in een datawarehouse thuis; wij stellen voor die kolom niet op te halen. Voor de overige
   persoonsgegevens is een keuze nodig.
6. **Mogen de bankgegevens in `Purchasing.Suppliers` mee?** Vijf kolommen
   (`BankAccountName`, `BankAccountBranch`, `BankAccountCode`, `BankAccountNumber`,
   `BankInternationalCode`) bevatten betaalgegevens van leveranciers. Ze staan ook in
   `Suppliers_Archive`.
7. **Wat betekent `OutstandingBalance` als hij overal `0.00` is?** In beide transactietabellen
   staat de kolom in de hele steekproef op nul. Of dat betekent dat alles is afgeletterd, of dat
   de kolom niet wordt gebruikt, is `UNKNOWN`.
8. **Zijn de elf `geography`-kolommen nodig?** Ze bevatten locaties en landsgrenzen, worden door
   de meting niet bemonsterd, en vragen bij het ophalen om een conversie. Als er geen
   kaartvraagstuk ligt, is ze weglaten de eenvoudigste keuze.
9. **Wat is het gewenste gedrag bij een gepauzeerde database?** De bron slaapt na 60 minuten in.
   Of het ophaalproces mag wachten op het opstarten, of dat de run dan opnieuw moet worden
   ingepland, is een keuze.
