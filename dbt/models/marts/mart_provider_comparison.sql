-- used for comparisons and analyse any ternds

with flagged as (

    select * from {{ ref('int_transparency_flagged') }}

),

comparison as (

    select
        firm,
        firm_type,
        corridor,
        sending_country_code,
        receiving_country_code,

        period_year,
        period_quarter,

        cc_number,
        send_amount,

        payment_instrument,
        pickup_method,
        speed_actual,
        access_point,
        receiving_network_coverage,

        is_disclosed_transparent,

        total_cost_pct,
        fee_cost_pct,
        fx_margin_pct,
        decomposed_cost_pct,
        cost_mismatch_flag

    from flagged

)

select * from comparison