from pyspark.sql.types import TimestampType, DecimalType, IntegerType
from pyspark.sql.functions import (
    col, explode, current_date, current_timestamp, date_sub
)
from pyspark.sql import DataFrame


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# TRANSFORMS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def transform_productions(df: DataFrame) -> DataFrame:
    return df.select(
        col('id').alias('Id'),
        col('title').alias('Titel'),
        col('startDate').alias('StartDatum'),
        col('season').alias('Seizoen'),
    )


def transform_performances(df: DataFrame) -> DataFrame:
    return df.select(
        col('production.id').alias('ProductieId'),
        col('theater_location.id').alias('TheaterLocatieId'),
        col('id').alias('Id'),
        col('number').alias('VoorstellingNummer'),
        col('date').cast(TimestampType()).alias('StartTijdVoorstelling'),
        col('status').alias('Status'),
        col('type').alias('Type'),
        col('private').alias('IsUitkoopZonderVerkoop'),
        col('in_festival').alias('IsInFestival'),
        col('amount_rank1').alias('AantalRang01'),
        col('amount_rank2').alias('AantalRang02'),
        col('amount_rank3').alias('AantalRang03'),
        col('amount_rank4').alias('AantalRang04'),
        col('amount_rank5').alias('AantalRang05'),
        col('amount_rank6').alias('AantalRang06'),
        col('amount_rank7').alias('AantalRang07'),
        col('amount_rank8').alias('AantalRang08'),
        col('amount_rank9').alias('AantalRang09'),
        col('amount_rank10').alias('AantalRang10'),
    )


def transform_theaters(df: DataFrame) -> DataFrame:
    return df.select(
        col('id').alias('Id'),
        col('city').alias('Plaats'),
        col('name').alias('Naam'),
        col('province.name').alias('Provincie'),
        col('street').alias('Straat'),
        col('zipcode').alias('Postcode'),
        col('type').alias('Type'),
    )


def transform_theater_locations(df: DataFrame) -> DataFrame:
    return (
        df.withColumn('loc', explode('theater_locations'))
        .select(
            col('id').alias('TheaterId'),
            col('loc.id').alias('Id'),
            col('loc.name').alias('Naam'),
        )
    )


def transform_sales(df: DataFrame) -> DataFrame:
    return (
        df.withColumn('perf', explode('performances'))
        .filter(col('perf.date').cast(TimestampType()) > date_sub(current_date(), 14))
        .select(
            col('perf.number').alias('VoorstellingId'),
            current_date().alias('SnapshotDatum'),
            (col('perf.recette').cast(DecimalType()) / 100).cast(DecimalType(8, 2)).alias('Recette'),
            col('perf.tickets').cast(IntegerType()).alias('Tickets'),
            col('perf.updated').cast(TimestampType()).alias('Updated'),
            current_timestamp().alias('Toegevoegd'),
        )
    )


entity_transform_config = {
    "productions":       transform_productions,
    "performances":      transform_performances,
    "theaters":          transform_theaters,
    "theater_locations": transform_theater_locations,
    "sales":             transform_sales,
}
