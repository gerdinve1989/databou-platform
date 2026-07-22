from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType,
    IntegerType, BooleanType, ArrayType
)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# SCHEMAS â€” StructType for spark.read.schema()
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_user_schema = StructType([
    StructField("id",   StringType(), True),
    StructField("name", StringType(), True),
])

_currency_schema = StructType([
    StructField("code", StringType(), True),
    StructField("rate", DoubleType(), True),
])

_amount_schema = StructType([
    StructField("inclVAT",          DoubleType(),  True),
    StructField("exclVAT",          DoubleType(),  True),
    StructField("VAT",              DoubleType(),  True),
    StructField("priceIncludedVAT", BooleanType(), True),
])

_vat_info_schema = StructType([
    StructField("id",         StringType(), True),
    StructField("name",       StringType(), True),
    StructField("percentage", DoubleType(), True),
    StructField("code",       StringType(), True),
])

_tariff_schema = StructType([
    StructField("id",         StringType(), True),
    StructField("name",       StringType(), True),
    StructField("percentage", DoubleType(), True),
    StructField("code",       StringType(), True),
])

_vat_item_schema = StructType([
    StructField("tariff",   _tariff_schema,   True),
    StructField("currency", _currency_schema, True),
    StructField("amount",   _amount_schema,   True),
])

_sales_point_schema = StructType([
    StructField("id",   StringType(), True),
    StructField("name", StringType(), True),
])

_payment_method_schema = StructType([
    StructField("id",   StringType(), True),
    StructField("name", StringType(), True),
])

_payment_method_type_schema = StructType([
    StructField("id",   StringType(), True),
    StructField("name", StringType(), True),
])

_payment_schema = StructType([
    StructField("currency",   _currency_schema,            True),
    StructField("externalId", StringType(),                True),
    StructField("amount",     DoubleType(),                True),
    StructField("method",     _payment_method_schema,      True),
    StructField("methodType", _payment_method_type_schema, True),
    StructField("journal",    StringType(),                True),
])

_payment_item_schema = StructType([
    StructField("id",        StringType(),     True),
    StructField("user",      _user_schema,     True),
    StructField("currency",  _currency_schema, True),
    StructField("createdAt", StringType(),     True),
    StructField("workDay",   StringType(),     True),
    StructField("amount",    DoubleType(),     True),
    StructField("shiftId",   StringType(),     True),
    StructField("payment",   _payment_schema,  True),
])

_course_schema = StructType([
    StructField("name", StringType(), True),
])

_product_schema = StructType([
    StructField("id",   StringType(), True),
    StructField("name", StringType(), True),
])

_price_schema = StructType([
    StructField("value",      DoubleType(),     True),
    StructField("currency",   StringType(),     True),
    StructField("includeVAT", BooleanType(),    True),
    StructField("VAT",        _vat_info_schema, True),
])

_sales_item_schema = StructType([
    StructField("salesItemType",  StringType(),                True),
    StructField("id",             StringType(),                True),
    StructField("course",         _course_schema,              True),
    StructField("user",           _user_schema,                True),
    StructField("currency",       _currency_schema,            True),
    StructField("createdAt",      StringType(),                True),
    StructField("workDay",        StringType(),                True),
    StructField("product",        _product_schema,             True),
    StructField("itemCount",      DoubleType(),                True),
    StructField("price",          _price_schema,               True),
    StructField("netAmount",      _amount_schema,              True),
    StructField("grossAmount",    _amount_schema,              True),
    StructField("remarks",        ArrayType(StringType()),      True),
    StructField("userShiftId",    StringType(),                True),
    StructField("salesPoint",     _sales_point_schema,         True),
    StructField("productGroups",  ArrayType(StringType()),      True),
    StructField("turnoverGroups", ArrayType(StringType()),      True),
])

_salespoint_level_4 = StructType([
    StructField("id",          StringType(), True),
    StructField("name",        StringType(), True),
    StructField("salesPoints", StringType(), True),
])

_salespoint_level_3 = StructType([
    StructField("id",          StringType(),                   True),
    StructField("name",        StringType(),                   True),
    StructField("salesPoints", ArrayType(_salespoint_level_4), True),
])

_salespoint_level_2 = StructType([
    StructField("id",          StringType(),                   True),
    StructField("name",        StringType(),                   True),
    StructField("salesPoints", ArrayType(_salespoint_level_3), True),
])

_salespoint_level_1 = StructType([
    StructField("id",          StringType(),                   True),
    StructField("name",        StringType(),                   True),
    StructField("salesPoints", ArrayType(_salespoint_level_2), True),
])

entity_schema_config = {

    "orders": StructType([
        StructField("id",                  StringType(),                    True),
        StructField("orderNr",             StringType(),                    True),
        StructField("createdAt",           StringType(),                    True),
        StructField("lastUpdatedAt",       StringType(),                    True),
        StructField("receiptNr",           StringType(),                    True),
        StructField("storeId",             StringType(),                    True),
        StructField("workDay",             StringType(),                    True),
        StructField("occupiedSeatsNumber", IntegerType(),                   True),
        StructField("salesPoint",          _sales_point_schema,             True),
        StructField("remarks",             ArrayType(StringType()),          True),
        StructField("paymentItems",        ArrayType(_payment_item_schema),  True),
        StructField("salesItems",          ArrayType(_sales_item_schema),    True),
    ]),

    "salespoints": StructType([
        StructField("_store_id",   StringType(),                   True),
        StructField("id",          StringType(),                   True),
        StructField("name",        StringType(),                   True),
        StructField("salesPoints", ArrayType(_salespoint_level_1), True),
    ]),

    "stores": StructType([
        StructField("id",   StringType(), True),
        StructField("name", StringType(), True),
    ]),

    "turnover_groups": StructType([
        StructField("id",       StringType(), True),
        StructField("name",     StringType(), True),
        StructField("parentID", StringType(), True),
    ]),
}
