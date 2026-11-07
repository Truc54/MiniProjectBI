{{
    config(
        schema='stg_clean',
        materialized='view'
    )
}}

with src as (
    select
        resultId                                    as source_result_id,
        raceId                                      as race_id,
        driverId                                    as driver_id,
        constructorId                               as constructor_id,
        statusId                                    as status_id,
        number                                      as car_number,
        grid                                        as grid_position,
        position                                    as finish_position,
        nullif(ltrim(rtrim(positionText)), N'')       as position_text,
        positionOrder                               as position_order,
        cast(points as decimal(6, 2))               as points,
        laps                                        as laps_completed,
        nullif(ltrim(rtrim([time])), N'')           as finish_time_text,
        milliseconds                                as finish_time_ms,
        fastestLap                                  as fastest_lap_number,
        rank                                        as fastest_lap_rank,
        nullif(ltrim(rtrim(fastestLapTime)), N'')   as fastest_lap_time_text,
        cast(fastestLapSpeed as decimal(7, 3))      as fastest_lap_speed_kph,
        _source_file,
        _batch_key,
        _load_mode,
        _ingested_at_utc
    from {{ source('stg', 'results') }}
)

select
    source_result_id,
    race_id,
    driver_id,
    constructor_id,
    status_id,
    car_number,
    grid_position,
    finish_position,
    position_text,
    position_order,
    points,
    laps_completed,
    finish_time_text,
    finish_time_ms,
    fastest_lap_number,
    fastest_lap_rank,
    fastest_lap_time_text,
    fastest_lap_speed_kph,
    _source_file,
    _batch_key,
    _load_mode,
    _ingested_at_utc
from src

