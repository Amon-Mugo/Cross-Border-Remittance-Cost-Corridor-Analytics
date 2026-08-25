# tests/transform/test_clean_nulls.py
#
# Purpose: Verifies clean_geography_nulls only nulls '..' in the six scoped
# geography columns, leaves every other column untouched (including a
# legitimate '..' value elsewhere, which must NOT be nulled), and fails loudly
# if the schema doesn't contain the expected columns.

import pytest
from pyspark.sql import Row

from src.transform.clean_nulls import clean_geography_nulls, GEOGRAPHY_NULL_COLUMNS


def test_replaces_dotdot_in_geography_columns(spark):
    df = spark.createDataFrame(
        [
            Row(
                source_region="..",
                source_lending="IBRD",
                source_G8G20="..",
                destination_region="Sub-Saharan Africa",
                destination_lending="..",
                destination_G8G20="..",
                firm="MoneyGram",
            )
        ]
    )
    result = clean_geography_nulls(df).collect()[0]

    assert result["source_region"] is None
    assert result["source_G8G20"] is None
    assert result["destination_lending"] is None
    assert result["destination_G8G20"] is None
    assert result["source_lending"] == "IBRD"
    assert result["destination_region"] == "Sub-Saharan Africa"


def test_does_not_touch_dotdot_outside_scoped_columns(spark):
    """A '..' value in a non-geography column must survive unchanged —
    the null marker is only meaningful in the six scoped columns."""
    df = spark.createDataFrame(
        [
            Row(
                source_region="..",
                source_lending="..",
                source_G8G20="..",
                destination_region="..",
                destination_lending="..",
                destination_G8G20="..",
                firm="..",  # deliberately suspicious value outside scope
            )
        ]
    )
    result = clean_geography_nulls(df).collect()[0]

    assert result["firm"] == ".."


def test_raises_on_missing_expected_columns(spark):
    df = spark.createDataFrame([Row(source_region="..")])

    with pytest.raises(ValueError, match="Expected geography columns not found"):
        clean_geography_nulls(df)


def test_all_six_geography_columns_are_covered():
    """Guards against silently dropping a column from the scoped list."""
    assert GEOGRAPHY_NULL_COLUMNS == [
        "source_region",
        "source_lending",
        "source_G8G20",
        "destination_region",
        "destination_lending",
        "destination_G8G20",
    ]
