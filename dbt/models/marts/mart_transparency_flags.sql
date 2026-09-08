-- this is used in groupig the firms only for anlytics purposes

with flagged as (
    
    select * from {{ ref('int_transparency_flagged') }}
),

scorecard as (
    select
       firm,
       firm_type,

       count(*)                                      as num_observations,
       count(distinct corridor)                       as num_corridors,
       count(distinct period_year,period_quarter)     as num_periods,

       avg(case when is_disclosed_transparent then 100.0 else 0 end)   as pct_disclosed_transparent,
       avg(case when total_cost_pct_missing  then 100.0 else 0 end)        as pct_total_cost_pct_missing,
       avg(case when cost_components_missing then 100.0 else 0 end)    as pct_cost_components_missing,

       count_if(cost_mismatch_flag)     as num_cost_mismatch_flagged,
       count_if(cost_mismatch_flag is not null )   as num_cost_mismatch_evaluable,
       (count_if(cost_mismatch_flag)/ nullif(count_if(cost_mismatch_flag is not null),0)) * 100  as pct_cost_mismatch_flagged,
       avg(transparency_flag_count) as avg_transparency_flag_count,
       count(*) >= 30                                   as has_sufficient_sample

    
    from flagged
    group by 
        firm,
        firm_type
)

select * from scorecard
