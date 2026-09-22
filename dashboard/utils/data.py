# dashboard/utils/data.py
#
# Shared read-only access to the exported marts DuckDB file. Cached so
# each page/session reuses one connection and each dataframe is loaded
# from disk only once, keeping the dashboard fast and self-contained.

from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).parent.parent / "data" / "marts.duckdb"


@st.cache_resource
def get_connection() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DB_PATH), read_only=True)


@st.cache_data
def load_corridor_cost_trends() -> pd.DataFrame:
    return get_connection().execute("SELECT * FROM mart_corridor_cost_trends").df()


@st.cache_data
def load_provider_comparison() -> pd.DataFrame:
    return get_connection().execute("SELECT * FROM mart_provider_comparison").df()


@st.cache_data
def load_transparency_flags() -> pd.DataFrame:
    return get_connection().execute("SELECT * FROM mart_transparency_flags").df()


@st.cache_data
def load_kenya_corridors() -> pd.DataFrame:
    return get_connection().execute("SELECT * FROM mart_kenya_corridors").df()
