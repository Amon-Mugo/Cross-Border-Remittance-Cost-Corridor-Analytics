# tests/transform/test_parse_dates.py
#
# Purpose: Verifies both known date formats parse correctly into a single
# date column, an unrecognized format yields null rather than raising, and
# period strings split into correct integer year/quarter columns.

import datetime

import pytest
from pyspark.sql import Row

from src.transform.parse_dates import parse_date_column, parse_period_column


def test_parses_short_date_format(spark):
    df = spark.createDataFrame([Row(date="11/May/2016")])
    result = parse_date_column(df).collect()[0]

    assert result["date"] == datetime.date(2016, 5, 11)
    assert result["date_raw"] == "11/May/2016"


def test_parses_long_date_format(spark):
    df = spark.createDataFrame([Row(date="2021-05-26 00:00:00")])
    result = parse_date_column(df).collect()[0]

    assert result["date"] == datetime.date(2021, 5, 26)
    assert result["date_raw"] == "2021-05-26 00:00:00"


def test_unrecognized_date_format_becomes_null(spark):
    """An unexpected format should not crash the pipeline — it should
    surface as null so it can be caught by downstream validation."""
    df = spark.createDataFrame([Row(date="not-a-date")])
    result = parse_date_column(df).collect()[0]

    assert result["date"] is None
    assert result["date_raw"] == "not-a-date"


def test_raises_when_date_column_missing(spark):
    df = spark.createDataFrame([Row(not_date="x")])

    with pytest.raises(ValueError, match="Expected 'date' column not found"):
        parse_date_column(df)


def test_parses_period_into_year_and_quarter(spark):
    df = spark.createDataFrame([Row(period="2016_2Q")])
    result = parse_period_column(df).collect()[0]

    assert result["period_year"] == 2016
    assert result["period_quarter"] == 2
    assert result["period"] == "2016_2Q"  # original preserved


def test_raises_when_period_column_missing(spark):
    df = spark.createDataFrame([Row(not_period="x")])

    with pytest.raises(ValueError, match="Expected 'period' column not found"):
        parse_period_column(df)
