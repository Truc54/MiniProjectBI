{{
    config(
        schema='dw',
        alias='DimRace',
        materialized='table'
    )
}}

with src as (
    select
        race_id                                                           as race_sk,
        race_id                                                           as source_race_id,
        season_year                                                       as season_year,
        round_number                                                      as round_number,
        race_name                                                         as race_name,
        concat(
            season_year,
            N' R',
            right('0' + cast(round_number as varchar(2)), 2),
            N' ',
            race_name
        )                                                                 as race_label,
        race_date                                                         as race_date,
        cast(has_sprint as bit)                                           as has_sprint,
        wiki_url                                                          as wiki_url
    from {{ ref('stg_races') }}
)

select
    race_sk,
    source_race_id,
    season_year,
    round_number,
    race_name,
    race_label,
    race_date,
    has_sprint,
    wiki_url
from src
union all
select
    -1                              as race_sk,
    -1                              as source_race_id,
    null                            as season_year,
    null                            as round_number,
    cast(N'Unknown Race' as nvarchar(200)) as race_name,
    cast(N'Unknown Race' as nvarchar(220)) as race_label,
    null                            as race_date,
    null                            as has_sprint,
    null                            as wiki_url

