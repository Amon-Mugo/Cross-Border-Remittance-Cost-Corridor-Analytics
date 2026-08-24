#purpose is to load the parquet data into a spark dataframe
#this where the purpose of emr services is to run

import logging
from pyspark.sql import SparkSession, DataFrame

logger= logging.getLogger(__name__)

EXPECTED_COLUMN_COUNT = 42
EXPECTED_ROW_COUNT = 197_999

def load_raw_parquet(spark: SparkSession, path: str) -> DataFrame:
    df=spark.read.parquet(path)
    actual_columns = len(df.columns)
    if actual_columns != EXPECTED_COLUMN_COUNT:
        raise ValueError(
            f"Column count mismatch: expected {EXPECTED_COLUMN_COUNT}, "
            f"got {actual_columns}. Source schema may have changed."
        )

    actual_rows=df.count()
    if actual_rows != EXPECTED_ROW_COUNT:
        logger.warning (
            "Row count is %s, baseline was %s. Expected if a new "
            "quarter's data has been published — not treated as an error.",
            actual_rows,
            EXPECTED_ROW_COUNT
        )
    return df

