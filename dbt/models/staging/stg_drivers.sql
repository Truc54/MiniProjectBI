{{
    config(
        schema='stg_clean',
        materialized='view'
    )
}}

with src as (
    select
        driverId                                                    as driver_id,
        nullif(ltrim(rtrim(driverRef)), N'')                        as driver_ref,
        number                                                      as permanent_number,
        nullif(ltrim(rtrim(code)), N'')                             as driver_code,
        nullif(ltrim(rtrim(forename)), N'')                         as forename,
        nullif(ltrim(rtrim(surname)), N'')                          as surname,
        concat(ltrim(rtrim(forename)), N' ', ltrim(rtrim(surname)))  as full_name,
        dob                                                         as date_of_birth,
        nullif(ltrim(rtrim(nationality)), N'')                      as driver_nationality,
        nullif(ltrim(rtrim(url)), N'')                              as wiki_url,
        _source_file,
        _batch_key,
        _load_mode,
        _ingested_at_utc
    from {{ source('stg', 'drivers') }}
)

select
    driver_id,
    driver_ref,
    permanent_number,
    driver_code,
    forename,
    surname,
    full_name,
    date_of_birth,
    driver_nationality,
    wiki_url,
    _source_file,
    _batch_key,
    _load_mode,
    _ingested_at_utc
from src

