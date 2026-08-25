# check duplicated columns

from pyspark.sql import DataFrame, functions as F
from pyspark.sql.window import Window

DUPLICATE_KEY_COLUMNS = ["corridor", "firm", "period"]


def check_duplicates(
    df: DataFrame, key_cols: list[str] = DUPLICATE_KEY_COLUMNS
) -> tuple[DataFrame, DataFrame]:

    count_window = Window.partitionBy(*key_cols)
    counted = df.withColumn("duplicate_count", F.count("*").over(count_window))
    clean_df = counted.filter(F.col("duplicate_count") == 1).drop("duplicate_count")
    flagged_report = counted.filter(F.col("duplicate_count") > 1)
    return clean_df, flagged_report
