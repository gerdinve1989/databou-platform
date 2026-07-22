from pyspark.sql.types import StringType
from pyspark.sql.functions import (
    col, concat_ws, when, cast, lit, explode, explode_outer,
    to_timestamp, to_date, concat, from_utc_timestamp, sum
)
from pyspark.sql import DataFrame


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# TRANSFORMS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def transform_departments(df: DataFrame) -> DataFrame:
    return df.select(
        concat(col('VestigingId'), lit('_'), col('TblAfdelingnr').cast(StringType())).alias('Id'),
        col('*')
    ).drop('TblAfdelingnr')


def transform_maingroups(df: DataFrame) -> DataFrame:
    return df.select(
        concat(col('VestigingId'), lit('_'), col('TblHoofdgroepnr').cast(StringType())).alias('Id'),
        col('VestigingId'),
        col('TblHoofdgroepnr').alias('HoofdgroepNr'),
        col('Omschrijving').alias('Naam'),
        col('BestelFormule'),
        col('VoorstelBestellingBerekenen'),
        col('Grootboeknummer'),
    )


def transform_subgroups(df: DataFrame) -> DataFrame:
    return df.select(
        concat(col('VestigingId'), lit('_'), col('TblSubgroepnr').cast(StringType())).alias('Id'),
        concat(col('VestigingId'), lit('_'), col('TblAfdelingnr').cast(StringType())).alias('FK_Afdelingen_Id'),
        concat(col('VestigingId'), lit('_'), col('TblHoofdgroepnr').cast(StringType())).alias('FK_Hoofdgroepen_Id'),
        col('VestigingId'),
        col('TblSubgroepnr').alias('SubgroepNr'),
        col('Omschrijving').alias('Naam'),
        col('TblAfdelingnr').alias('AfdelingNr'),
        col('TblHoofdgroepnr').alias('HoofdgroepNr'),
        col('NietMeeDoenBestellingen'),
        col('NietMeeDoenDebiteurenRapport'),
        col('NietMeeDoenVoorraad'),
        col('BrutoWinstPercentage'),
        col('Leeftijdgrens'),
        col('BoekingsTekst'),
        col('TblHorecaGroepenID').alias('HorecaGroepId'),
        col('DezeGroepNietTonenInOmzet'),
    )


def transform_suppliers(df: DataFrame) -> DataFrame:
    return df.select(
        concat(col('VestigingId'), lit('_'), col('TblLeveranciersnr').cast(StringType())).alias('Id'),
        col('*')
    ).drop('TblLeveranciersnr')


def transform_payment_methods(df: DataFrame) -> DataFrame:
    return df.select(
        col('Code_kolom').alias('Id'),
        col('*')
    ).drop('Code_kolom')


def transform_vat_codes(df: DataFrame) -> DataFrame:
    return df.select(
        col('Kode').alias('Id'),
        col('*')
    ).drop('Kode')


def transform_turnover_types(df: DataFrame) -> DataFrame:
    return df.select(
        concat(col('VestigingId'), lit('_'), col('TblSoortOmzetnr').cast(StringType())).alias('Id'),
        col('VestigingId'),
        col('TblSoortOmzetnr').alias('OmzetSoortNr'),
        col('SoortOmzetomschrijving').alias('Naam'),
        col('ZienAlsDerving'),
        col('JournaliserenAls'),
        col('GrootBoekSluitregel'),
        col('GrootboekVerkoopkosten'),
        col('GrootboekDebet'),
        col('GrootboekCredit'),
        col('AantallenAlsNegatiefBehandelen'),
        col('NaarWinkel'),
    )


def transform_shops(df: DataFrame) -> DataFrame:
    return df.select(
        concat(col('VestigingId'), lit('_'), col('TblWinkelnr').cast(StringType())).alias('Id'),
        col('VestigingId'),
        col('TblWinkelnr').alias('WinkelNr'),
        col('Omschrijving').alias('Naam'),
        col('Adres'),
        col('PC').alias('Postcode'),
        col('Plaats'),
        col('LandCodeISO2').alias('LandCode'),
        col('Emailadres'),
        col('Telefoon'),
        col('Mobiel'),
        col('BICcode'),
        col('IBAN'),
        col('BtwNr'),
        col('DivisionCodeExactOnline'),
        col('ArtikelenMuterenIsToegestaan'),
    )


def transform_cash_registers(df: DataFrame) -> DataFrame:
    return df.select(
        concat(
            col('VestigingId'), lit('_'),
            col('TblWinkelsnr').cast(StringType()), lit('_'),
            col('TblKassanr').cast(StringType())
        ).alias('Id'),
        concat(col('VestigingId'), lit('_'), col('TblWinkelsnr').cast(StringType())).alias('FK_Winkels_Id'),
        col('VestigingId'),
        col('TblKassanr').alias('KassaNr'),
        col('TblWinkelsnr').alias('WinkelNr'),
        col('Omschrijving').alias('Naam'),
        col('NietMeerActief'),
        col('IsHorecaKassa'),
        col('KassaZonderladen'),
        col('KassaMetVasteLade'),
        to_timestamp(col('LaatstStartDatum')).alias('LaatstStartDatum'),
        to_timestamp(col('LaatsteStopDatum')).alias('LaatsteStopDatum'),
    )


def transform_country_codes(df: DataFrame) -> DataFrame:
    return df.select(
        col('LandCodeISO2').alias('Id'),
        col('*')
    ).drop('LandCodeISO2')


def transform_hospitality_groups(df: DataFrame) -> DataFrame:
    return df.select(
        concat(col('VestigingId'), lit('_'), col('TblHorecaGroepenID').cast(StringType())).alias('Id'),
        col('VestigingId'),
        col('*')
    ).drop('TblHorecaGroepenID')


def transform_hospitality_items(df: DataFrame) -> DataFrame:
    return df.select(
        concat(col('VestigingId'), lit('_'), col('TblHorecaItemsID').cast(StringType())).alias('Id'),
        col('VestigingId'),
        col('*')
    ).drop('TblHorecaItemsID')


def transform_hospitality_items_choices(df: DataFrame) -> DataFrame:
    return df.select(
        concat(col('VestigingId'), lit('_'), col('TblHorecaItemsKeuzeID').cast(StringType())).alias('Id'),
        col('VestigingId'),
        col('*')
    ).drop('TblHorecaItemsKeuzeID')


def transform_action_descriptions(df: DataFrame) -> DataFrame:
    return df.select(
        concat(col('VestigingId'), lit('_'), col('TblActieOmschrijvingID').cast(StringType())).alias('Id'),
        col('VestigingId'),
        col('*')
    ).drop('TblActieOmschrijvingID')


def transform_actions(df: DataFrame) -> DataFrame:
    return df.select(
        concat(col('VestigingId'), lit('_'), col('TblActieID').cast(StringType())).alias('Id'),
        col('VestigingId'),
        col('*')
    ).drop('TblActieID')


def transform_articles(df: DataFrame) -> DataFrame:
    return df.select(
        concat(col('VestigingId'), lit('_'), col('TblArtikelnr').cast(StringType())).alias('Id'),
        col('VestigingId'),
        col('*')
    ).drop('TblArtikelnr')


def transform_customers(df: DataFrame) -> DataFrame:
    return df.select(
        concat(col('VestigingId'), lit('_'), col('TblKlantenID').cast(StringType())).alias('Id'),
        col('VestigingId'),
        col('*')
    ).drop('TblKlantenID')


def transform_day_turnover(df: DataFrame) -> DataFrame:
    return df.select(
        concat(
            col('VestigingId'), lit('_'),
            col('Transaction.branch').cast(StringType()), lit('_'),
            col('Transaction.register').cast(StringType()), lit('_'),
            col('Transaction.billno').cast(StringType())
        ).alias('Id'),
        concat(col('VestigingId'), lit('_'), col('Transaction.branch').cast(StringType())).alias('FK_Winkels_Id'),
        concat(
            col('VestigingId'), lit('_'),
            col('Transaction.branch').cast(StringType()), lit('_'),
            col('Transaction.register').cast(StringType())
        ).alias('FK_Kassas_Id'),
        col('VestigingId'),
        col('Transaction.billno').alias('BonNummer'),
        col('Transaction.cashier').alias('Kassamedewerker'),
        col('Transaction.custno').alias('KlantNummer'),
        col('Transaction.custname').alias('KlantNaam'),
        to_timestamp(col('Transaction.time')).alias('Tijd'),
        to_date(col('Transaction.time')).alias('Datum'),
        col('Transaction.total').alias('TotaalBedrag'),
        col('Transaction.VATNumber').alias('BTWNummer'),
        col('Transaction.DoNotChargeVAT').alias('ZonderBTW'),
    )


def transform_day_turnover_lines(df: DataFrame) -> DataFrame:
    _transaction_id = concat(
        col('VestigingId'), lit('_'),
        col('Transaction.branch').cast(StringType()), lit('_'),
        col('Transaction.register').cast(StringType()), lit('_'),
        col('Transaction.billno').cast(StringType())
    )
    return (
        df
        .filter(col('Transaction.Ordered').isNotNull())
        .withColumn('item', explode('Transaction.Ordered'))
        .select(
            _transaction_id.alias('FK_DagOmzetTransacties_Id'),
            col('VestigingId'),
            to_date(col('Transaction.time')).alias('Datum'),
            col('item.plu').alias('PLU'),
            col('item.text').alias('Omschrijving'),
            col('item.count').alias('Aantal'),
            col('item.gewicht').alias('Gewicht'),
            col('item.gewichtartikel').alias('GewichtArtikel'),
            col('item.price').alias('Prijs'),
            col('item.korting').alias('Korting'),
            col('item.brutoverkoopwaarde').alias('BrutoVerkoopwaarde'),
            col('item.verkoopwaarde').alias('Verkoopwaarde'),
            col('item.inkoopwaarde').alias('Inkoopwaarde'),
            col('item.scancode').alias('Scancode'),
            concat(col('VestigingId'), lit('_'), col('item.subgroep').cast(StringType())).alias('FK_Subgroepen_Id'),
            col('item.subgroep').alias('SubgroepNr'),
            concat(col('VestigingId'), lit('_'), col('item.hoofdgroep').cast(StringType())).alias('FK_Hoofdgroepen_Id'),
            col('item.hoofdgroep').alias('HoofdgroepNr'),
            col('item.afdeling').alias('AfdelingNr'),
            col('item.omzetsoort').alias('OmzetSoortNr'),
            col('item.tax').alias('BTWCode'),
            col('item.taxperc').alias('BTWPercentage'),
            col('item.actieomzet').alias('ActieOmzet'),
        )
        .groupBy(
            'FK_DagOmzetTransacties_Id', 'VestigingId', 'Datum', 'PLU', 'Omschrijving',
            'GewichtArtikel', 'Prijs', 'Korting', 'Scancode',
            'FK_Subgroepen_Id', 'SubgroepNr', 'FK_Hoofdgroepen_Id', 'HoofdgroepNr',
            'AfdelingNr', 'OmzetSoortNr', 'BTWCode', 'BTWPercentage', 'ActieOmzet'
        )
        .agg(
            sum('Aantal').alias('Aantal'),
            sum('Gewicht').alias('Gewicht'),
            sum('BrutoVerkoopwaarde').alias('BrutoVerkoopwaarde'),
            sum('Verkoopwaarde').alias('Verkoopwaarde'),
            sum('Inkoopwaarde').alias('Inkoopwaarde')
        )
    )


def transform_invoices(df: DataFrame) -> DataFrame:
    return df.select(
        concat(col('VestigingId'), lit('_'), col('Factuurnummer').cast(StringType())).alias('Id'),
        col('VestigingId'),
        col('*')
    ).drop('Factuurnummer')


entity_transform_config = {
    "departments":               transform_departments,
    "maingroups":                transform_maingroups,
    "subgroups":                 transform_subgroups,
    "suppliers":                 transform_suppliers,
    "payment_methods":           transform_payment_methods,
    "vat_codes":                 transform_vat_codes,
    "turnover_types":            transform_turnover_types,
    "shops":                     transform_shops,
    "cash_registers":            transform_cash_registers,
    "country_codes":             transform_country_codes,
    "hospitality_groups":        transform_hospitality_groups,
    "hospitality_items":         transform_hospitality_items,
    "hospitality_items_choices": transform_hospitality_items_choices,
    "action_descriptions":       transform_action_descriptions,
    "actions":                   transform_actions,
    "articles":                  transform_articles,
    "customers":                 transform_customers,
    "day_turnover":              transform_day_turnover,
    "day_turnover_lines":        transform_day_turnover_lines,
    "invoices":                  transform_invoices,
}
