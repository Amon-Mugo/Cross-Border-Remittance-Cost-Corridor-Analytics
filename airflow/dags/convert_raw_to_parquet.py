"""


Incrementally converts the cumulative World Bank RPW xlsx drop into a
single new-quarter parquet slice, uploads it to S3 raw/<quarter_label>/data.parquet,
skipping quarters already present in S3 raw/. Returns the detected
quarter_label for downstream XCom use (EMR job argument, Snowflake load call).
"""

import sys
import tempfile
from pathlib import Path

import boto3
import pandas as pd

SHEET_NAME = "Dataset (from Q2 2016)"
PERIOD_COLUMN = "period"
RAW_PREFIX = "raw/"


def list_existing_quarters(bucket: str, prefix: str) -> set[str]:
    """Return quarter_label values already present as raw/<quarter_label>/ prefixes in S3."""
    s3 = boto3.client("s3")
    paginator = s3.get_paginator("list_objects_v2")
    quarters = set()
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter="/"):
        for common_prefix in page.get("CommonPrefixes", []):
            quarter_label = common_prefix["Prefix"].removeprefix(prefix).rstrip("/")
            if quarter_label:
                quarters.add(quarter_label)
    return quarters


def find_new_quarter(df: pd.DataFrame, existing_quarters: set[str]) -> str:
    """Return the latest quarter_label present in df but not yet in S3."""
    file_quarters = set(df[PERIOD_COLUMN].unique())
    new_quarters = sorted(file_quarters - existing_quarters)

    if not new_quarters:
        raise ValueError(
            "No new quarters found in source file — all periods already loaded to S3."
        )

    # "YYYY_#Q" sorts correctly as a string (single-digit quarter, fixed-width year)
    return new_quarters[-1]


def convert_xlsx_to_parquet(input_path: str, raw_bucket: str) -> str:
    """Convert the newest un-loaded quarter in the cumulative xlsx drop to
    parquet and upload it to s3://<raw_bucket>/raw/<quarter_label>/data.parquet.

    Returns the detected quarter_label.
    """
    src = Path(input_path)
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {input_path}")

    df = pd.read_excel(src, sheet_name=SHEET_NAME, engine="openpyxl")

    existing_quarters = list_existing_quarters(raw_bucket, RAW_PREFIX)
    quarter_label = find_new_quarter(df, existing_quarters)

    quarter_df = df[df[PERIOD_COLUMN] == quarter_label].copy()
    quarter_df["date"] = quarter_df["date"].astype(str)

    s3_key = f"{RAW_PREFIX}{quarter_label}/data.parquet"

    with tempfile.NamedTemporaryFile(suffix=".parquet") as tmp_file:
        quarter_df.to_parquet(tmp_file.name, engine="pyarrow", index=False)
        boto3.client("s3").upload_file(tmp_file.name, raw_bucket, s3_key)

    print(
        f"Wrote {len(quarter_df)} rows for quarter {quarter_label} "
        f"to s3://{raw_bucket}/{s3_key}"
    )

    return quarter_label


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: convert_raw_to_parquet.py <input_path> <raw_bucket>")
        sys.exit(1)

    result = convert_xlsx_to_parquet(sys.argv[1], sys.argv[2])
    print(result)