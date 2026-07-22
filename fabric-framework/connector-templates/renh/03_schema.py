from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType,
    IntegerType, BooleanType, ArrayType, LongType
)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# SCHEMAS â€” StructType for spark.read.schema()
# Only entities that need explicit schema inference are listed here.
# Most flat entities use schema-on-read; schemas here are for nested/complex types.
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

entity_schema_config = {

    "departments": StructType([
        StructField("TblAfdelingnr", IntegerType(), True),
        StructField("Omschrijving",  StringType(),  True),
        StructField("Emailadres",    StringType(),  True),
        StructField("Grootboeknr",   StringType(),  True),
    ]),

    "maingroups": StructType([
        StructField("TblHoofdgroepnr",            IntegerType(), True),
        StructField("Omschrijving",                StringType(),  True),
        StructField("BestelFormule",               StringType(),  True),
        StructField("VoorstelBestellingBerekenen", BooleanType(), True),
        StructField("Grootboeknummer",             StringType(),  True),
    ]),

    "subgroups": StructType([
        StructField("TblSubgroepnr",                    IntegerType(), True),
        StructField("Omschrijving",                      StringType(),  True),
        StructField("TblAfdelingnr",                    IntegerType(), True),
        StructField("TblHoofdgroepnr",                  IntegerType(), True),
        StructField("NietMeeDoenBestellingen",          BooleanType(), True),
        StructField("NietMeeDoenDebiteurenRapport",     BooleanType(), True),
        StructField("NietMeeDoenVoorraad",              BooleanType(), True),
        StructField("BrutoWinstPercentage",             DoubleType(),  True),
        StructField("Leeftijdgrens",                    IntegerType(), True),
        StructField("BoekingsTekst",                    StringType(),  True),
        StructField("ExternePrinter",                   IntegerType(), True),
        StructField("TypeOrderbon",                     IntegerType(), True),
        StructField("PrintVolgorde",                    IntegerType(), True),
        StructField("TblHorecaGroepenID",               IntegerType(), True),
        StructField("TblGangenID",                      IntegerType(), True),
        StructField("DezeGroepNaarWeegschaalBijMix",    BooleanType(), True),
        StructField("DezeGroepNietTonenInOmzet",        BooleanType(), True),
    ]),

    "turnover_types": StructType([
        StructField("TblSoortOmzetnr",                  IntegerType(), True),
        StructField("SoortOmzetomschrijving",            StringType(),  True),
        StructField("ZienAlsDerving",                    BooleanType(), True),
        StructField("JournaliserenAls",                  IntegerType(), True),
        StructField("GrootBoekSluitregel",               StringType(),  True),
        StructField("GrootboekVerkoopkosten",            StringType(),  True),
        StructField("GrootboekDebet",                    StringType(),  True),
        StructField("GrootboekCredit",                   StringType(),  True),
        StructField("AantallenAlsNegatiefBehandelen",   BooleanType(), True),
        StructField("NaarWinkel",                        IntegerType(), True),
    ]),

    "shops": StructType([
        StructField("TblWinkelnr",                   IntegerType(), True),
        StructField("Omschrijving",                   StringType(),  True),
        StructField("Adres",                          StringType(),  True),
        StructField("PC",                             StringType(),  True),
        StructField("Plaats",                         StringType(),  True),
        StructField("LandCodeISO2",                  StringType(),  True),
        StructField("AdministratieCode",             StringType(),  True),
        StructField("DagOmzetExclBtw",               DoubleType(),  True),
        StructField("TonenOpKaart",                  BooleanType(), True),
        StructField("Lattitude",                     DoubleType(),  True),
        StructField("Longitude",                     DoubleType(),  True),
        StructField("Emailadres",                    StringType(),  True),
        StructField("Telefoon",                      StringType(),  True),
        StructField("Mobiel",                        StringType(),  True),
        StructField("BICcode",                       StringType(),  True),
        StructField("IBAN",                          StringType(),  True),
        StructField("BtwNr",                         StringType(),  True),
        StructField("DivisionCodeExactOnline",       StringType(),  True),
        StructField("DatumLaatsteSynchronisatie",    StringType(),  True),
        StructField("ArtikelenMuterenIsToegestaan",  BooleanType(), True),
    ]),

    "cash_registers": StructType([
        StructField("TblWinkelsnr",                  IntegerType(), True),
        StructField("TblKassanr",                    IntegerType(), True),
        StructField("Omschrijving",                  StringType(),  True),
        StructField("LaatsteDatumGesynchroniseerd", StringType(),  True),
        StructField("KassaZonderladen",              BooleanType(), True),
        StructField("KassaMetVasteLade",             IntegerType(), True),
        StructField("NietMeerActief",                BooleanType(), True),
        StructField("LaatstStartDatum",              StringType(),  True),
        StructField("LaatsteStopDatum",              StringType(),  True),
        StructField("IsHorecaKassa",                 BooleanType(), True),
        StructField("GebruikMettlerAPI",             BooleanType(), True),
        StructField("PingTimeout",                   IntegerType(), True),
        StructField("Groep",                         IntegerType(), True),
    ]),

    "day_turnover": StructType([
        StructField("Transaction", StructType([
            StructField("branch",         IntegerType(), True),
            StructField("register",       IntegerType(), True),
            StructField("billno",         StringType(),  True),
            StructField("cashier",        IntegerType(), True),
            StructField("custno",         IntegerType(), True),
            StructField("custname",       StringType(),  True),
            StructField("time",           StringType(),  True),
            StructField("total",          DoubleType(),  True),
            StructField("VATNumber",      StringType(),  True),
            StructField("DoNotChargeVAT", BooleanType(), True),
            StructField("Ordered", ArrayType(StructType([
                StructField("count",              IntegerType(), True),
                StructField("gewicht",            DoubleType(),  True),
                StructField("plu",                LongType(),    True),
                StructField("price",              DoubleType(),  True),
                StructField("brutoverkoopwaarde", DoubleType(),  True),
                StructField("korting",            DoubleType(),  True),
                StructField("verkoopwaarde",      DoubleType(),  True),
                StructField("inkoopwaarde",       DoubleType(),  True),
                StructField("scancode",           StringType(),  True),
                StructField("subgroep",           IntegerType(), True),
                StructField("tax",                IntegerType(), True),
                StructField("taxperc",            IntegerType(), True),
                StructField("hoofdgroep",         IntegerType(), True),
                StructField("afdeling",           IntegerType(), True),
                StructField("omzetsoort",         IntegerType(), True),
                StructField("gewichtartikel",     BooleanType(), True),
                StructField("text",               StringType(),  True),
                StructField("actieomzet",         StringType(),  True),
            ])), True),
            StructField("payform", ArrayType(StructType([
                StructField("amount",      DoubleType(),  True),
                StructField("payformid",   IntegerType(), True),
                StructField("payformname", StringType(),  True),
            ])), True),
        ]), True),
    ]),
}
