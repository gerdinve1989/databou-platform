from pyspark.sql.functions import col, to_date
from pyspark.sql import DataFrame


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# TRANSFORMS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def transform_taxi_trip_fact(df: DataFrame) -> DataFrame:
    return df.select(
        col("trip_id").alias("RitId"),
        col("trip_date").alias("RitDatum"),
        col("vendor_id").alias("LeverancierId"),
        col("pickup_datetime").alias("OphaalMoment"),
        col("dropoff_datetime").alias("AfzetMoment"),
        col("passenger_count").alias("AantalPassagiers"),
        col("trip_distance").alias("RitAfstand"),
        col("ratecodeid").alias("TariefCode"),
        col("store_and_fwd_flag").alias("OpslagVlag"),
        col("pulocationid").alias("OphaalLocatieId"),
        col("dolocationid").alias("AfzetLocatieId"),
        col("payment_type").alias("Betaalwijze"),
        col("fare_amount").alias("RitBedrag"),
        col("extra").alias("Toeslag"),
        col("mta_tax").alias("MtaBelasting"),
        col("tip_amount").alias("Fooi"),
        col("tolls_amount").alias("TolBedrag"),
        col("improvement_surcharge").alias("VerbeteringsToeslag"),
        col("total_amount").alias("TotaalBedrag"),
        col("congestion_surcharge").alias("FileToeslag"),
        col("airport_fee").alias("LuchthavenToeslag"),
        col("cbd_congestion_fee").alias("CbdFileToeslag"),
        col("load_batch_id").alias("LaadBatchId"),
        col("load_utc").alias("LaadUtc"),
    )


def transform_hvfhv_trip_fact(df: DataFrame) -> DataFrame:
    return df.select(
        col("hvfhv_trip_id").alias("HvfhvRitId"),
        to_date(col("pickup_datetime")).alias("OphaalDatum"),
        col("hvfhs_license_num").alias("LicentieNummer"),
        col("dispatching_base_num").alias("BasisNummer"),
        col("originating_base_num").alias("HerkomstBasisNummer"),
        col("request_datetime").alias("AanvraagMoment"),
        col("on_scene_datetime").alias("TerPlaatsteMoment"),
        col("pickup_datetime").alias("OphaalMoment"),
        col("dropoff_datetime").alias("AfzetMoment"),
        col("pulocationid").alias("OphaalLocatieId"),
        col("dolocationid").alias("AfzetLocatieId"),
        col("trip_miles").alias("RitMijlen"),
        col("trip_time").alias("RitTijdSeconden"),
        col("base_passenger_fare").alias("BasisRitBedrag"),
        col("tolls").alias("TolBedrag"),
        col("bcf").alias("ZwartAutoFonds"),
        col("sales_tax").alias("Omzetbelasting"),
        col("congestion_surcharge").alias("FileToeslag"),
        col("airport_fee").alias("LuchthavenToeslag"),
        col("tips").alias("Fooi"),
        col("driver_pay").alias("ChauffeursLoon"),
        col("shared_request_flag").alias("GedeeldVerzoek"),
        col("shared_match_flag").alias("GedeeldMatch"),
        col("access_a_ride_flag").alias("ToegangsRit"),
        col("wav_request_flag").alias("RolstoelVerzoek"),
        col("wav_match_flag").alias("RolstoelMatch"),
        col("cbd_congestion_fee").alias("CbdFileToeslag"),
        col("load_batch_id").alias("LaadBatchId"),
        col("load_utc").alias("LaadUtc"),
    )


def transform_fhv_trip_fact(df: DataFrame) -> DataFrame:
    return df.select(
        col("fhv_trip_id").alias("FhvRitId"),
        to_date(col("pickup_datetime")).alias("OphaalDatum"),
        col("dispatching_base_num").alias("BasisNummer"),
        col("pickup_datetime").alias("OphaalMoment"),
        col("dropoff_datetime").alias("AfzetMoment"),
        col("pulocationid").alias("OphaalLocatieId"),
        col("dolocationid").alias("AfzetLocatieId"),
        col("sr_flag").alias("GedeeldRit"),
        col("affiliated_base_number").alias("GelieerdeBasisNummer"),
        col("load_batch_id").alias("LaadBatchId"),
        col("load_utc").alias("LaadUtc"),
    )


def transform_taxi_zone_lookup(df: DataFrame) -> DataFrame:
    return df.select(
        col("location_id").alias("LocatieId"),
        col("borough").alias("Stadsdeel"),
        col("zone").alias("Zone"),
        col("service_zone").alias("ServiceZone"),
        col("load_utc").alias("LaadUtc"),
    )


def transform_taxi_load_batch(df: DataFrame) -> DataFrame:
    return df.select(
        col("load_batch_id").alias("LaadBatchId"),
        col("source_name").alias("BronNaam"),
        col("source_path").alias("BronPad"),
        col("load_started_utc").alias("LaadStartUtc"),
        col("load_finished_utc").alias("LaadEindeUtc"),
        col("rows_loaded").alias("AantalRijen"),
        col("load_status").alias("LaadStatus"),
        col("notes").alias("Notities"),
    )


entity_transform_config = {
    "taxi_trip_fact":    transform_taxi_trip_fact,
    "hvfhv_trip_fact":   transform_hvfhv_trip_fact,
    "fhv_trip_fact":     transform_fhv_trip_fact,
    "taxi_zone_lookup":  transform_taxi_zone_lookup,
    "taxi_load_batch":   transform_taxi_load_batch,
}
