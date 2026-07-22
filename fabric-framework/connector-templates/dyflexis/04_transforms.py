from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType,
    IntegerType, BooleanType, ArrayType, TimestampType, DateType
)
from pyspark.sql.functions import (
    col, concat_ws, when, cast, lit, explode, explode_outer,
    to_timestamp, to_date, concat, from_utc_timestamp
)
from pyspark.sql import DataFrame


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# TRANSFORMS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def transform_employee(df: DataFrame) -> DataFrame:
    return df.select(
                col('employeeId').alias('MedewerkerId'),
                to_date(col('dateOfBirth')).alias('Geboortedatum'),
                concat_ws(' ',
                    when(col('firstName') != '', col('firstName')),
                    when(col('lastNamePrefix') != '', col('lastNamePrefix')),
                    when(col('lastName') != '', col('lastName'))
                ).alias('Naam'),
                to_date(col('employmentStart')).alias('DienstverbandStart'),
                to_date(col('employmentEnd')).alias('DienstverbandEinde'),
                col('personnelNumber').alias('Personeelsnummer'),
                col('costCenter').alias('Kostenplaats')
            )

def transform_employee_contract(df: DataFrame) -> DataFrame:
    return (
        df
        .withColumn('contract',
                explode('contracts')
            ).select(
                col('contract.contractReference').alias('Id'),
                col('employeeId').alias('FK_Medewerker_Id'),
                col('contract.officeId').alias('VestigingId'),
                col('contract.type').alias('ContractType'),
                to_date(col('contract.start')).alias('StartDatum'),
                to_date(col('contract.end')).alias('EindDatum'),
                col('contract.hoursPerWeek').alias('UrenPerWeek'),
                col('contract.daysPerWeek').alias('DagenPerWeek'),
                col('contract.hourlySalary').alias('Uurloon'),
                col('contract.maxHoursPerWeek').alias('MaxUrenPerWeek')
            ).distinct()
    )


def transform_department_tree(df: DataFrame) -> DataFrame:
    _cols = ['Id', 'Naam', 'Type', 'AangemaaktOp', 'GewijzigdOp', 'KostenplaatsId', 'KostenplaatsNaam', 'Actief', 'ParentId']

    df_offices = df.select(
        col('id').cast(StringType()).alias('Id'),
        col('name').alias('Naam'),
        col('type').alias('Type'),
        col('created').alias('AangemaaktOp'),
        col('modified').alias('GewijzigdOp'),
        col('costCenterId').alias('KostenplaatsId'),
        col('costCenterName').alias('KostenplaatsNaam'),
        col('active').alias('Actief'),
        lit(None).cast(StringType()).alias('ParentId')
    )

    df_dept_l0 = (df
        .withColumn('dept', explode_outer('departments'))
        .select(
            col('dept.id').cast(StringType()).alias('Id'),
            col('dept.name').alias('Naam'),
            col('dept.type').alias('Type'),
            col('dept.created').alias('AangemaaktOp'),
            col('dept.modified').alias('GewijzigdOp'),
            col('dept.costCenterId').alias('KostenplaatsId'),
            col('dept.costCenterName').alias('KostenplaatsNaam'),
            col('dept.active').alias('Actief'),
            col('id').cast(StringType()).alias('ParentId')
        ).filter(col('Id').isNotNull())
    )

    df_dg_l1 = (df
        .withColumn('dg1', explode_outer('departmentGroups'))
        .select(
            col('dg1.id').cast(StringType()).alias('Id'),
            col('dg1.name').alias('Naam'),
            col('dg1.type').alias('Type'),
            col('dg1.created').alias('AangemaaktOp'),
            col('dg1.modified').alias('GewijzigdOp'),
            col('dg1.costCenterId').alias('KostenplaatsId'),
            col('dg1.costCenterName').alias('KostenplaatsNaam'),
            col('dg1.active').alias('Actief'),
            col('id').cast(StringType()).alias('ParentId')
        ).filter(col('Id').isNotNull())
    )

    df_dept_l1 = (df
        .withColumn('dg1', explode_outer('departmentGroups'))
        .withColumn('dept', explode_outer('dg1.departments'))
        .select(
            col('dept.id').cast(StringType()).alias('Id'),
            col('dept.name').alias('Naam'),
            col('dept.type').alias('Type'),
            col('dept.created').alias('AangemaaktOp'),
            col('dept.modified').alias('GewijzigdOp'),
            col('dept.costCenterId').alias('KostenplaatsId'),
            col('dept.costCenterName').alias('KostenplaatsNaam'),
            col('dept.active').alias('Actief'),
            col('dg1.id').cast(StringType()).alias('ParentId')
        ).filter(col('Id').isNotNull())
    )

    df_dg_l2 = (df
        .withColumn('dg1', explode_outer('departmentGroups'))
        .withColumn('dg2', explode_outer('dg1.departmentGroups'))
        .select(
            col('dg2.id').cast(StringType()).alias('Id'),
            col('dg2.name').alias('Naam'),
            col('dg2.type').alias('Type'),
            col('dg2.created').alias('AangemaaktOp'),
            col('dg2.modified').alias('GewijzigdOp'),
            col('dg2.costCenterId').alias('KostenplaatsId'),
            col('dg2.costCenterName').alias('KostenplaatsNaam'),
            col('dg2.active').alias('Actief'),
            col('dg1.id').cast(StringType()).alias('ParentId')
        ).filter(col('Id').isNotNull())
    )

    df_dept_l2 = (df
        .withColumn('dg1', explode_outer('departmentGroups'))
        .withColumn('dg2', explode_outer('dg1.departmentGroups'))
        .withColumn('dept', explode_outer('dg2.departments'))
        .select(
            col('dept.id').cast(StringType()).alias('Id'),
            col('dept.name').alias('Naam'),
            col('dept.type').alias('Type'),
            col('dept.created').alias('AangemaaktOp'),
            col('dept.modified').alias('GewijzigdOp'),
            col('dept.costCenterId').alias('KostenplaatsId'),
            col('dept.costCenterName').alias('KostenplaatsNaam'),
            col('dept.active').alias('Actief'),
            col('dg2.id').cast(StringType()).alias('ParentId')
        ).filter(col('Id').isNotNull())
    )

    return (
        df_offices.select(_cols)
        .union(df_dept_l0.select(_cols))
        .union(df_dg_l1.select(_cols))
        .union(df_dept_l1.select(_cols))
        .union(df_dg_l2.select(_cols))
        .union(df_dept_l2.select(_cols))
        .distinct()
    )


def transform_registered_hours(df: DataFrame) -> DataFrame:
    return df.select(
            col('id').alias('Id'),
            col('employeeId').alias('FK_Medewerker_Id'),
            col('departmentId').alias('FK_Afdeling_Id'),
            col('personnelNumber').alias('Personeelsnummer'),
            concat_ws(' ',
                when(col('firstName') != '', col('firstName')),
                when(col('infix') != '', col('infix')),
                when(col('lastName') != '', col('lastName'))
            ).alias('Naam'),
            col('employeeCostCenter').alias('MedewerkerKostenplaats'),
            col('contractTypeId').alias('ContractTypeId'),
            col('contractType').alias('ContractType'),
            col('startDateTime').cast(DateType()).alias('Datum'),
            col('startDateTime').cast(TimestampType()).alias('StartTijdstip'),
            col('endDateTime').cast(TimestampType()).alias('EindTijdstip'),
            col('hourType').alias('UurType'),
            col('hours').alias('Uren'),
            col('status').alias('Status'),
            col('breakMinutes').alias('PauzeMinuten'),
            col('duration').alias('Duur'),
        )


entity_transform_config = {
    "employee":          transform_employee,
    "employee_contract": transform_employee_contract,
    "department_tree":   transform_department_tree,
    "registered_hours":  transform_registered_hours,
}
