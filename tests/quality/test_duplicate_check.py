# tests/quality/test_duplicate_check.py
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

from src.quality.duplicate_check import check_duplicates

SCHEMA = StructType(
    [
        StructField("corridor", StringType(), True),
        StructField("firm", StringType(), True),
        StructField("period", StringType(), True),
        StructField("payment instrument", StringType(), True),
        StructField("send_amount", DoubleType(), True),
    ]
)


def test_duplicate_check_no_duplicates_returns_all_rows_clean(spark):
    df = spark.createDataFrame(
        [
            ("US-MX", "FirmA", "2016_2Q", "Bank transfer", 200.0),
            ("US-MX", "FirmB", "2016_2Q", "Bank transfer", 200.0),
            ("US-KE", "FirmA", "2016_2Q", "Mobile wallet", 100.0),
        ],
        SCHEMA,
    )

    clean_df, flagged_report = check_duplicates(df)

    assert clean_df.count() == 3
    assert flagged_report.count() == 0


def test_duplicate_check_flags_both_rows_of_a_duplicate_pair(spark):
    df = spark.createDataFrame(
        [
            ("US-MX", "FirmA", "2016_2Q", "Bank transfer", 200.0),
            ("US-MX", "FirmA", "2016_2Q", "Bank transfer", 200.0),
            ("US-KE", "FirmA", "2016_2Q", "Mobile wallet", 100.0),
        ],
        SCHEMA,
    )

    clean_df, flagged_report = check_duplicates(df)

    # both rows sharing the full grain key (corridor, firm, period,
    # instrument, send_amount) are flagged as true duplicates
    assert clean_df.count() == 1
    assert flagged_report.count() == 2
    for row in flagged_report.collect():
        assert row["duplicate_count"] == 2


def test_duplicate_check_triplicate_reports_all_three(spark):
    df = spark.createDataFrame(
        [
            ("US-MX", "FirmA", "2016_2Q", "Bank transfer", 200.0),
            ("US-MX", "FirmA", "2016_2Q", "Bank transfer", 200.0),
            ("US-MX", "FirmA", "2016_2Q", "Bank transfer", 200.0),
        ],
        SCHEMA,
    )

    clean_df, flagged_report = check_duplicates(df)

    assert clean_df.count() == 0
    assert flagged_report.count() == 3
    for row in flagged_report.collect():
        assert row["duplicate_count"] == 3


def test_duplicate_check_clean_output_has_no_helper_columns(spark):
    df = spark.createDataFrame(
        [
            ("US-MX", "FirmA", "2016_2Q", "Bank transfer", 200.0),
        ],
        SCHEMA,
    )

    clean_df, flagged_report = check_duplicates(df)

    assert set(clean_df.columns) == set(df.columns)
    assert "duplicate_count" in flagged_report.columns
