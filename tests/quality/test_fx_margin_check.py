# tests/quality/test_fx_margin_check.py
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

from src.quality.fx_margin_check import check_fx_margin

SCHEMA = StructType(
    [
        StructField("corridor", StringType(), True),
        StructField("firm", StringType(), True),
        StructField("period", StringType(), True),
        StructField("fx margin", DoubleType(), True),
    ]
)


def test_fx_margin_check_flags_negative_margins(spark):
    df = spark.createDataFrame(
        [
            ("US-MX", "FirmA", "2016_2Q", 0.02),
            ("US-MX", "FirmB", "2016_2Q", -0.01),
            ("US-KE", "FirmA", "2016_2Q", 0.05),
        ],
        SCHEMA,
    )

    clean_df, flagged_report = check_fx_margin(df)

    assert clean_df.count() == 2
    assert flagged_report.count() == 1
    assert flagged_report.collect()[0]["firm"] == "FirmB"


def test_fx_margin_check_keeps_null_margin_in_clean_df(spark):
    df = spark.createDataFrame(
        [
            ("US-MX", "FirmA", "2016_2Q", None),
        ],
        SCHEMA,
    )

    clean_df, flagged_report = check_fx_margin(df)

    assert clean_df.count() == 1
    assert flagged_report.count() == 0


def test_fx_margin_check_zero_margin_is_not_flagged(spark):
    df = spark.createDataFrame(
        [
            ("US-MX", "FirmA", "2016_2Q", 0.0),
        ],
        SCHEMA,
    )

    clean_df, flagged_report = check_fx_margin(df)

    assert clean_df.count() == 1
    assert flagged_report.count() == 0


def test_fx_margin_check_no_negatives_returns_all_rows_clean(spark):
    df = spark.createDataFrame(
        [
            ("US-MX", "FirmA", "2016_2Q", 0.02),
            ("US-KE", "FirmA", "2016_2Q", 0.05),
        ],
        SCHEMA,
    )

    clean_df, flagged_report = check_fx_margin(df)

    assert clean_df.count() == 2
    assert flagged_report.count() == 0
