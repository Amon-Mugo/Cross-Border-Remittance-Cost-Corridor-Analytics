#the orchestration of the etl pipeline and for the quality and transform

import argparse # used for cli commands
import logging
from pyspark.sql import DataFrame,SparkSession

from src.quality.duplicate_check import check_duplicates
from src.quality.fx_margin_check import check_fx_margin
from src.quality.transparency_flag import check_transparency
from src.transform.clean_nulls import clean_geography_nulls
from src.transform.load_raw import load_raw_parquet
from src.transform.parse_dates import parse_date_column, parse_period_column
from src.transform.unpivot_cc import unpivot_cc
from src.transform.validate_grain import validate_grain

logger=logging.getLogger(__name__)
RAW_BUCKET="remittance-corridor-raw-data-bucket-011294328070"
CURATED_BUCKET="remittance-corridor-curated-data-bucket-011294328070"
DEFAULT_RAW_PATH= (f"s3://{RAW_BUCKET}/raw/full_history/rpw_q2_2016_2025.parquet")
DEFAULT_OUTPUT_PATH= f"s3://{CURATED_BUCKET}"

def run_pipeline(spark: SparkSession, raw_path: str) -> tuple[DataFrame, dict[str, DataFrame]]:

    df=load_raw_parquet(spark,raw_path) #used to load data from parquet 

    #load important data from the raw data
    df=clean_geography_nulls(df)
    df=parse_date_column(df)
    df=parse_period_column(df)
    df=unpivot_cc(df)

    #check for quality issues
    df, grain_duplicates_report=validate_grain(df) #gain_duplicates will hold duplicate records

    df, fx_margin_report=check_fx_margin(df) #fx_margin report will hold negative fx margins

    df, transparency_report=check_transparency(df) #transparency report will no 

    df, duplicate_check_report=check_duplicates(df) #duplicate check report will hold duplicate records

    reports ={
        "grain_duplicates":grain_duplicates_report,
        "fx_margin":fx_margin_report,
        "transparency":transparency_report,
        "duplicate_check":duplicate_check_report
        }
    for name,report_df in reports.items():
        flagged_count=report_df.count()
        if flagged_count:#if there are flagged records
            logger.warning("%s ,%d row(s) flagged",name,flagged_count)

    return df,reports

# write_ouputs
def write_outputs(clean_df:DataFrame,reports:dict[str,DataFrame],output_path:str)->None:
    #clean_df is the clean data
    #reports is the quality reports
    #output_path uses emr.tf and iam.tf policies to write to s3

    clean_out=f"{output_path.rstrip('/')}/clean" #this strips the trailing slash
    logger.info("writing clean output to %s",clean_out)
    clean_df.write.mode("overwrite").parquet(clean_out) 

    for name,report_df in reports.items():
        report_out=f"{output_path.rstrip('/')}/quality_reports/{name}"
        logger.info("writing %s report to %s",name,report_out)
        report_df.write.mode("overwrite").parquet(report_out)


#cli commands for the pipeline and raw and output paths
def parse_args()->argparse.Namespace:
    parser=argparse.ArgumentParser(
    description="Run the Cross-Border Remittance Cost & Corridor "
    "Analytics transform + quality pipeline."
    )

    #registering the raw s3
    parser.add_argument(
        "--raw-path",
        default=DEFAULT_RAW_PATH,
        help="S3 path to the raw Parquet input(raw_bucket).",
    )
    #registering the output s3
    parser.add_argument(
        "--output-path",
        default=DEFAULT_OUTPUT_PATH,
        help="S3 path to the curated bucket to write clean output and "
        "quality reports under.",

    )

    return parser.parse_args()

#orchestrating the pipeline
def main()->None:
    logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    )
    #cli args
    args=parse_args() #cli to be displayed in the terminal

    #init spark session
    spark=(
        SparkSession.builder.appName(
            "cross-border-remittance-corridor-pipeline"
        ).getOrCreate()
    )

    #run the pipeline
    try:
        clean_df, reports = run_pipeline(spark, args.raw_path) #based on our first function run_pipeline
        write_outputs(clean_df,reports,args.output_path)
    finally:
        spark.stop()

if __name__=="__main__":
    main()