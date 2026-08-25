# validates the columns
# duplicated columns are not dropped rather counted

from pyspark.sql import DataFrame, functions as F
from pyspark.sql.window import Window

GRAIN_COLUMNS = ["corridor", "firm", "payment instrument", "period", "send_amount"]
_ROW_ID_COL = "_row_id"
_ROW_NUMBER_COL = "_grain_row_number"


def validate_grain(
    df: DataFrame, grain_cols: list[str] = GRAIN_COLUMNS
) -> tuple[DataFrame, DataFrame]:
    # one dataframe is fro clean data and the other is for duplicates

    indexed = df.withColumn(_ROW_ID_COL, F.monotonically_increasing_id())
    # create a new column named _row_id and each have unique ids

    grain_window = Window.partitionBy(*grain_cols).orderBy(_ROW_ID_COL)
    # creates a group of grain_cols data and orders by _row_id

    ranked = indexed.withColumn(_ROW_NUMBER_COL, F.row_number().over(grain_window))
    # creates a new column named _grain_row_number and assigns a unique number to each row
    # enables us to identify duplicates

    count_window = Window.partitionBy(*grain_cols)
    # this creates a group of grain_cols data only

    ranked = ranked.withColumn("duplicate_count", F.count("*").over(count_window))
    # creates a new column named duplicate_count and counts the number of rows in the group

    clean_df = ranked.filter(F.col(_ROW_NUMBER_COL) == 1).drop(
        _ROW_ID_COL, _ROW_NUMBER_COL, "duplicate_count"
    )
    # filters out the rows with duplicate_count>1 and drops the _row_id and _grain_row_number columns

    duplicates_report = ranked.filter(F.col(_ROW_NUMBER_COL) > 1).drop(
        _ROW_ID_COL, _ROW_NUMBER_COL
    )
    # filters out non duplicates but keeps duplicate_count column

    return clean_df, duplicates_report
