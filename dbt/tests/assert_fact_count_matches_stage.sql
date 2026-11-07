with stage_count as (
    select count(*) as cnt from {{ ref('stg_results') }}
),
fact_count as (
    select count(*) as cnt from {{ ref('fact_race_result') }}
)
select
    s.cnt as stage_cnt,
    f.cnt as fact_cnt
from stage_count s
cross join fact_count f
where s.cnt != f.cnt

