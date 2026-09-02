# the orchestration of the etl pipeline and for the quality and transform

import argparse  # used for cli commands
import logging
from pyspark.sql import DataFrame, SparkSession

from src.quality.duplicate_check import check_duplicates
from src.quality.fx_margin_check import check_fx_margin
from src.quality.transparency_flag import check_transparency
from src.transform.clean_nulls import clean_geography_nulls
from src.transform.load_raw import load_raw_parquet
from src.transform.parse_dates import parse_date_column, parse_period_column
from src.transform.unpivot_cc import unpivot_cc
from src.transform.validate_grain import validate_grain

logger = logging.getLogger(__name__)
RAW_BUCKET = "remittance-corridor-raw-data-bucket-<redacted>"
CURATED_BUCKET = "remittance-corridor-curated-data-bucket-<redacted>"
DEFAULT_RAW_PATH = f"s3://{RAW_BUCKET}/raw/full_history/rpw_q2_2016_2025.parquet"
DEFAULT_OUTPUT_PATH = f"s3://{CURATED_BUCKET}"


def run_pipeline(
    spark: SparkSession, raw_path: str
) -> tuple[DataFrame, dict[str, DataFrame]]:

    df = load_raw_parquet(spark, raw_path)  # used to load data from parquet

    # load important data from the raw data
    df = clean_geography_nulls(df)
    df = parse_date_column(df)
    df = parse_period_column(df)
    df = unpivot_cc(df)

    # validate_grain is the only hard filter: it removes true
    # full-grain duplicate rows, which are structurally invalid data.
    df, grain_duplicates_report = validate_grain(df)

    # fx_margin, transparency, and duplicate_check are quality flags,
    # not filters. Each runs against the same grain-deduped df and
    # only its flagged-rows report is kept -- clean_df is not narrowed
    # further, so a bad fx margin or an untransparent pricing
    # disclosure stays visible in the curated output and its own
    # quality report, instead of being silently dropped.
    _, fx_margin_report = check_fx_margin(df)
    _, transparency_report = check_transparency(df)
    _, duplicate_check_report = check_duplicates(df)

    reports = {
        "grain_duplicates": grain_duplicates_report,
        "fx_margin": fx_margin_report,
        "transparency": transparency_report,
        "duplicate_check": duplicate_check_report,
    }
    for name, report_df in reports.items():
        flagged_count = report_df.count()
        if flagged_count:  # if there are flagged records
            logger.warning("%s ,%d row(s) flagged", name, flagged_count)

    return df, reports


# write_ouputs
def write_outputs(
    clean_df: DataFrame, reports: dict[str, DataFrame], output_path: str
) -> None:
    # clean_df is the clean data, written per-quarter so Snowflake's
    # LOAD_REMITTANCE_RAW can target one quarter's subfolder at a time
    # reports is the quality reports
    # output_path uses emr.tf and iam.tf policies to write to s3

    base = output_path.rstrip("/")
    periods = [row["period"] for row in clean_df.select("period").distinct().collect()]

    for period in periods:
        period_out = f"{base}/{period}/clean"
        logger.info("writing clean output for %s to %s", period, period_out)
        clean_df.filter(clean_df["period"] == period).write.mode("overwrite").parquet(
            period_out
        )

    for name, report_df in reports.items():
        report_out = f"{base}/quality_reports/{name}"
        logger.info("writing %s report to %s", name, report_out)
        report_df.write.mode("overwrite").parquet(report_out)


# cli commands for the pipeline and raw and output paths
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Cross-Border Remittance Cost & Corridor "
        "Analytics transform + quality pipeline."
    )

    # registering the raw s3
    parser.add_argument(
        "--raw-path",
        default=DEFAULT_RAW_PATH,
        help="S3 path to the raw Parquet input(raw_bucket).",
    )
    # registering the output s3
    parser.add_argument(
        "--output-path",
        default=DEFAULT_OUTPUT_PATH,
        help="S3 path to the curated bucket to write clean output and "
        "quality reports under.",
    )

    return parser.parse_args()


# orchestrating the pipeline
def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    # cli args
    args = parse_args()  # cli to be displayed in the terminal

    # init spark session
    spark = SparkSession.builder.appName(
        "cross-border-remittance-corridor-pipeline"
    ).getOrCreate()

    # run the pipeline
    try:
        clean_df, reports = run_pipeline(
            spark, args.raw_path
        )  # based on our first function run_pipeline
        write_outputs(clean_df, reports, args.output_path)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
