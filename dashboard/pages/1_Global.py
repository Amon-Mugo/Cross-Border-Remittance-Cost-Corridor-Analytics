# dashboard/pages/1_Global.py
#
# Global view: corridor cost trends over time (multi-corridor comparison)
# and a firm-level transparency scorecard, both across all markets in
# the World Bank RPW dataset.

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.country_names import corridor_label
from utils.data import load_corridor_cost_trends, load_transparency_flags
from utils.formatting import fmt_pct

st.set_page_config(page_title="Global | Remittance Corridor Analytics", layout="wide")
st.title("\U0001F30D Global Corridor Cost Trends")

cost_trends = load_corridor_cost_trends()

cost_trends = cost_trends.copy()
cost_trends["period_label"] = (
    cost_trends["period_year"].astype(str) + " Q" + cost_trends["period_quarter"].astype(str)
)
cost_trends["period_sort_key"] = (
    cost_trends["period_year"] * 10 + cost_trends["period_quarter"]
)
cost_trends["corridor_label"] = cost_trends.apply(
    lambda row: corridor_label(row["sending_country_code"], row["receiving_country_code"]),
    axis=1,
)


def weighted_avg(group: pd.DataFrame, value_col: str, weight_col: str) -> float:
    weights = group[weight_col]
    if weights.sum() == 0:
        return group[value_col].mean()
    return (group[value_col] * weights).sum() / weights.sum()


grouped_rows = []
group_cols = ["corridor", "corridor_label", "period_label", "period_sort_key"]
for keys, group in cost_trends.groupby(group_cols):
    corridor, corridor_lbl, period_label, period_sort_key = keys
    grouped_rows.append(
        {
            "corridor": corridor,
            "corridor_label": corridor_lbl,
            "period_label": period_label,
            "period_sort_key": period_sort_key,
            "avg_total_cost_pct": weighted_avg(group, "avg_total_cost_pct", "num_observations"),
            "num_observations": group["num_observations"].sum(),
        }
    )
corridor_trend = pd.DataFrame(grouped_rows).sort_values("period_sort_key")

top_corridors = (
    corridor_trend.groupby("corridor_label")["num_observations"]
    .sum()
    .sort_values(ascending=False)
    .head(5)
    .index.tolist()
)

all_corridors = sorted(corridor_trend["corridor_label"].unique().tolist())
selected_corridors = st.multiselect(
    "Corridors to compare",
    options=all_corridors,
    default=top_corridors,
)

if selected_corridors:
    plot_df = corridor_trend[corridor_trend["corridor_label"].isin(selected_corridors)]
    fig = px.line(
        plot_df,
        x="period_label",
        y="avg_total_cost_pct",
        color="corridor_label",
        markers=True,
        labels={
            "period_label": "Period",
            "avg_total_cost_pct": "Avg. total cost (%)",
            "corridor_label": "Corridor",
        },
        title="Average Remittance Cost by Corridor Over Time",
    )
    fig.update_layout(xaxis_tickangle=-45, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Select at least one corridor to see its cost trend.")

st.divider()
st.subheader("Firm-Level Transparency Scorecard")

transparency_flags = load_transparency_flags()

only_sufficient = st.checkbox(
    "Only show firms with sufficient sample size (30+ observations)",
    value=True,
)

table_df = transparency_flags.copy()
if only_sufficient:
    table_df = table_df[table_df["has_sufficient_sample"]]

table_df = table_df.sort_values("pct_cost_mismatch_flagged", ascending=False)
table_df["pct_disclosed_transparent"] = table_df["pct_disclosed_transparent"].apply(fmt_pct)
table_df["pct_cost_mismatch_flagged"] = table_df["pct_cost_mismatch_flagged"].apply(fmt_pct)

st.dataframe(
    table_df[
        [
            "firm",
            "firm_type",
            "num_observations",
            "num_corridors",
            "pct_disclosed_transparent",
            "pct_cost_mismatch_flagged",
            "avg_transparency_flag_count",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)
