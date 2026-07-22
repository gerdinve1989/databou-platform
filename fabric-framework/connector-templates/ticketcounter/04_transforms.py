from pyspark.sql.types import StringType
from pyspark.sql.functions import (
    col, concat_ws, when, cast, lit, explode, explode_outer,
    to_timestamp, to_date, concat
)
from pyspark.sql import DataFrame


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# TRANSFORMS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def transform_baskets(df: DataFrame) -> DataFrame:
    return df.select(
        concat(col("Resort"), lit("_"), col("BasketKey")).alias("Id"),
        col("Resort"),
        col("BasketKey").alias("MandjeSleutel"),
        col("BasketNumber").alias("MandjeNummer"),
        col("BasketConfirmed").alias("MandjeBevestigd"),
        col("ExternalBasketNumber").alias("ExternMandjeNummer"),
        col("ExternalInvoiceId").alias("ExternFactuurId"),
        col("PosFirstName").alias("PosVoornaam"),
        col("PosMiddleName").alias("PosTussenvoegsel"),
        col("PosLastName").alias("PosAchternaam"),
        col("PosName").alias("PosNaam"),
        col("PosGroupName").alias("PosGroepNaam"),
        col("Contact"),
    )


def transform_ticket_scans(df: DataFrame) -> DataFrame:
    return df.select(
        concat(col("Resort"), lit("_"), col("ScanId")).alias("Id"),
        col("Resort"),
        col("ScanId"),
        col("TicketCode"),
        col("ScanGroupName").alias("ScanGroepNaam"),
        col("DeviceID").alias("ApparaatId"),
        col("Type"),
        col("ScanDate").cast("timestamp").alias("ScanDatum"),
        col("ReservationKey").alias("FK_Reservering_Sleutel"),
        col("SubscriptionKey").alias("FK_Abonnement_Sleutel"),
        col("SubscriptionProductKey").alias("FK_AbonnementProduct_Sleutel"),
        col("SubscriptionTemplateKey").alias("FK_AbonnementTemplate_Sleutel"),
        col("EventKey").alias("FK_Evenement_Sleutel"),
        col("PerformanceKey").alias("FK_Voorstelling_Sleutel"),
        col("PerformanceSectionKey").alias("FK_VoorstellingSectie_Sleutel"),
        col("ProductName").alias("ProductNaam"),
        col("InternalId").alias("InternId"),
        col("ProductInternalId").alias("ProductInternId"),
        col("Name").alias("Naam"),
        col("EMail").alias("Email"),
        col("FirstName").alias("Voornaam"),
        col("Middle").alias("Tussenvoegsel"),
        col("LastName").alias("Achternaam"),
        col("CompanyName").alias("Bedrijfsnaam"),
        col("PhoneNumber").alias("Telefoonnummer"),
        col("Street").alias("Straat"),
        col("HouseNumber").alias("Huisnummer"),
        col("PostalCode").alias("Postcode"),
        col("CityName").alias("Plaatsnaam"),
        col("CountryName").alias("Landnaam"),
        col("Lat").alias("Breedtegraad"),
        col("Lon").alias("Lengtegraad"),
        col("ValidFrom").cast("timestamp").alias("GeldigVanaf"),
        col("ValidTo").cast("timestamp").alias("GeldigTot"),
        col("ReservationNumber").alias("ReserveringsNummer"),
        col("PriceKey").alias("PrijsSleutel"),
        col("Price").alias("Prijs"),
        col("OriginalPrice").alias("OriginelePrijs"),
        col("BuyingPrice").alias("InkoopPrijs"),
        col("ExternalID").alias("ExternId"),
        col("ExternalReservationNumber").alias("ExternReserveringsNummer"),
        col("ExtraInfo1"),
        col("ExtraInfo2"),
        col("ExtraInfo3"),
        col("TestPayment").alias("TestBetaling"),
        col("ReceiveNewsletter").alias("OntvangtNieuwsbrief"),
    )


def transform_sold_tickets(df: DataFrame) -> DataFrame:
    return df.select(
        concat(col("Resort"), lit("_"), col("TicketCode")).alias("Id"),
        col("Resort"),
        col("TicketCode"),
        col("Type"),
        col("ReservationKey").alias("FK_Reservering_Sleutel"),
        col("EventKey").alias("FK_Evenement_Sleutel"),
        col("PerformanceKey").alias("FK_Voorstelling_Sleutel"),
        col("PerformanceSectionKey").alias("FK_VoorstellingSectie_Sleutel"),
        col("ContactHolderKey").alias("FK_ContactHouder_Sleutel"),
        col("ProductName").alias("ProductNaam"),
        col("SaleDate").cast("timestamp").alias("VerkoopDatum"),
        col("TotalPrice").alias("TotalePrijs"),
        col("Price").alias("Prijs"),
        col("OriginalPrice").alias("OriginelePrijs"),
        col("BuyingPrice").alias("InkoopPrijs"),
        col("NrOfSeats").alias("AantalStoelen"),
        col("Channel").alias("Kanaal"),
        col("SalesChannel").alias("VerkoopKanaal"),
        col("PaymentMethod").alias("BetaalMethode"),
        col("Name").alias("Naam"),
        col("EMail").alias("Email"),
        col("FirstName").alias("Voornaam"),
        col("Middle").alias("Tussenvoegsel"),
        col("LastName").alias("Achternaam"),
        col("CompanyName").alias("Bedrijfsnaam"),
        col("PhoneNumber").alias("Telefoonnummer"),
        col("Street").alias("Straat"),
        col("HouseNumber").alias("Huisnummer"),
        col("PostalCode").alias("Postcode"),
        col("CityName").alias("Plaatsnaam"),
        col("CountryName").alias("Landnaam"),
        col("Lat").alias("Breedtegraad"),
        col("Lon").alias("Lengtegraad"),
        col("ValidFrom").cast("timestamp").alias("GeldigVanaf"),
        col("ValidTo").cast("timestamp").alias("GeldigTot"),
        col("CapacityDate").cast("date").alias("CapaciteitDatum"),
        col("CapacityStartDate").cast("date").alias("CapaciteitStartDatum"),
        col("CapacityStartTime").alias("CapaciteitStartTijd"),
        col("CapacityEndTime").alias("CapaciteitEindTijd"),
        col("ReservationNumber").alias("ReserveringsNummer"),
        col("ResellerName").alias("ResellerNaam"),
        col("PriceKey").alias("PrijsSleutel"),
        col("Language").alias("Taal"),
        col("LanguageCode").alias("TaalCode"),
        col("BrancheID").alias("VestigingId"),
        col("CancelDate").cast("timestamp").alias("AnnuleringsDatum"),
        col("ConfirmedDate").cast("timestamp").alias("BevestigdDatum"),
        col("PosGroupTitle").alias("PosGroepTitel"),
        col("PosTitle").alias("PosTitel"),
        col("PosContact"),
        col("ExternalReservationNumber").alias("ExternReserveringsNummer"),
        col("ExternalID").alias("ExternId"),
        col("ExtraInfo1"),
        col("ExtraInfo2"),
        col("ExtraInfo3"),
        col("TestPayment").alias("TestBetaling"),
        col("ReceiveNewsLetter").alias("OntvangtNieuwsbrief"),
        col("VatNumber").alias("BtwNummer"),
        col("VatLow").alias("BtwLaag"),
        col("VatMiddle").alias("BtwMiddel"),
        col("VatHigh").alias("BtwHoog"),
        col("AmountExVatLow").alias("BedragExBtwLaag"),
        col("AmountExVatMiddle").alias("BedragExBtwMiddel"),
        col("AmountExVatHigh").alias("BedragExBtwHoog"),
        col("CashBooking").alias("ContantBoeking"),
    )


def transform_sold_subscriptions(df: DataFrame) -> DataFrame:
    return df.select(
        concat(col("Resort"), lit("_"), col("SubscriptionKey")).alias("Id"),
        col("Resort"),
        col("SubscriptionKey").alias("AbonnementSleutel"),
        col("Type"),
        col("ReservationKey").alias("FK_Reservering_Sleutel"),
        col("SubscriptionTemplateKey").alias("FK_AbonnementTemplate_Sleutel"),
        col("SubscriptionHolderKey").alias("FK_AbonnementHouder_Sleutel"),
        col("ProductName").alias("ProductNaam"),
        col("SaleDate").cast("timestamp").alias("VerkoopDatum"),
        col("Price").alias("Prijs"),
        col("Renewal").alias("Verlenging"),
        col("Channel").alias("Kanaal"),
        col("PaymentMethod").alias("BetaalMethode"),
        col("NrOfSubscriptionProducts").alias("AantalAbonnementProducten"),
        col("InternalId").alias("InternId"),
        col("Name").alias("Naam"),
        col("EMail").alias("Email"),
        col("FirstName").alias("Voornaam"),
        col("Middle").alias("Tussenvoegsel"),
        col("LastName").alias("Achternaam"),
        col("CompanyName").alias("Bedrijfsnaam"),
        col("PhoneNumber").alias("Telefoonnummer"),
        col("Street").alias("Straat"),
        col("HouseNumber").alias("Huisnummer"),
        col("PostalCode").alias("Postcode"),
        col("CityName").alias("Plaatsnaam"),
        col("CountryName").alias("Landnaam"),
        col("Lat").alias("Breedtegraad"),
        col("Lon").alias("Lengtegraad"),
        col("ValidFrom").cast("timestamp").alias("GeldigVanaf"),
        col("ValidTo").cast("timestamp").alias("GeldigTot"),
        col("Gender").alias("Geslacht"),
        col("BirthDate").cast("date").alias("Geboortedatum"),
        col("CancelDate").cast("timestamp").alias("AnnuleringsDatum"),
        col("ReservationNumber").alias("ReserveringsNummer"),
        col("Language").alias("Taal"),
        col("LanguageCode").alias("TaalCode"),
        col("LoyaltyLevel").alias("LoyaliteitNiveau"),
        col("PosGroupTitle").alias("PosGroepTitel"),
        col("PosTitle").alias("PosTitel"),
        col("PosContact"),
        col("ExternalID").alias("ExternId"),
        col("TestPayment").alias("TestBetaling"),
        col("ReceiveNewsLetter").alias("OntvangtNieuwsbrief"),
    )


def transform_cancellations(df: DataFrame) -> DataFrame:
    id_col = concat(col("Resort"), lit("_"), col("ReservationKey"), lit("_"), col("ValidFrom"))
    w = Window.partitionBy(id_col).orderBy(col("CancelDate").desc())
    return (
        df
        .withColumn("_id", id_col)
        .withColumn("_rn", row_number().over(w))
        .filter(col("_rn") == 1)
        .select(
            col("_id").alias("Id"),
            col("Resort"),
            col("ReservationKey").alias("ReserveringsSleutel"),
            col("ReservationNumber").alias("ReserveringsNummer"),
            col("ExternalReservationNumber").alias("ExternReserveringsNummer"),
            col("CancelDate").cast("timestamp").alias("AnnuleringsDatum"),
            col("Price").alias("Prijs"),
            col("OriginalPrice").alias("OriginelePrijs"),
            col("NrOfSeats").alias("AantalStoelen"),
            col("ValidFrom").cast("timestamp").alias("GeldigVanaf"),
            col("ValidTo").cast("timestamp").alias("GeldigTot"),
        )
    )


entity_transform_config = {
    "baskets":            transform_baskets,
    "ticket_scans":       transform_ticket_scans,
    "sold_tickets":       transform_sold_tickets,
    "sold_subscriptions": transform_sold_subscriptions,
    "cancellations":      transform_cancellations,
}
