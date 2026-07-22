from pyspark.sql.types import (
    StructType, StructField, StringType, BooleanType
)

# HubSpot CRM v3 list responses return objects as:
#   {"id": "...", "properties": {...}, "createdAt": "...", "updatedAt": "...", "archived": false, "url": "..."}
# Every value inside "properties" is delivered as a string (numbers, dates and
# datetimes included) â€” casting happens in 04_transforms.py.

_feedback_submission_properties = StructType([
    StructField("hs_object_id",                       StringType(), True),
    StructField("hs_survey_type",                     StringType(), True),
    StructField("hs_survey_id",                       StringType(), True),
    StructField("hs_survey_name",                     StringType(), True),
    StructField("hs_survey_channel",                  StringType(), True),
    StructField("hs_industry_standard_question_type", StringType(), True),
    StructField("hs_value",                           StringType(), True),
    StructField("hs_response_group",                  StringType(), True),
    StructField("hs_submission_timestamp",            StringType(), True),
    StructField("hs_contact_id",                      StringType(), True),
    StructField("hs_content",                         StringType(), True),
    StructField("hs_createdate",                      StringType(), True),
    StructField("hs_lastmodifieddate",                StringType(), True),
    StructField("sv_abm_visitdate",                   StringType(), True),
    StructField("sv_ap_dtt_visitedate",               StringType(), True),
    StructField("sv_fr_dtt_booking_arrival",          StringType(), True),
    StructField("sv_fr_dtt_booking_departure",        StringType(), True),
    StructField("sv_frm_booking_arrival",             StringType(), True),
    StructField("sv_frm_booking_departure",           StringType(), True),
])

_contact_properties = StructType([
    StructField("hs_object_id",                       StringType(), True),
    StructField("email",                              StringType(), True),
    StructField("firstname",                          StringType(), True),
    StructField("lastname",                           StringType(), True),
    StructField("lifecyclestage",                     StringType(), True),
    StructField("hubspot_owner_id",                   StringType(), True),
    StructField("createdate",                         StringType(), True),
    StructField("lastmodifieddate",                   StringType(), True),
    StructField("hs_feedback_last_nps_rating_number", StringType(), True),
    StructField("hs_feedback_last_survey_date",       StringType(), True),
])

entity_schema_config = {
    "feedback_submissions": StructType([
        StructField("id",         StringType(),                    True),
        StructField("properties", _feedback_submission_properties, True),
        StructField("createdAt",  StringType(),                    True),
        StructField("updatedAt",  StringType(),                    True),
        StructField("archived",   BooleanType(),                   True),
        StructField("url",        StringType(),                    True),
    ]),

    "contacts": StructType([
        StructField("id",         StringType(),        True),
        StructField("properties", _contact_properties, True),
        StructField("createdAt",  StringType(),        True),
        StructField("updatedAt",  StringType(),        True),
        StructField("archived",   BooleanType(),       True),
    ]),
}
