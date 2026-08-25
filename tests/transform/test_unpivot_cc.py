# tests/transform/test_unpivot_cc.py
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

from src.transform.unpivot_cc import unpivot_cc

SCHEMA = StructType(
    [
        StructField("corridor", StringType(), True),
        StructField("firm", StringType(), True),
        StructField("period", StringType(), True),
        StructField("cc1 lcu amount", DoubleType(), True),
        StructField("cc1 denomination amount", DoubleType(), True),
        StructField("cc1 lcu code", StringType(), True),
        StructField("cc1 lcu fee", DoubleType(), True),
        StructField("cc1 lcu fx rate", DoubleType(), True),
        StructField("cc1 fx margin", DoubleType(), True),
        StructField("cc1 total cost %", DoubleType(), True),
        StructField("cc2 lcu amount", DoubleType(), True),
        StructField("cc2 denomination amount", DoubleType(), True),
        StructField("cc2 lcu code", StringType(), True),
        StructField("cc2 lcu fee", DoubleType(), True),
        StructField("cc2 lcu fx rate", DoubleType(), True),
        StructField("cc2 fx margin", DoubleType(), True),
        StructField("cc2 total cost %", DoubleType(), True),
    ]
)


def test_unpivot_cc_splits_both_sides_and_carries_shared_columns(spark):
    df = spark.createDataFrame(
        [
            (
                "US-MX",
                "FirmA",
                "2016_2Q",
                # cc1
                204.0,
                200.0,
                "USD",
                4.0,
                1.0,
                0.02,
                2.0,
                # cc2
                510.0,
                500.0,
                "MXN",
                10.0,
                18.5,
                0.05,
                2.0,
            ),
        ],
        SCHEMA,
    )

    result = unpivot_cc(df).orderBy("cc_number").collect()

    assert len(result) == 2

    cc1_row, cc2_row = result

    # shared columns carry through unchanged onto both output rows
    for row in (cc1_row, cc2_row):
        assert row["corridor"] == "US-MX"
        assert row["firm"] == "FirmA"
        assert row["period"] == "2016_2Q"

    # cc1 side: driving field renamed to send_amount, other subfields
    # stripped of their prefix and carried through with correct values
    assert cc1_row["cc_number"] == 1
    assert cc1_row["send_amount"] == 200.0
    assert cc1_row["lcu amount"] == 204.0
    assert cc1_row["lcu code"] == "USD"
    assert cc1_row["lcu fee"] == 4.0
    assert cc1_row["lcu fx rate"] == 1.0
    assert cc1_row["fx margin"] == 0.02
    assert cc1_row["total cost %"] == 2.0

    # cc2 side: same checks, confirms no cross-contamination between sides
    assert cc2_row["cc_number"] == 2
    assert cc2_row["send_amount"] == 500.0
    assert cc2_row["lcu amount"] == 510.0
    assert cc2_row["lcu code"] == "MXN"
    assert cc2_row["lcu fee"] == 10.0
    assert cc2_row["lcu fx rate"] == 18.5
    assert cc2_row["fx margin"] == 0.05
    assert cc2_row["total cost %"] == 2.0


def test_unpivot_cc_drops_null_driving_amount(spark):
    df = spark.createDataFrame(
        [
            (
                "US-MX",
                "FirmA",
                "2016_2Q",
                # cc1
                204.0,
                200.0,
                "USD",
                4.0,
                1.0,
                0.02,
                2.0,
                # cc2 — null denomination amount
                None,
                None,
                "MXN",
                10.0,
                18.5,
                0.05,
                2.0,
            ),
        ],
        SCHEMA,
    )

    result = unpivot_cc(df).collect()

    # cc2 side has a null denomination amount and must be dropped entirely,
    # not kept as a row with a null send_amount
    assert len(result) == 1
    assert result[0]["cc_number"] == 1
    assert result[0]["send_amount"] == 200.0
    assert result[0]["lcu code"] == "USD"


def test_unpivot_cc_drops_both_sides_when_both_amounts_null(spark):
    df = spark.createDataFrame(
        [
            (
                "US-MX",
                "FirmA",
                "2016_2Q",
                None,
                None,
                "USD",
                4.0,
                1.0,
                0.02,
                2.0,
                None,
                None,
                "MXN",
                10.0,
                18.5,
                0.05,
                2.0,
            ),
        ],
        SCHEMA,
    )

    result = unpivot_cc(df).collect()

    # entire source row is dropped when neither side has a driving amount
    assert len(result) == 0
