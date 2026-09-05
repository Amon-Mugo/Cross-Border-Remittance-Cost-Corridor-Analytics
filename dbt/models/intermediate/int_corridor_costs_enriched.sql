--used to enrcih stagging remittance data with referrence data
-- using seed lockup tables without changing table grain or dropping any records
--resoleved Kossovo's issue with the staging model
--preserve the grain of the source data using left joins


with staged as (

    select * from {{ ref('stg_remittance_raw') }}

),

with_country_codes as (
    select
        staged.*,
        case left(corridor, 3)
            when 'KSV' then 'XKX'
            else left(corridor, 3)
        end as sending_country_code,
        case right(corridor, 3)
            when 'KSV' then 'XKX'
            else right(corridor, 3)
        end as receiving_country_code,
        case
            when lcu_code = 'CFA' and left(corridor, 3) in ('CIV', 'SEN', 'BEN', 'BFA', 'GNB', 'MLI', 'NER', 'TGO') then 'XOF'
            when lcu_code = 'CFA' and left(corridor, 3) in ('CMR', 'CAF', 'TCD', 'COG', 'GNQ', 'GAB') then 'XAF'
            else lcu_code
        end as lcu_code_resolved
    from staged
),
enriched as (

    select
        base.* exclude (lcu_code),
        base.lcu_code as lcu_code_raw,

        source_ref.region        as source_region,
        source_ref.income_group  as source_income_group_current,

        dest_ref.region          as destination_region_current,
        dest_ref.income_group    as destination_income_group_current,

        currency_ref.currency_name as sending_currency_name

    from with_country_codes as base

    left join {{ ref('seed_region_income_reference') }} as source_ref
        on base.sending_country_code = source_ref.country_iso3

    left join {{ ref('seed_region_income_reference') }} as dest_ref
        on base.receiving_country_code = dest_ref.country_iso3

    left join {{ ref('seed_currency_reference') }} as currency_ref
        on base.lcu_code_resolved = currency_ref.currency_code

)

select * from enriched