--this is acts as a an authentication bridge between snowflake and aws s3

CREATE STORAGE INTEGRATION REMITTANCE_S3_INTEGRATION
     TYPE = EXTERNAL_STAGE
     STORAGE_PROVIDER = 'S3'
    ENABLED = TRUE
     STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::<ACCOUNT_ID>:role/remittance-corridor-snowflake-access-<ACCOUNT_ID>'
     STORAGE_ALLOWED_LOCATIONS = ('s3://remittance-corridor-curated-data-bucket-<ACCOUNT_ID>/');


--RUN THAT FIRST TO CREATE THE STAGE

--run this to get the arn

DESC INTEGRATION REMITTANCE_S3_INTEGRATION;
