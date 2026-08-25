# this groups the cc1 and cc2 data into a single column
# each with their shared columns
# null values are removed

from pyspark.sql import DataFrame, functions as F

CC_PREFIXES = ("cc1 ", "cc2 ")  # prefixes used in grouping
DRIVING_FIELD = "denomination amount"  # used to filter out null or non-null values


def unpivot_cc(df: DataFrame) -> DataFrame:

    shared_cols = [
        c for c in df.columns if not c.startswith(CC_PREFIXES)
    ]  # this filters
    # out the cc1 and cc2 columns and drop them
    sides = []
    for prefix in CC_PREFIXES:
        cc_number = int(
            prefix.strip()[-1]
        )  # this removes the whitespace and the cc number
        # and 1 and 2 becomes integers thus cc1 and cc2
        prefixed_cols = [c for c in df.columns if c.startswith(prefix)]
        # this groups the cc1 and cc2 with their shared columns which are 7 eg(cc1 lu_amount and cc2 lu_amount,etc)

        select_exprs = [F.col(c) for c in shared_cols]
        # this builds a pyspark list for all shared_columns eg destination,etc

        select_exprs += [F.col(c).alias(c[len(prefix) :]) for c in prefixed_cols]
        # this builds a pyspark list for all the columns with the prefix removed eg cc1_lu_amount, becomes lu_amount etc

        select_exprs.append(F.lit(cc_number).alias("cc_number"))
        # bulds a new column of cc_numbers

        sides_df = df.select(*select_exprs)
        sides_df = sides_df.filter(F.col(DRIVING_FIELD).isNotNull())
        sides_df = sides_df.withColumnRenamed(DRIVING_FIELD, "send_amount")
        sides.append(sides_df)

    return sides[0].unionByName(sides[1])
