-- Purpose: Incremental, per-quarter load procedure for REMITTANCE_RAW.
-- Each call targets one quarter's subfolder under the curated bucket
-- (e.g. <quarter_label>/clean/).
-- Incorporates explicit DELETE-then-COPY idempotency to safely support re-runs.
-- Logs each run to REMITTANCE_LOAD_HISTORY for audit.
USE ROLE REMITTANCE_LOADER_ROLE;
USE DATABASE REMITTANCE_CORRIDOR;
USE SCHEMA RAW;
CREATE OR REPLACE TABLE REMITTANCE_LOAD_HISTORY (
    load_id       NUMBER AUTOINCREMENT START 1 INCREMENT 1,
    quarter_label STRING,
    loaded_at     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    row_count     NUMBER,
    status        STRING,
    error_message STRING
)
COMMENT = 'Audit log of each REMITTANCE_RAW load run, one row per COPY INTO execution';
CREATE OR REPLACE PROCEDURE LOAD_REMITTANCE_RAW(QUARTER_LABEL STRING)
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    loaded_rows NUMBER DEFAULT 0;
    stage_path  STRING DEFAULT '@REMITTANCE_CURATED_STAGE/' || :QUARTER_LABEL || '/clean/';
    delete_sql  STRING;
    copy_sql    STRING;
BEGIN
    -- 1. Construct and execute DELETE query for explicit idempotency
    delete_sql := 'DELETE FROM REMITTANCE_RAW WHERE PERIOD = ''' || :QUARTER_LABEL || '''';
    EXECUTE IMMEDIATE :delete_sql;
    -- 2. Construct and execute dynamic COPY INTO statement
    copy_sql := 'COPY INTO REMITTANCE_RAW FROM ' || :stage_path ||
                ' FILE_FORMAT = (FORMAT_NAME = PARQUET_FORMAT)' ||
                ' PATTERN = ''.*\.parquet''' ||
                ' MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE' ||
                ' ON_ERROR = ABORT_STATEMENT';
    EXECUTE IMMEDIATE :copy_sql;
    -- 3. Capture post-load cumulative table row count
    SELECT COUNT(*) INTO :loaded_rows FROM REMITTANCE_RAW;
    -- 4. Record successful execution receipt in audit history
    INSERT INTO REMITTANCE_LOAD_HISTORY (quarter_label, row_count, status)
    VALUES (:QUARTER_LABEL, :loaded_rows, 'SUCCESS');
    RETURN 'Loaded quarter ' || :QUARTER_LABEL || '. Table now has ' || :loaded_rows || ' total rows.';
EXCEPTION
    WHEN OTHER THEN
        INSERT INTO REMITTANCE_LOAD_HISTORY (quarter_label, row_count, status, error_message)
        VALUES (:QUARTER_LABEL, 0, 'FAILED', :SQLERRM);
        RAISE;
END;
$$;
