# dashboard/app.py
#
# Entry point for the Cross-Border Remittance dashboard. Sets shared
# page config and gives a landing overview before users drill into the
# Global or Kenya pages in the sidebar.

import streamlit as st

from utils.data import (
    load_corridor_cost_trends,
    load_kenya_corridors,
    load_provider_comparison,
    load_transparency_flags,
)
from utils.formatting import fmt_count

st.set_page_config(
    page_title="Cross-Border Remittance Cost & Corridor Analytics",
    page_icon="\U0001F310",
    layout="wide",
)

st.title("\U0001F310 Cross-Border Remittance Cost & Corridor Analytics")
st.caption(
    "World Bank Remittance Prices Worldwide (RPW) dataset, 2016 Q2 \u2013 2025 Q1"
)

st.markdown(
    """
Use the sidebar to explore:

- **Global** \u2014 corridor cost trends and firm-level transparency across all markets
- **Kenya** \u2014 a spotlight on Kenya's sending and receiving remittance corridors
"""
)

cost_trends = load_corridor_cost_trends()
provider_comparison = load_provider_comparison()
transparency_flags = load_transparency_flags()
kenya_corridors = load_kenya_corridors()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Corridors tracked", fmt_count(cost_trends["corridor"].nunique()))
col2.metric("Provider observations", fmt_count(len(provider_comparison)))
col3.metric("Firms scored", fmt_count(len(transparency_flags)))
col4.metric("Kenya observations", fmt_count(len(kenya_corridors)))

st.divider()
st.caption(
    "Data: World Bank Remittance Prices Worldwide. "
    "Exported from dbt marts to a local DuckDB file \u2014 "
    "see `dashboard/export_marts.py` to refresh."
)
