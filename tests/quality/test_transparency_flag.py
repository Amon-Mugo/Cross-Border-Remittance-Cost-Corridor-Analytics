# tests/quality/test_transparency_flag.py
from pyspark.sql.types import StructType, StructField, StringType

from src.quality.transparency_flag import check_transparency

SCHEMA = StructType(
    [
        StructField("corridor", StringType(), True),
        StructField("firm", StringType(), True),
        StructField("period", StringType(), True),
        StructField("transparent", StringType(), True),
    ]
)


def test_transparency_flag_flags_no_regardless_of_case(spark):
    df = spark.createDataFrame(
        [
            ("US-MX", "FirmA", "2016_2Q", "Yes"),
            ("US-MX", "FirmB", "2016_2Q", "no"),
            ("US-KE", "FirmA", "2016_2Q", "No"),
            ("US-KE", "FirmB", "2016_2Q", " NO "),
        ],
        SCHEMA,
    )

    clean_df, flagged_report = check_transparency(df)

    assert clean_df.count() == 1
    assert flagged_report.count() == 3
    flagged_firms = {row["firm"] for row in flagged_report.collect()}
    assert flagged_firms == {"FirmB", "FirmA"}


def test_transparency_flag_yes_regardless_of_case_is_clean(spark):
    df = spark.createDataFrame(
        [
            ("US-MX", "FirmA", "2016_2Q", "yes"),
            ("US-MX", "FirmB", "2016_2Q", "Yes"),
            ("US-KE", "FirmA", "2016_2Q", " YES "),
        ],
        SCHEMA,
    )

    clean_df, flagged_report = check_transparency(df)

    assert clean_df.count() == 3
    assert flagged_report.count() == 0


def test_transparency_flag_keeps_null_in_clean_df(spark):
    df = spark.createDataFrame(
        [
            ("US-MX", "FirmA", "2016_2Q", None),
        ],
        SCHEMA,
    )

    clean_df, flagged_report = check_transparency(df)

    assert clean_df.count() == 1
    assert flagged_report.count() == 0


def test_transparency_flag_no_negatives_returns_all_rows_clean(spark):
    df = spark.createDataFrame(
        [
            ("US-MX", "FirmA", "2016_2Q", "Yes"),
            ("US-KE", "FirmA", "2016_2Q", "yes"),
        ],
        SCHEMA,
    )

    clean_df, flagged_report = check_transparency(df)

    assert clean_df.count() == 2
    assert flagged_report.count() == 0
