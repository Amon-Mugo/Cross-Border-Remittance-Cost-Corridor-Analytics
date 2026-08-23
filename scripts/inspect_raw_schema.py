
import pandas as pd

SHEET_NAME = "Dataset (from Q2 2016)"
FILE_PATH = "rpw_dataset_2011_2025_q1.xlsx"


def main():
    df = pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME, engine="openpyxl")

    print("=== SHAPE ===")
    print(df.shape)

    print("\n=== COLUMNS ===")
    for col in df.columns:
        print(repr(col))

    print("\n=== DTYPES ===")
    print(df.dtypes)

    print("\n=== SAMPLE ROWS ===")
    print(df.head(5).to_string())

    print("\n=== '..' NULL MARKER CHECK (per column) ===")
    dotdot_counts = (df.astype(str) == "..").sum()
    print(dotdot_counts[dotdot_counts > 0])

    print("\n=== 'date' COLUMN SAMPLE (raw values, unparsed) ===")
    if "date" in df.columns:
        print(df["date"].head(10).to_string())
        print("dtype:", df["date"].dtype)

    print("\n=== 'period' COLUMN UNIQUE VALUES (sample) ===")
    if "period" in df.columns:
        print(sorted(df["period"].dropna().unique())[:10])

    print("\n=== cc1_ / cc2_ COLUMN NAMES ===")
    cc_cols = [c for c in df.columns if str(c).lower().startswith(("cc1_", "cc2_"))]
    print(cc_cols)

    print("\n=== 'transparent' VALUE COUNTS ===")
    if "transparent" in df.columns:
        print(df["transparent"].value_counts(dropna=False))


if __name__ == "__main__":
    main()