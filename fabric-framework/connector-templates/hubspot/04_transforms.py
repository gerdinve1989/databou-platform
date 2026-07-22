from pyspark.sql.types import IntegerType, TimestampType, DateType
from pyspark.sql.functions import col, coalesce, current_date, date_add, lit, to_date, to_timestamp, when
from pyspark.sql import DataFrame

# Survey â†’ location mapping (Van Hoorne). hs_survey_id is the stable key; the
# survey name is only a fallback for future surveys not yet mapped here.
_LOCATIONS = {
    "9":  ("Avonturenboerderij Molenwaard",  "park"),
    "28": ("Avonturenpark De Tovertuin",     "park"),
    "10": ("Familie Resort Molenwaard",      "resort"),
    "29": ("Familie Resort De Tovertuin",    "resort"),
}


def _locatie(sid_col, fallback_col):
    expr = None
    for sid, (name, _t) in _LOCATIONS.items():
        expr = when(sid_col == sid, lit(name)) if expr is None else expr.when(sid_col == sid, lit(name))
    return expr.otherwise(fallback_col)


def _locatie_type(sid_col):
    expr = None
    for sid, (_name, t) in _LOCATIONS.items():
        expr = when(sid_col == sid, lit(t)) if expr is None else expr.when(sid_col == sid, lit(t))
    return expr.otherwise(lit("onbekend"))


def transform_feedback_submissions(df: DataFrame) -> DataFrame:
    """One row per scored NPS survey submission.

    Filters out knowledge-base feedback (no survey id) and unscored/CSAT
    submissions, so hubspot.Nps only holds NPS-classified answers.
    `Datum` is the assumed reporting axis: park visit date where the survey
    captured one, else the submission date â€” both source dates stay available
    as separate columns so the axis can be switched without re-ingesting.
    """
    p = "properties"
    df = df.filter(
        col(f"{p}.hs_survey_id").isNotNull()
        & col(f"{p}.hs_value").isNotNull()
        & col(f"{p}.hs_response_group").isin("PROMOTER", "PASSIVE", "DETRACTOR")
    )
    bezoek = coalesce(
        to_date(col(f"{p}.sv_abm_visitdate")),
        to_date(col(f"{p}.sv_ap_dtt_visitedate")),
    )
    inzend = to_timestamp(col(f"{p}.hs_submission_timestamp"))
    # Visit dates are typed in by respondents and contain typos (observed range
    # 1925..2926). Only trust them within a sane window; else fall back to the
    # (system-generated) submission date for the reporting axis.
    bezoek_valide = when(
        (bezoek >= lit("2020-01-01")) & (bezoek <= date_add(current_date(), 1)), bezoek
    )
    return df.select(
        col("id").alias("Id"),
        col(f"{p}.hs_survey_id").cast(IntegerType()).alias("SurveyId"),
        col(f"{p}.hs_survey_name").alias("SurveyNaam"),
        _locatie(col(f"{p}.hs_survey_id"), col(f"{p}.hs_survey_name")).alias("Locatie"),
        _locatie_type(col(f"{p}.hs_survey_id")).alias("LocatieType"),
        col(f"{p}.hs_value").cast(IntegerType()).alias("Score"),
        col(f"{p}.hs_response_group").alias("Groep"),
        coalesce(bezoek_valide, inzend.cast(DateType())).alias("Datum"),
        bezoek.alias("BezoekDatum"),
        inzend.cast(DateType()).alias("InzendDatum"),
        inzend.alias("InzendTijdstip"),
        to_date(col(f"{p}.sv_fr_dtt_booking_arrival")).alias("FrDttAankomst"),
        to_date(col(f"{p}.sv_frm_booking_arrival")).alias("FrmAankomst"),
        col(f"{p}.hs_contact_id").alias("ContactId"),
        col(f"{p}.hs_content").alias("Toelichting"),
        to_timestamp(col(f"{p}.hs_lastmodifieddate")).alias("GewijzigdOp"),
    )


entity_transform_config = {
    "feedback_submissions": transform_feedback_submissions,
}
