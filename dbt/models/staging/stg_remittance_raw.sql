-- used for cleaness and standardise raw remittance data before it lands for
-- downstream processing
-- remittance_corridor is the schema name of the dbt source
--remittance_raw is the table name of the dbt source

with source as (

    select * from {{ source('remittance_corridor', 'remittance_raw') }}

),

renamed as (

    select
        cast(id as number(38,0))                          as raw_id,
        trim(corridor)                                     as corridor,
        trim(firm)                                          as firm,
        trim(firm_type)                                     as firm_type,
        trim("payment instrument")                          as payment_instrument,
        trim("pickup method")                               as pickup_method,
        trim("access point")                                as access_point,
        trim("speed actual")                                as speed_actual,
        trim("receiving network coverage")                  as receiving_network_coverage,
        trim(transparent)                                   as transparent,

        trim(source_code)                                   as source_code,
        trim(source_name)                                   as source_country_name,
        trim(source_income)                                 as source_income_group,
        trim("source_G8G20")                                as source_g8g20,

        trim(destination_code)                              as destination_code,
        trim(destination_name)                              as destination_country_name,
        trim(destination_region)                            as destination_region,
        trim(destination_income)                             as destination_income_group,
        trim(destination_lending)                            as destination_lending_category,

        cast(date as date)                                as transaction_date,
        trim(date_raw)                                       as date_raw,
        trim(period)                                         as period_label,
        cast(period_year as number(4,0))                    as period_year,
        cast(period_quarter as number(1,0))                 as period_quarter,

        cast(cc_number as number(38,0))                      as cc_number,
        trim("lcu code")                                     as lcu_code,

        cast(send_amount as number(18,6))                   as send_amount,
        cast("lcu amount" as number(18,6))                  as lcu_amount,
        cast("lcu fee" as number(18,6))                     as lcu_fee,
        cast("lcu fx rate" as number(18,6))                 as lcu_fx_rate,
        cast("inter lcu bank fx" as number(18,6))           as inter_lcu_bank_fx,
        cast("fx margin" as number(18,6))                   as fx_margin,
        cast("total cost %" as number(18,6))                as total_cost_pct,

        trim("Standard Note")                               as standard_note

    from source

)

select * from renamed