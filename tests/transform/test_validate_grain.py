# tests/transform/test_validate_grain.py
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

from src.transform.validate_grain import validate_grain

SCHEMA = StructType(
    [
        StructField("corridor", StringType(), True),
        StructField("firm", StringType(), True),
        StructField("payment instrument", StringType(), True),
        StructField("period", StringType(), True),
        StructField("send_amount", DoubleType(), True),
        StructField("fx margin", DoubleType(), True),
    ]
)


def test_validate_grain_no_duplicates_returns_all_rows_unchanged(spark):
    df = spark.createDataFrame(
        [
            ("US-MX", "FirmA", "Bank transfer", "2016_2Q", 200.0, 0.02),
            ("US-MX", "FirmB", "Bank transfer", "2016_2Q", 200.0, 0.03),
            ("US-KE", "FirmA", "Mobile wallet", "2016_2Q", 100.0, 0.01),
        ],
        SCHEMA,
    )

    clean_df, duplicates_report = validate_grain(df)

    assert clean_df.count() == 3
    assert duplicates_report.count() == 0


def test_validate_grain_drops_duplicates_and_reports_them(spark):
    df = spark.createDataFrame(
        [
            ("US-MX", "FirmA", "Bank transfer", "2016_2Q", 200.0, 0.02),
            ("US-MX", "FirmA", "Bank transfer", "2016_2Q", 200.0, 0.05),
            ("US-KE", "FirmA", "Mobile wallet", "2016_2Q", 100.0, 0.01),
        ],
        SCHEMA,
    )

    clean_df, duplicates_report = validate_grain(df)

    # one duplicate pair collapses to one row; the unique row is untouched
    assert clean_df.count() == 2
    assert duplicates_report.count() == 1

    clean_rows = {row["fx margin"] for row in clean_df.collect()}
    assert clean_rows == {0.02, 0.01}

    dup_row = duplicates_report.collect()[0]
    assert dup_row["corridor"] == "US-MX"
    assert dup_row["fx margin"] == 0.05
    assert dup_row["duplicate_count"] == 2


def test_validate_grain_reports_correct_count_for_triplicate(spark):
    df = spark.createDataFrame(
        [
            ("US-MX", "FirmA", "Bank transfer", "2016_2Q", 200.0, 0.01),
            ("US-MX", "FirmA", "Bank transfer", "2016_2Q", 200.0, 0.02),
            ("US-MX", "FirmA", "Bank transfer", "2016_2Q", 200.0, 0.03),
        ],
        SCHEMA,
    )

    clean_df, duplicates_report = validate_grain(df)

    assert clean_df.count() == 1
    assert duplicates_report.count() == 2
    for row in duplicates_report.collect():
        assert row["duplicate_count"] == 3


def test_validate_grain_clean_output_has_no_helper_columns(spark):
    df = spark.createDataFrame(
        [
            ("US-MX", "FirmA", "Bank transfer", "2016_2Q", 200.0, 0.02),
        ],
        SCHEMA,
    )

    clean_df, duplicates_report = validate_grain(df)

    assert set(clean_df.columns) == set(df.columns)
    assert "duplicate_count" in duplicates_report.columns
