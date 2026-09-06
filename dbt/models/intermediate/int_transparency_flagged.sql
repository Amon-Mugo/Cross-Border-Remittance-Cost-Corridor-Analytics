-- this is used to flag null values
-- check null values from any cost metrics we have defined so far
with decomposed as (
    select * from {{ ref('int_provider_cost_decomposed') }}
),

flagged as (
    select
       decomposed.*,
       case
            when lower(trim(transparent)) = 'yes' then true
            when lower(trim(transparent)) = 'no' then false
            else null
        end as is_disclosed_transparent,

        total_cost_pct is null as total_cost_pct_missing,
        (fee_cost_pct is null or fx_margin_pct is null) as cost_components_missing,

        case 
           when decomposed_cost_pct is null or total_cost_pct is null then null
           else abs(decomposed_cost_pct - total_cost_pct) > 0.01
        end as cost_mismatch_flag
    from decomposed
),

with_flag_count as (
    SELECT
       flagged.*,
       (case when total_cost_pct_missing then 1 else 0 end)
       + (case when cost_components_missing then 1 else 0 end)
       + (case when cost_mismatch_flag then 1 else 0 end )  as transparency_flag_count
    from flagged
)

select * from with_flag_count