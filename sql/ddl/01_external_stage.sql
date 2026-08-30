-- this points to the s3 bucket where the data is stored
-- after given authentication and role by 03_storage_integration.sql

USE ROLE REMITTANCE_LOADER_ROLE;
USE DATABASE REMITTANCE_CORRIDOR;
USE SCHEMA RAW;

CREATE OR REPLACE EXTERNAL STAGE REMITTANCE_CURATED_STAGE
     URL = 's3://remittance-corridor-curated-data-bucket-<ACCOUNT_ID>/'
     STORAGE_INTEGRATION = REMITTANCE_S3_INTEGRATION
     COMMENT = 'Points at curated bucket output of the pyspark pipeline(clean+quantity_reports)';