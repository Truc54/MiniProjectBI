{{
    config(
        schema='dw',
        alias='FactRaceResult',
        materialized='incremental',
        incremental_strategy='delete+insert',
        unique_key='source_result_id'
    )
}}

with results as (
    select *
    from {{ ref('stg_results') }} r
    {% if is_incremental() %}
    where r._ingested_at_utc > (
        select coalesce(max(_ingested_at_utc), cast('1900-01-01' as datetime2(3)))
        from {{ this }}
    )
    {% endif %}
),
races as (
    select
        race_id,
        circuit_id,
        date_sk
    from {{ ref('stg_races') }}
),
dim_dates as (
    select date_sk
    from {{ ref('dim_date') }}
),
dim_races as (
    select
        race_sk,
        source_race_id
    from {{ ref('dim_race') }}
),
dim_circuits as (
    select
        circuit_sk,
        source_circuit_id
    from {{ ref('dim_circuit') }}
),
dim_drivers as (
    select
        driver_sk,
        source_driver_id
    from {{ ref('dim_driver') }}
),
dim_constructors as (
    select
        constructor_sk,
        source_constructor_id
    from {{ ref('dim_constructor') }}
),
dim_statuses as (
    select
        status_sk,
        source_status_id
    from {{ ref('dim_status') }}
)

select
    r.source_result_id,
    coalesce(d.date_sk, -1)                                                      as date_sk,
    coalesce(ra.race_sk, -1)                                                    as race_sk,
    coalesce(ci.circuit_sk, -1)                                                 as circuit_sk,
    coalesce(dr.driver_sk, -1)                                                  as driver_sk,
    coalesce(co.constructor_sk, -1)                                             as constructor_sk,
    coalesce(st.status_sk, -1)                                                  as status_sk,
    r.position_text,
    case
        when r.position_text not like '%[^0-9]%' and r.position_text <> '' then 'CLASSIFIED'
        when r.position_text = 'R' then 'RETIRED'
        when r.position_text = 'D' then 'DISQUALIFIED'
        when r.position_text = 'E' then 'EXCLUDED'
        when r.position_text = 'W' then 'WITHDRAWN'
        when r.position_text = 'F' then 'FAILED_TO_QUALIFY'
        when r.position_text = 'N' then 'NOT_CLASSIFIED'
        else 'UNKNOWN'
    end                                                                         as result_outcome_code,
    r.points,
    r.grid_position,
    r.finish_position,
    r.position_order,
    case
        when r.grid_position > 0 and r.finish_position > 0
            then r.grid_position - r.finish_position
        else null
    end                                                                         as places_gained,
    case when r.position_order = 1 then cast(1 as bit) else cast(0 as bit) end  as is_win,
    case when r.finish_position between 1 and 3 then cast(1 as bit) else cast(0 as bit) end as is_podium,
    case when r.finish_position is not null then cast(1 as bit) else cast(0 as bit) end     as is_classified,
    case when r.points > 0 then cast(1 as bit) else cast(0 as bit) end          as is_points_finish,
    case when r.grid_position > 0 then cast(1 as bit) else cast(0 as bit) end   as is_valid_grid_start,
    r._batch_key,
    r._ingested_at_utc
from results r
left join races ra_src
    on r.race_id = ra_src.race_id
left join dim_dates d
    on ra_src.date_sk = d.date_sk
left join dim_races ra
    on r.race_id = ra.source_race_id
left join dim_circuits ci
    on ra_src.circuit_id = ci.source_circuit_id
left join dim_drivers dr
    on r.driver_id = dr.source_driver_id
left join dim_constructors co
    on r.constructor_id = co.source_constructor_id
left join dim_statuses st
    on r.status_id = st.source_status_id
