{{
    config(
        schema='stg_clean',
        materialized='view'
    )
}}

with src as (
    select
        raceId                                                as race_id,
        year                                                  as season_year,
        round                                                 as round_number,
        circuitId                                             as circuit_id,
        nullif(ltrim(rtrim(name)), N'')                       as race_name,
        [date]                                                as race_date,
        cast(convert(char(8), [date], 112) as int)            as date_sk,
        [time]                                                as race_start_time_utc,
        nullif(ltrim(rtrim(url)), N'')                        as wiki_url,
        fp1_date,
        fp1_time                                              as fp1_time_utc,
        fp2_date,
        fp2_time                                              as fp2_time_utc,
        fp3_date,
        fp3_time                                              as fp3_time_utc,
        quali_date,
        quali_time                                            as quali_time_utc,
        sprint_date,
        sprint_time                                           as sprint_time_utc,
        case when sprint_date is not null then 1 else 0 end   as has_sprint,
        _source_file,
        _batch_key,
        _load_mode,
        _ingested_at_utc
    from {{ source('stg', 'races') }}
)

select
    race_id,
    season_year,
    round_number,
    circuit_id,
    race_name,
    race_date,
    date_sk,
    race_start_time_utc,
    wiki_url,
    fp1_date,
    fp1_time_utc,
    fp2_date,
    fp2_time_utc,
    fp3_date,
    fp3_time_utc,
    quali_date,
    quali_time_utc,
    sprint_date,
    sprint_time_utc,
    has_sprint,
    _source_file,
    _batch_key,
    _load_mode,
    _ingested_at_utc
from src

