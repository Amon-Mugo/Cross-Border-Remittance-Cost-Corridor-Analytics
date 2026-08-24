# tests/transform/test_load_raw.py
#
# Purpose: Verifies load_raw_parquet enforces column-count schema drift
# detection (hard fail) and does not raise on row-count differences
# (expected to grow quarterly, only logged as a warning).

import pytest

from src.transform.load_raw import load_raw_parquet, EXPECTED_COLUMN_COUNT


def test_loads_parquet_successfully_regardless_of_row_count(spark, tmp_path):
    """Row count differing from the baseline must NOT raise — this dataset
    grows every quarter and that's expected, not an error."""
    columns = [f"col_{i}" for i in range(EXPECTED_COLUMN_COUNT)]
    row = {c: "value" for c in columns}

    df = spark.createDataFrame([row])  # only 1 row, nowhere near EXPECTED_ROW_COUNT
    out_path = str(tmp_path / "test.parquet")
    df.write.parquet(out_path)

    result = load_raw_parquet(spark, out_path)

    assert result.count() == 1
    assert len(result.columns) == EXPECTED_COLUMN_COUNT


def test_raises_on_wrong_column_count(spark, tmp_path):
    df = spark.createDataFrame([{"only_one_column": "x"}])
    out_path = str(tmp_path / "bad_schema.parquet")
    df.write.parquet(out_path)

    with pytest.raises(ValueError, match="Column count mismatch"):
        load_raw_parquet(spark, out_path)