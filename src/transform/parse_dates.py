# enable dates to have a proper timestamp format
# and also decompose 2016_2Q is split into 2016 and 2Q
from pyspark.sql import DataFrame
import pyspark.sql.functions as F

DATE_FORMAT_SHORT = "dd/MMM/yyyy"
DATE_FORMAT_LONG = "yyyy-MM-dd HH:mm:ss"


def parse_date_column(df: DataFrame) -> DataFrame:
    if "date" not in df.columns:
        raise ValueError("Expected 'date' column not found in DataFrame")
    return df.withColumn("date_raw", F.col("date")).withColumn(
        "date",
        F.coalesce(
            F.to_date(F.try_to_timestamp(F.col("date_raw"), F.lit(DATE_FORMAT_SHORT))),
            F.to_date(F.try_to_timestamp(F.col("date_raw"), F.lit(DATE_FORMAT_LONG))),
        ),
    )


def parse_period_column(df: DataFrame) -> DataFrame:
    if "period" not in df.columns:
        raise ValueError("Expected 'period' column not found in DataFrame")
    return df.withColumn(
        "period_year", F.split(F.col("period"), "_").getItem(0).cast("int")
    ).withColumn(
        "period_quarter",
        F.regexp_extract(F.col("period"), r"_(\d)Q", 1).cast("int"),
    )
