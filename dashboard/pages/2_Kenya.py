# dashboard/pages/2_Kenya.py
#
# Kenya spotlight: sending vs receiving corridor breakdown, cost trends
# over time, and a firm comparison specific to Kenya's remittance market.

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.country_names import corridor_label
from utils.data import load_kenya_corridors
from utils.formatting import fmt_count, fmt_pct

st.set_page_config(page_title="Kenya | Remittance Corridor Analytics", layout="wide")
st.title("\U0001F1F0\U0001F1EA Kenya Corridor Spotlight")

kenya = load_kenya_corridors()
kenya = kenya.copy()
kenya["corridor_label"] = kenya.apply(
    lambda row: corridor_label(row["sending_country_code"], row["receiving_country_code"]),
    axis=1,
)

role_filter = st.radio(
    "Kenya's role",
    options=["Both", "Receiving", "Sending"],
    horizontal=True,
)

if role_filter != "Both":
    filtered = kenya[kenya["kenya_role"] == role_filter.lower()]
else:
    filtered = kenya

col1, col2, col3, col4 = st.columns(4)
col1.metric("Observations", fmt_count(len(filtered)))
col2.metric("Corridors", filtered["corridor"].nunique())
col3.metric("Firms", filtered["firm"].nunique())
col4.metric(
    "Avg. total cost (%)",
    fmt_pct(filtered["total_cost_pct"].mean()) if len(filtered) else "\u2013",
)

st.divider()
st.subheader("Cost Trend Over Time")

trend = filtered.copy()
trend["period_label"] = trend["period_year"].astype(str) + " Q" + trend["period_quarter"].astype(str)
trend["period_sort_key"] = trend["period_year"] * 10 + trend["period_quarter"]

trend_agg = (
    trend.groupby(["corridor_label", "period_label", "period_sort_key"])["total_cost_pct"]
    .mean()
    .reset_index()
    .sort_values("period_sort_key")
)

corridor_counts = trend.groupby("corridor_label").size().sort_values(ascending=False)
default_corridors = corridor_counts.head(5).index.tolist()
all_corridors = sorted(trend["corridor_label"].unique().tolist())

selected_corridors = st.multiselect(
    "Corridors to compare",
    options=all_corridors,
    default=default_corridors,
)

if selected_corridors:
    plot_df = trend_agg[trend_agg["corridor_label"].isin(selected_corridors)]
    fig = px.line(
        plot_df,
        x="period_label",
        y="total_cost_pct",
        color="corridor_label",
        markers=True,
        labels={
            "period_label": "Period",
            "total_cost_pct": "Avg. total cost (%)",
            "corridor_label": "Corridor",
        },
        title="Kenya Corridor Cost Over Time",
    )
    fig.update_layout(xaxis_tickangle=-45, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Select at least one corridor to see its cost trend.")

st.divider()
st.subheader("Firm Comparison")

firm_agg = (
    filtered.groupby(["firm", "firm_type"])
    .agg(
        num_observations=("total_cost_pct", "count"),
        avg_total_cost_pct=("total_cost_pct", "mean"),
        pct_disclosed_transparent=("is_disclosed_transparent", "mean"),
    )
    .reset_index()
)
firm_agg["pct_disclosed_transparent"] = firm_agg["pct_disclosed_transparent"] * 100

min_obs = st.slider("Minimum observations per firm", min_value=1, max_value=50, value=10)
firm_agg_filtered = firm_agg[firm_agg["num_observations"] >= min_obs].sort_values(
    "avg_total_cost_pct", ascending=True
)

high_cost_firms = firm_agg_filtered[firm_agg_filtered["avg_total_cost_pct"] >= 20]
if not high_cost_firms.empty:
    names_with_n = ", ".join(
        f"{row.firm} (n={row.num_observations})" for row in high_cost_firms.itertuples()
    )
    st.caption(
        f"\u26a0\ufe0f Notably high-cost firms above: {names_with_n}. "
        "Sample sizes shown in parentheses \u2014 costs are bank-published rates, "
        "not necessarily reflective of the cheapest available channel."
    )

fig_bar = px.bar(
    firm_agg_filtered,
    x="avg_total_cost_pct",
    y="firm",
    orientation="h",
    color="firm_type",
    labels={"avg_total_cost_pct": "Avg. total cost (%)", "firm": "Firm"},
    title="Average Cost by Firm (Kenya Corridors)",
)
fig_bar.update_layout(yaxis={"categoryorder": "total ascending"})
st.plotly_chart(fig_bar, use_container_width=True)

display_df = firm_agg_filtered.copy()
display_df["avg_total_cost_pct"] = display_df["avg_total_cost_pct"].apply(fmt_pct)
display_df["pct_disclosed_transparent"] = display_df["pct_disclosed_transparent"].apply(fmt_pct)
st.dataframe(display_df, use_container_width=True, hide_index=True)
