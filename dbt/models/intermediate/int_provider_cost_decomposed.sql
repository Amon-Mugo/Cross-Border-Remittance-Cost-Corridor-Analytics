with enriched as (
    select * from {{ ref('int_corridor_costs_enriched') }}
),
with_cost_components as (
    select
        enriched.* exclude (fx_margin),
        fx_margin as fx_margin_pct,
        lcu_fee / nullif(lcu_amount,0) * 100 as fee_cost_pct
    from enriched
),

decomposed as(
    select
        with_cost_components.*,
        fee_cost_pct + fx_margin_pct as decomposed_cost_pct
    from with_cost_components
)

select * from decomposed