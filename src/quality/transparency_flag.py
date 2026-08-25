# this filters out no and yes and null values
# flagged_report has no
# clean_df has  yes and no

from pyspark.sql import DataFrame, functions as F

TRANSPARENT_COLUMN = "transparent"  # column name
NON_TRANSPARENT_VALUE = "no"


def check_transparency(
    df: DataFrame, transparent_col: str = TRANSPARENT_COLUMN
) -> tuple[DataFrame, DataFrame]:

    normalized = F.lower(F.trim(F.col(transparent_col)))
    # this removes any white space and makes it lowercase values

    is_non_transparent = normalized == NON_TRANSPARENT_VALUE
    # this checks if the value is no

    flagged_report = df.filter(is_non_transparent)
    # this filters out yes and has now has no rows

    clean_df = df.filter(~is_non_transparent | F.col(transparent_col).isNull())
    # this filters out no and has now has yes and null rows

    return clean_df, flagged_report
