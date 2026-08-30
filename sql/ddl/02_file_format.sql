-- THIS creates a parquet file for reading crated pipeline output

USE ROLE REMITTANCE_LOADER_ROLE;
USE DATABASE REMITTACE_CORRIDOR;
USE SCHEMA RAW;

CREATE OR REPLACE FILE FORMAT PARQUET_FORMAT
    TYPE = PARQUET
    COMMENT = 'Parquet file format for reading the pipeline.py output';