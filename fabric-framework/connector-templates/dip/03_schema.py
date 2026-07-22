from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, BooleanType, ArrayType
)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# SCHEMAS â€” StructType for spark.read.schema()
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_production_ref_schema = StructType([
    StructField("id", StringType(), True),
])

_theater_location_ref_schema = StructType([
    StructField("id", IntegerType(), True),
])

_province_schema = StructType([
    StructField("name", StringType(), True),
])

_theater_location_schema = StructType([
    StructField("id",   IntegerType(), True),
    StructField("name", StringType(),  True),
])

entity_schema_config = {

    "productions": StructType([
        StructField("id",        StringType(),  True),
        StructField("title",     StringType(),  True),
        StructField("startDate", StringType(),  True),
        StructField("season",    StringType(),  True),
    ]),

    "performances": StructType([
        StructField("id",               IntegerType(),                True),
        StructField("number",           IntegerType(),                True),
        StructField("date",             StringType(),                 True),
        StructField("status",           StringType(),                 True),
        StructField("type",             StringType(),                 True),
        StructField("private",          BooleanType(),                True),
        StructField("in_festival",      BooleanType(),                True),
        StructField("production",       _production_ref_schema,       True),
        StructField("theater_location", _theater_location_ref_schema, True),
        StructField("amount_rank1",     IntegerType(),                True),
        StructField("amount_rank2",     IntegerType(),                True),
        StructField("amount_rank3",     IntegerType(),                True),
        StructField("amount_rank4",     IntegerType(),                True),
        StructField("amount_rank5",     IntegerType(),                True),
        StructField("amount_rank6",     IntegerType(),                True),
        StructField("amount_rank7",     IntegerType(),                True),
        StructField("amount_rank8",     IntegerType(),                True),
        StructField("amount_rank9",     IntegerType(),                True),
        StructField("amount_rank10",    IntegerType(),                True),
        StructField("_production_id",   StringType(),                 True),
    ]),

    "theaters": StructType([
        StructField("id",                IntegerType(),                       True),
        StructField("city",              StringType(),                        True),
        StructField("name",              StringType(),                        True),
        StructField("province",          _province_schema,                    True),
        StructField("street",            StringType(),                        True),
        StructField("zipcode",           StringType(),                        True),
        StructField("type",              StringType(),                        True),
        StructField("theater_locations", ArrayType(_theater_location_schema), True),
    ]),

    "sales": StructType([
        StructField("id",           IntegerType(),                        True),
        StructField("name",         StringType(),                         True),
        StructField("updated",      StringType(),                         True),
        StructField("tickets",      IntegerType(),                        True),
        StructField("recette",      IntegerType(),                        True),
        StructField("performances", ArrayType(StructType([
            StructField("number",  IntegerType(), True),
            StructField("date",    StringType(),  True),
            StructField("updated", StringType(),  True),
            StructField("tickets", IntegerType(), True),
            StructField("recette", IntegerType(), True),
        ])),                                                               True),
        StructField("_production_id", StringType(),                       True),
    ]),
}
