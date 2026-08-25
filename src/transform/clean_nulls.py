# to check any null values in the data
# and replace is with null
from pyspark.sql import DataFrame
import pyspark.sql.functions as F

NULL_MARKER = ".."
GEOGRAPHY_NULL_COLUMNS = [
    "source_region",
    "source_lending",
    "source_G8G20",
    "destination_region",
    "destination_lending",
    "destination_G8G20",
]


def clean_geography_nulls(df: DataFrame) -> DataFrame:
    missing = [c for c in GEOGRAPHY_NULL_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Expected geography columns not found in DataFrame: {missing}"
        )

    result = df
    for column in GEOGRAPHY_NULL_COLUMNS:
        result = result.withColumn(
            column,
            F.when(F.col(column) == NULL_MARKER, None).otherwise(F.col(column)),
        )
    return result
