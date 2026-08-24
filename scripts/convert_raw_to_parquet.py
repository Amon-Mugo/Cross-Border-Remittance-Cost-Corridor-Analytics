# used to load xlsx files into parquet

from pathlib import Path
import sys  # read command line arguments and exit codes
import pandas as pd

SHEET_NAME = "Dataset (from Q2 2016)"


def convert_xlsx_to_parquet(input_path: str, output_path: str) -> None:
    # read xlsx file
    src = Path(input_path)
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {input_path}")

    df = pd.read_excel(src, sheet_name=SHEET_NAME, engine="openpyxl")
    expected_rows = 197_999

    if len(df) != expected_rows:
        raise ValueError(
            f"Row count mismatch: expected {expected_rows}, got {len(df)}. "
            "Source sheet may have changed — verify before proceeding."
        )
    df["date"] = df["date"].astype(str)

    df.to_parquet(output_path, engine="pyarrow", index=False)
    print(f"Wrote {len(df)} rows, {len(df.columns)} columns to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: convert_xlsx_to_parquet.py <input_path> <output_path>")
        sys.exit(1)

    convert_xlsx_to_parquet(sys.argv[1], sys.argv[2])