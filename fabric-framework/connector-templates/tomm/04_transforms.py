from pyspark.sql.types import StringType
from pyspark.sql.functions import (
    col, when, lit, explode, count, substring, coalesce, to_date, sum, first, avg
)
from pyspark.sql import DataFrame


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# TRANSFORMS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def transform_booking(df: DataFrame) -> DataFrame:
    df_booking_basis = (
        df
        .withColumn(
            'Resort',
            when(
                substring(col('number'), 1, 3).isin('FRM', 'DTT'),
                substring(col('number'), 1, 3)
            ).otherwise(lit('FRM'))
        )
        .select(
            col('id').alias('Id'),
            col('number').alias('Boekingnummer'),
            col('Resort'),
            to_date(col('arrival')).alias('Aankomst'),
            to_date(col('departure')).alias('Vertrek'),
            col('status').alias('Status'),
            to_date(col('date')).alias('Boekingdatum'),
            col('arrived').alias('Ingecheckt'),
            col('departed').alias('Uitgecheckt'),
            col('stay_days').alias('Verblijfdagen'),
            col('total').alias('Totalekosten'),
            col('cost_of_stay').alias('Verblijfkosten'),
            col('cost_of_items').alias('Artikelkosten'),
            col('cost_of_discount').alias('Kortingkosten'),
            col('cost_of_stay_excluding_vat').alias('VerblijfkostenExclusiefBtw'),
            col('cost_of_stay_vat_percentage').alias('VerblijfkostenBtwPercentage'),
            col('sales_channel').alias('Verkoopkanaal'),
        )
    )

    df_license_plate = (
        df
        .withColumn('Kenteken', explode('license_plates'))
        .groupBy('id')
        .count()
    )

    return (
        df_booking_basis.alias('booking')
        .join(df_license_plate, df_booking_basis['Id'] == df_license_plate['id'], 'left')
        .withColumn(
            'KentekenGeregistreerd',
            when(coalesce(df_license_plate['count'], lit(0)) > 0, lit(True)).otherwise(lit(False))
        )
        .select('booking.*', 'KentekenGeregistreerd')
    )


def transform_person(df: DataFrame) -> DataFrame:
    return df.select(
        col('person.id').alias('Id'),
        col('person.first_name').alias('Voornaam'),
        col('person.last_name').alias('Achternaam'),
        col('person.last_name_prefix').alias('AchternaamVoorvoegsel'),
        col('person.email').alias('Email'),
        col('person.phone_number').alias('Telefoonnummer'),
        col('person.cell_phone_number').alias('Mobielnummer'),
        to_date(col('person.birthday')).alias('Geboortedatum'),
        col('person.gender').alias('Geslacht'),
        col('person.street').alias('Straat'),
        col('person.house_number').alias('Huisnummer'),
        col('person.house_number_prefix').alias('HuisnummerToevoeging'),
        col('person.zip_code').alias('Postcode'),
        col('person.city').alias('Plaats'),
        col('person.country').alias('Land'),
        col('person.language').alias('Taal'),
        col('person.newsletter').alias('Nieuwsbrief'),
        col('person.organisation').alias('Organisatie'),
        col('id').alias('FK_Boeking_Id'),
    )


def transform_guest(df: DataFrame) -> DataFrame:
    return (
        df
        .select(explode('guests').alias('guest_data'), col('id'))
        .select(
            col('guest_data.id').alias('Id'),
            to_date(col('guest_data.birthday')).alias('Geboortedatum'),
            col('guest_data.gender').alias('Geslacht'),
            col('id').alias('FK_Boeking_Id'),
        )
        .filter(col('Id').isNotNull())
    )


def transform_booking_rule(df: DataFrame) -> DataFrame:
    df_booking_rule_basis = (
        df
        .select(explode('booking_rules').alias('rule'), col('id'))
        .select(
            col('rule.id').alias('Id'),
            col('rule.accommodation_id').alias('AccommodatieId'),
            col('rule.accommodation').alias('Accommodatie'),
            col('rule.accommodation_group_id').alias('AccommodatiegroepId'),
            col('rule.accommodation_group').alias('AccommodatieGroep'),
            col('rule.location').alias('Locatie'),
            col('rule.arrangement').alias('Arrangement'),
            substring(col('rule.arrival_time'), 1, 8).alias('Aankomsttijd'),
            substring(col('rule.departure_time'), 1, 8).alias('Vertrektijd'),
            col('rule.total').alias('TotaalPersonen'),
            col('rule.cost_of_stay').alias('Verblijfkosten'),
            col('rule.cost_of_discount').alias('Kortingkosten'),
            col('id').alias('FK_Boeking_Id'),
        )
    )

    df_age_category = (
        df
        .withColumn('rules', explode('booking_rules'))
        .withColumn('agecat', explode('rules.age_categories'))
        .select(
            col('rules.id').alias('FK_Rule_Id'),
            col('id').alias('FK_Booking_Id'),
            col('agecat.from').alias('AgeCatFrom'),
            col('agecat.till').alias('AgeCatTill'),
            col('agecat.persons').alias('NumberPersons'),
        )
    )

    return (
        df_booking_rule_basis.alias('basis')
        .join(
            df_age_category.alias('age0'),
            (col('age0.FK_Rule_Id') == col('basis.Id'))
            & (col('age0.FK_Booking_Id') == col('basis.FK_Boeking_Id'))
            & (col('age0.AgeCatFrom') == 0),
            'left',
        )
        .join(
            df_age_category.alias('age2'),
            (col('age2.FK_Rule_Id') == col('basis.Id'))
            & (col('age2.FK_Booking_Id') == col('basis.FK_Boeking_Id'))
            & (col('age2.AgeCatFrom') == 2),
            'left',
        )
        .join(
            df_age_category.alias('age13'),
            (col('age13.FK_Rule_Id') == col('basis.Id'))
            & (col('age13.FK_Booking_Id') == col('basis.FK_Boeking_Id'))
            & (col('age13.AgeCatFrom') == 13),
            'left',
        )
        .join(
            df_age_category.alias('age21'),
            (col('age21.FK_Rule_Id') == col('basis.Id'))
            & (col('age21.FK_Booking_Id') == col('basis.FK_Boeking_Id'))
            & (col('age21.AgeCatFrom') == 21),
            'left',
        )
        .select(
            col('basis.Id'),
            col('basis.AccommodatieId'),
            col('basis.Accommodatie'),
            col('basis.AccommodatiegroepId'),
            col('basis.AccommodatieGroep'),
            col('basis.Locatie'),
            col('basis.Arrangement'),
            col('basis.Aankomsttijd'),
            col('basis.Vertrektijd'),
            col('basis.TotaalPersonen'),
            col('basis.Verblijfkosten'),
            col('basis.Kortingkosten'),
            col('age0.NumberPersons').alias('AantalLeeftijd0tot2'),
            col('age2.NumberPersons').alias('AantalLeeftijd2tot13'),
            col('age13.NumberPersons').alias('AantalLeeftijd13tot21'),
            col('age21.NumberPersons').alias('AantalLeeftijd21plus'),
            col('basis.FK_Boeking_Id'),
        )
    )


def transform_item_rule(df: DataFrame) -> DataFrame:
    return (
        df
        .select(col('id'), explode('item_rules').alias('item'))
        .groupBy(
            col('item.id').alias('Id'),
            col('item.name').alias('Artikelnaam'),
            col('item.accommodation_id').alias('AccommodatieId'),
            col('item.location_id').alias('LocatieId'),
            col('item.from').alias('GeldigVan'),
            col('item.till').alias('GeldigTot'),
            col('id').alias('FK_Boeking_Id'),
        )
        .agg(
            sum(col('item.amount')).alias('Aantal'),
            sum(col('item.price')).alias('BedragInclBtw'),
            sum(col('item.price_excluding_vat')).alias('BedragExBtw')
        )
    )


entity_transform_config = {
    "booking":      transform_booking,
    "person":       transform_person,
    "guest":        transform_guest,
    "booking_rule": transform_booking_rule,
    "item_rule":    transform_item_rule,
}
