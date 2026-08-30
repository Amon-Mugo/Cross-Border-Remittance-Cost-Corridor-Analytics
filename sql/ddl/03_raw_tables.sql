-- used the data we read from the parquet files from the emr cluster of pyspark 
--  we used this command SELECT $1 FROM @REMITTANCE_CORRIDOR.RAW.REMITTANCE_CURATED_STAGE/clean/
  --(FILE_FORMAT => REMITTANCE_CORRIDOR.RAW.PARQUET_FORMAT, PATTERN => '.*\\.parquet')
--LIMIT 5;
-- which we used in 02_file_formats.sql

USE ROLE REMITTANCE_LOADER_ROLE;
USE DATABASE REMITTANCE_CORRIDOR;
USE SCHEMA RAW;

CREATE OR REPLACE TABLE REMITTANCE_RAW(
     "Standard Note"               STRING,
    "access point"                STRING,
    cc_number                     NUMBER(38,0),
    corridor                      STRING,
    date                          DATE,
    date_raw                      STRING,
    destination_code              STRING,
    destination_income            STRING,
    destination_lending           STRING,
    destination_name              STRING,
    destination_region            STRING,
    firm                          STRING,
    firm_type                     STRING,
    "fx margin"                   FLOAT,
    id                            NUMBER(38,0),
    "inter lcu bank fx"           FLOAT,
    "lcu amount"                  FLOAT,
    "lcu code"                    STRING,
    "lcu fee"                     FLOAT,
    "lcu fx rate"                 FLOAT,
    "payment instrument"          STRING,
    period                        STRING,
    period_quarter                NUMBER(1,0),
    period_year                   NUMBER(4,0),
    "pickup method"                STRING,
    "receiving network coverage"  STRING,
    send_amount                   FLOAT,
    "source_G8G20"                STRING,
    source_code                   STRING,
    source_income                 STRING,
    source_name                   STRING,
    "speed actual"                STRING,
    "total cost %"                FLOAT,
    transparent                   STRING

)

COMMENT = 'RAW landing table for cleaned/unpivoted remittance corridor data from the EMR pipeline';