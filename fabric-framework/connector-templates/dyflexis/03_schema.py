from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType,
    IntegerType, BooleanType, ArrayType
)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# SCHEMAS â€” StructType for spark.read.schema()
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_department_schema = StructType([
    StructField("id",             IntegerType(), True),
    StructField("name",           StringType(),  True),
    StructField("type",           StringType(),  True),
    StructField("created",        StringType(),  True),
    StructField("modified",       StringType(),  True),
    StructField("costCenterId",   IntegerType(), True),
    StructField("costCenterName", StringType(),  True),
    StructField("active",         BooleanType(), True),
])

_dept_group_level_2 = StructType([
    StructField("id",               IntegerType(),                     True),
    StructField("name",             StringType(),                      True),
    StructField("type",             StringType(),                      True),
    StructField("created",          StringType(),                      True),
    StructField("modified",         StringType(),                      True),
    StructField("costCenterId",     IntegerType(),                     True),
    StructField("costCenterName",   StringType(),                      True),
    StructField("active",           BooleanType(),                     True),
    StructField("departmentGroups", ArrayType(StringType()),           True),
    StructField("departments",      ArrayType(_department_schema),     True),
])

_dept_group_level_1 = StructType([
    StructField("id",               IntegerType(),                     True),
    StructField("name",             StringType(),                      True),
    StructField("type",             StringType(),                      True),
    StructField("created",          StringType(),                      True),
    StructField("modified",         StringType(),                      True),
    StructField("costCenterId",     IntegerType(),                     True),
    StructField("costCenterName",   StringType(),                      True),
    StructField("active",           BooleanType(),                     True),
    StructField("departmentGroups", ArrayType(_dept_group_level_2),    True),
    StructField("departments",      ArrayType(_department_schema),     True),
])

_contract_schema = StructType([
    StructField("contractReference", StringType(),  True),
    StructField("officeId",          IntegerType(), True),
    StructField("type",              IntegerType(), True),
    StructField("start",             StringType(),  True),
    StructField("end",               StringType(),  True),
    StructField("hoursPerWeek",      DoubleType(),  True),
    StructField("daysPerWeek",       DoubleType(),  True),
    StructField("hourlySalary",      DoubleType(),  True),
    StructField("maxHoursPerWeek",   DoubleType(),  True),
])

entity_schema_config = {

    "department_tree": StructType([
        StructField("id",               IntegerType(),                     True),
        StructField("name",             StringType(),                      True),
        StructField("type",             StringType(),                      True),
        StructField("created",          StringType(),                      True),
        StructField("modified",         StringType(),                      True),
        StructField("addressId",        IntegerType(),                     True),
        StructField("costCenterId",     IntegerType(),                     True),
        StructField("costCenterName",   StringType(),                      True),
        StructField("active",           BooleanType(),                     True),
        StructField("departmentGroups", ArrayType(_dept_group_level_1),    True),
        StructField("departments",      ArrayType(_department_schema),     True),
    ]),

    "employee": StructType([
        StructField("employeeId",            IntegerType(),                    True),
        StructField("initials",              StringType(),                     True),
        StructField("firstName",             StringType(),                     True),
        StructField("lastNamePrefix",        StringType(),                     True),
        StructField("lastName",              StringType(),                     True),
        StructField("nameFormat",            StringType(),                     True),
        StructField("maritalStatus",         StringType(),                     True),
        StructField("partnerInitials",       StringType(),                     True),
        StructField("partnerFirstName",      StringType(),                     True),
        StructField("partnerLastNamePrefix", StringType(),                     True),
        StructField("partnerLastName",       StringType(),                     True),
        StructField("gender",                StringType(),                     True),
        StructField("phoneNumber",           StringType(),                     True),
        StructField("phoneNumber2",          StringType(),                     True),
        StructField("email",                 StringType(),                     True),
        StructField("dateOfBirth",           StringType(),                     True),
        StructField("placeOfBirth",          StringType(),                     True),
        StructField("streetName",            StringType(),                     True),
        StructField("streetNumber",          StringType(),                     True),
        StructField("postalCode",            StringType(),                     True),
        StructField("city",                  StringType(),                     True),
        StructField("nationality",           StringType(),                     True),
        StructField("employmentStart",       StringType(),                     True),
        StructField("employmentEnd",         StringType(),                     True),
        StructField("personnelNumber",       StringType(),                     True),
        StructField("costCenter",            StringType(),                     True),
        StructField("probationDate",         StringType(),                     True),
        StructField("employerReferenceId",   StringType(),                     True),
        StructField("jobDescription",        StringType(),                     True),
        StructField("employments",           ArrayType(IntegerType()),         True),
        StructField("contracts",             ArrayType(_contract_schema),      True),
        StructField("customFields",          ArrayType(StringType()),          True),
    ]),

    "registered_hours": StructType([
        StructField("id",                   IntegerType(), True),
        StructField("employeeId",           IntegerType(), True),
        StructField("personnelNumber",      StringType(),  True),
        StructField("firstName",            StringType(),  True),
        StructField("infix",                StringType(),  True),
        StructField("lastName",             StringType(),  True),
        StructField("employeeCostCenter",   StringType(),  True),
        StructField("contractTypeId",       IntegerType(), True),
        StructField("contractType",         StringType(),  True),
        StructField("officeId",             IntegerType(), True),
        StructField("officeName",           StringType(),  True),
        StructField("departmentId",         IntegerType(), True),
        StructField("departmentName",       StringType(),  True),
        StructField("costCenterId",         IntegerType(), True),
        StructField("costCenterName",       StringType(),  True),
        StructField("costCenterCode",       StringType(),  True),
        StructField("startDateTime",        StringType(),  True),
        StructField("endDateTime",          StringType(),  True),
        StructField("hourType",             StringType(),  True),
        StructField("hours",                DoubleType(),  True),
        StructField("status",               StringType(),  True),
        StructField("breakMinutes",         IntegerType(), True),
        StructField("duration",             IntegerType(), True),
        StructField("kilometers",           DoubleType(),  True),
        StructField("customExpenses",       ArrayType(StringType()), True),
        StructField("remark",               StringType(),  True),
    ]),
}
