from pyspark.sql.types import StringType, DateType
from pyspark.sql.functions import (
    col, concat_ws, when, cast, lit, explode, explode_outer,
    to_timestamp, to_date, concat, coalesce, from_utc_timestamp
)
from pyspark.sql import DataFrame


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# TRANSFORMS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def transform_orders(df: DataFrame) -> DataFrame:
    return df.select(
        concat(col("VestigingId"), lit("_"), col("id")).alias("Id"),
        concat(col("VestigingId"), lit("_"), col("storeId")).alias("FK_Locaties_Id"),
        concat(col("VestigingId"), lit("_"), col("salesPoint.id")).alias("FK_Verkooppunten_Id"),
        col("VestigingId"),
        col("orderNr").alias("OrderNummer"),
        col("receiptNr").alias("BonNummer"),
        col("workDay").cast("date").alias("Datum"),
        col("occupiedSeatsNumber").alias("AantalStoelenBezet"),
        from_utc_timestamp(col("createdAt"), "Europe/Amsterdam").alias("AangemaaktOp"),
        from_utc_timestamp(col("lastUpdatedAt"), "Europe/Amsterdam").alias("LaatsteWijziging"),
    )


def transform_sales_items(df: DataFrame) -> DataFrame:
    return (
        df
        .withColumn('item', explode('salesItems').alias('item')
            ).select(
                concat(col('VestigingId'), lit('_'), col('item.id')).alias('Id'),
                concat(col('VestigingId'), lit('_'), col('id')).alias('FK_Orders_Id'),
                concat(col('VestigingId'), lit('_'), col('item.turnoverGroups').getItem(0)).alias('FK_Omzetgroepen_Id'),
                col('item.salesItemType').alias('SalesType'),
                col('item.course.name').alias('ItemType'),
                col('item.user.name').alias('Gebruiker'),
                from_utc_timestamp(col('item.createdAt'), "Europe/Amsterdam").alias('AangemaaktOp'),
                col('item.workDay').cast(DateType()).alias('Datum'),
                col('item.product.id').alias('ProductId'),
                col('item.product.name').alias('ProductNaam'),
                col('item.userShiftId').alias('GebruikersSessieId'),
                col('item.itemCount').alias('Aantal'),
                col('item.price.value').alias('Prijs'),
                col('item.price.currency').alias('Valuta'),
                col('item.price.includeVAT').alias('PrijsInclBTW'),
                col('item.price.VAT.id').alias('BTWTariefId'),
                col('item.price.VAT.percentage').alias('BTWPercentage'),
                col('item.netAmount.inclVAT').alias('NettoBedragInclBTW'),
                col('item.netAmount.exclVAT').alias('NettoBedragExclBTW'),
                col('item.netAmount.VAT').alias('NettoBedragBTW'),
                col('item.grossAmount.inclVAT').alias('BrutoBedragInclBTW'),
                col('item.grossAmount.exclVAT').alias('BrutoBedragExclBTW'),
                col('item.grossAmount.VAT').alias('BrutoBedragBTW'),
                col('item.productGroups').getItem(0).alias('ProductGroep1'),
                col('item.productGroups').getItem(1).alias('ProductGroep2')
            )
        )


def transform_payment_items(df: DataFrame) -> DataFrame:
    return (
        df
        .withColumn('payment', explode('paymentItems').alias('item'))
            .select(
                concat(col('VestigingId'), lit('_'), col('payment.id')).alias('Id'),
                concat(col('VestigingId'), lit('_'), col('id')).alias('FK_Orders_Id'),
                col('payment.user.name').alias('Gebruiker'),
                from_utc_timestamp(col('payment.createdAt'), "Europe/Amsterdam").alias('AangemaaktOp'),
                col('payment.workDay').cast(DateType()).alias('Datum'),
                col('payment.amount').alias('Bedrag'),
                col('payment.currency.code').alias('ValutaCode'),
                col('payment.currency.rate').alias('ValutaKoers'),
                col('payment.shiftId').alias('GebruikerSessieId'),
                col('payment.payment.externalId').alias('ExternId'),
                col('payment.payment.amount').alias('BetalingBedrag'),
                col('payment.payment.method.id').alias('BetalingsmethodeId'),
                col('payment.payment.method.name').alias('BetalingsmethodeNaam'),
                col('payment.payment.methodType.name').alias('BetalingsmethodeTypeNaam')
            )
        )


def transform_salespoints(df: DataFrame) -> DataFrame:
    _cols = ['Id', 'Type', 'VestigingId', 'LocatieId', 'VerkooppuntId', 'Naam', 'ParentVerkooppuntId']

    df_salespoint_parent = df.select(
        concat(col('VestigingId'), lit('_'), col('id')).alias('Id'),
        col('VestigingId'),
        lit('Level1').alias('Type'),
        col('_store_id').alias('LocatieId'),
        col('id').alias('VerkooppuntId'),
        col('name').alias('Naam'),
        lit(None).cast(StringType()).alias('ParentVerkooppuntId')
    )

    df_level_1 = (df
        .withColumn('level1', explode_outer('salesPoints'))
        .select(
            concat(col('VestigingId'), lit('_'), col('level1.id')).alias('Id'),
            col('VestigingId'),
            lit('Level2').alias('Type'),
            col('_store_id').alias('LocatieId'),
            concat(col('VestigingId'), lit('_'), col('id')).alias('ParentVerkooppuntId'),
            col('level1.id').alias('VerkooppuntId'),
            col('level1.name').alias('Naam'),
            col('level1.salesPoints').alias('salesPoints_level2')
        )
        .filter(col('level1.id').isNotNull())
    )

    df_level_2 = (df_level_1
        .withColumn('level2', explode_outer('salesPoints_level2'))
        .select(
            concat(col('VestigingId'), lit('_'), col('level2.id')).alias('Id'),
            col('VestigingId'),
            lit('Level3').alias('Type'),
            col('LocatieId'),
            concat(col('VestigingId'), lit('_'), col('VerkooppuntId')).alias('ParentVerkooppuntId'),
            col('level2.id').alias('VerkooppuntId'),
            col('level2.name').alias('Naam'),
            col('level2.salesPoints').alias('salesPoints_level3')
        )
        .filter(col('level2.id').isNotNull())
    )

    df_level_3 = (df_level_2
        .withColumn('level3', explode_outer('salesPoints_level3'))
        .select(
            concat(col('VestigingId'), lit('_'), col('level3.id')).alias('Id'),
            col('VestigingId'),
            col('LocatieId'),
            lit('Level4').alias('Type'),
            concat(col('VestigingId'), lit('_'), col('VerkooppuntId')).alias('ParentVerkooppuntId'),
            col('level3.id').alias('VerkooppuntId'),
            col('level3.name').alias('Naam'),
            col('level3.salesPoints').alias('salesPoints_level4')
        )
        .filter(col('level3.id').isNotNull())
    )

    df_level_4 = (df_level_3
        .withColumn('level4', explode_outer('salesPoints_level4'))
        .select(
            concat(col('VestigingId'), lit('_'), col('level4.id')).alias('Id'),
            col('VestigingId'),
            col('LocatieId'),
            lit('Level5').alias('Type'),
            concat(col('VestigingId'), lit('_'), col('VerkooppuntId')).alias('ParentVerkooppuntId'),
            col('level4.id').alias('VerkooppuntId'),
            col('level4.name').alias('Naam')
        )
        .filter(col('level4.id').isNotNull())
    )

    return (
        df_salespoint_parent.select(_cols)
        .union(df_level_1.select(_cols))
        .union(df_level_2.select(_cols))
        .union(df_level_3.select(_cols))
        .union(df_level_4.select(_cols))
        .distinct()
    )


def transform_stores(df: DataFrame) -> DataFrame:
    return df.select(
        concat(col('VestigingId'), lit('_'), col('id')).alias('Id'),
        col('VestigingId'),
        col('id').alias('LocatieId'),
        col('name').alias('Naam')
    )


def transform_turnover_groups(df: DataFrame) -> DataFrame:
    parent_lookup = df.select(
        concat(col('VestigingId'), lit('_'), col('id')).alias('_parent_id'),
        col('name').alias('ParentOmzetGroep')
    )

    df_with_parent = df.join(
        parent_lookup,
        concat(df['VestigingId'], lit('_'), df['parentID']) == parent_lookup['_parent_id'],
        'left'
    )

    return df_with_parent.select(
        concat(col('VestigingId'), lit('_'), col('id')).alias('Id'),
        col('VestigingId'),
        col('id').alias('Omzetgroep'),
        col('name').alias('Naam'),
        when(col('parentID').isNotNull(), col('_parent_id'))
            .otherwise(lit(None)).alias('ParentId'),
        coalesce(col('ParentOmzetGroep'), col('name')).alias('HoofdOmzetgroep')
    ).distinct()


entity_transform_config = {
    "orders":          transform_orders,
    "sales_items":     transform_sales_items,
    "payment_items":   transform_payment_items,
    "salespoints":     transform_salespoints,
    "stores":          transform_stores,
    "turnover_groups": transform_turnover_groups,
}
