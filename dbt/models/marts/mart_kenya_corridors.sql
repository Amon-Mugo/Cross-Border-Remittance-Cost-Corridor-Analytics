-- this will be used specifically for anaytics of kenya only

with flagged as (
    select * from {{ ref('int_transparency_flagged') }}
),

kenya_corridors as (
    SELECT
       firm,
       firm_type,
       corridor,
       sending_country_code,
       receiving_country_code,

       case
           when sending_country_code = 'KEN' then 'sending'
           when receiving_country_code = 'KEN' then 'receiving'
        end as kenya_role,

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
    where sending_country_code = 'KEN' or receiving_country_code='KEN'
)

SELECT * FROM kenya_corridors