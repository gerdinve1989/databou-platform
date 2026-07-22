from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType,
    IntegerType, BooleanType, ArrayType
)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# SCHEMAS â€” StructType for spark.read.schema()
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_person_schema = StructType([
    StructField("id",                  StringType(),  True),
    StructField("first_name",          StringType(),  True),
    StructField("last_name",           StringType(),  True),
    StructField("last_name_prefix",    StringType(),  True),
    StructField("email",               StringType(),  True),
    StructField("phone_number",        StringType(),  True),
    StructField("cell_phone_number",   StringType(),  True),
    StructField("birthday",            StringType(),  True),
    StructField("gender",              StringType(),  True),
    StructField("street",              StringType(),  True),
    StructField("house_number",        StringType(),  True),
    StructField("house_number_prefix", StringType(),  True),
    StructField("zip_code",            StringType(),  True),
    StructField("city",                StringType(),  True),
    StructField("country",             StringType(),  True),
    StructField("language",            StringType(),  True),
    StructField("newsletter",          BooleanType(), True),
    StructField("organisation",        StringType(),  True),
])

_guest_schema = StructType([
    StructField("id",       StringType(), True),
    StructField("birthday", StringType(), True),
    StructField("gender",   StringType(), True),
])

_age_category_schema = StructType([
    StructField("from",    IntegerType(), True),
    StructField("till",    IntegerType(), True),
    StructField("persons", IntegerType(), True),
])

_booking_rule_schema = StructType([
    StructField("id",                     StringType(),                       True),
    StructField("accommodation_id",       StringType(),                       True),
    StructField("accommodation",          StringType(),                       True),
    StructField("accommodation_group_id", StringType(),                       True),
    StructField("accommodation_group",    StringType(),                       True),
    StructField("location",               StringType(),                       True),
    StructField("arrangement",            StringType(),                       True),
    StructField("arrival_time",           StringType(),                       True),
    StructField("departure_time",         StringType(),                       True),
    StructField("total",                  IntegerType(),                      True),
    StructField("cost_of_stay",           DoubleType(),                       True),
    StructField("cost_of_discount",       DoubleType(),                       True),
    StructField("age_categories",         ArrayType(_age_category_schema),    True),
])

_item_rule_schema = StructType([
    StructField("id",                  StringType(),  True),
    StructField("name",                StringType(),  True),
    StructField("accommodation_id",    StringType(),  True),
    StructField("location_id",         StringType(),  True),
    StructField("from",                StringType(),  True),
    StructField("till",                StringType(),  True),
    StructField("amount",              DoubleType(),  True),
    StructField("price",               DoubleType(),  True),
    StructField("price_excluding_vat", DoubleType(),  True),
    StructField("vat_percentage",      DoubleType(),  True),
])

entity_schema_config = {
    "booking": StructType([
        StructField("id",                              StringType(),                       True),
        StructField("number",                          StringType(),                       True),
        StructField("arrival",                         StringType(),                       True),
        StructField("departure",                       StringType(),                       True),
        StructField("status",                          StringType(),                       True),
        StructField("date",                            StringType(),                       True),
        StructField("arrived",                         BooleanType(),                      True),
        StructField("departed",                        BooleanType(),                      True),
        StructField("stay_days",                       IntegerType(),                      True),
        StructField("total",                           DoubleType(),                       True),
        StructField("cost_of_stay",                    DoubleType(),                       True),
        StructField("cost_of_items",                   DoubleType(),                       True),
        StructField("cost_of_discount",                DoubleType(),                       True),
        StructField("cost_of_stay_excluding_vat",      DoubleType(),                       True),
        StructField("cost_of_stay_vat_percentage",     DoubleType(),                       True),
        StructField("sales_channel",                   StringType(),                       True),
        StructField("license_plates",                  ArrayType(StringType()),             True),
        StructField("person",                          _person_schema,                      True),
        StructField("guests",                          ArrayType(_guest_schema),             True),
        StructField("booking_rules",                   ArrayType(_booking_rule_schema),      True),
        StructField("item_rules",                      ArrayType(_item_rule_schema),         True),
    ]),
}
