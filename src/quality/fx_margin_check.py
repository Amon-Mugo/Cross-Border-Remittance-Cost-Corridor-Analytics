# check if there is null values and negative values in fx margin
# if negative there is a new column added to the data

from pyspark.sql import DataFrame, functions as F

MARGIN_COLUMN = "fx margin"


def check_fx_margin(
    df: DataFrame, margin_col: str = MARGIN_COLUMN
) -> tuple[DataFrame, DataFrame]:

    is_negative = F.col(margin_col) < 0
    # checks if the fx margin is negative
    tagged_report = df.filter(is_negative)  # new column added to the data

    clean_df = df.filter(
        ~is_negative | F.col(margin_col).isNull()
    )  # clean the data and check if there is null values
    # clean the data and check if there is null values

    return clean_df, tagged_report
