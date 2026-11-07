{{
    config(
        schema='dw',
        alias='DimStatus',
        materialized='table'
    )
}}

with src as (
    select
        status_id                                 as status_sk,
        status_id                                 as source_status_id,
        status_label                              as status_label,
        outcome_group                             as outcome_group,
        outcome_category                          as outcome_category
    from {{ ref('stg_status') }}
)

select
    status_sk,
    source_status_id,
    status_label,
    outcome_group,
    outcome_category
from src
union all
select
    -1                                            as status_sk,
    -1                                            as source_status_id,
    cast(N'Unknown' as nvarchar(100))             as status_label,
    cast('OTHER' as varchar(20))                  as outcome_group,
    cast('UNREVIEWED' as varchar(40))             as outcome_category

