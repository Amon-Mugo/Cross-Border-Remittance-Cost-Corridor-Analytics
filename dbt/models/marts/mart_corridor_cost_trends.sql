-- used for analytics of the cost of remittance 

with flagged as (

    select * from {{ ref('int_transparency_flagged') }}

),

aggregated as (

    select 
        corridor,
        sending_country_code,
        receiving_country_code,
        source_region,
        destination_region_current,

        period_year,
        period_quarter,

        cc_number,
        send_amount,
        is_disclosed_transparent,

        count(*)                       as num_observations,
        count(distinct firm)           as num_providers,

        avg(total_cost_pct)            as avg_total_cost_pct,
        median(total_cost_pct)         as median_total_cost_pct,
        min(total_cost_pct)            as min_total_cost_pct,
        max(total_cost_pct)            as max_total_cost_pct,
        avg(fee_cost_pct)              as avg_fee_cost_pct,
        avg(fx_margin_pct)             as avg_fx_margin_pct,
        avg(decomposed_cost_pct)       as avg_decomposed_cost_pct,
        count_if(cost_mismatch_flag)   as num_cost_mismatch_flagged

    from flagged

    group by
        corridor,
        sending_country_code,
        receiving_country_code,
        source_region,
        destination_region_current,
        period_year,
        period_quarter,
        cc_number,
        send_amount,
        is_disclosed_transparent

)

select * from aggregated