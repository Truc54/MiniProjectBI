{{
    config(
        schema='dw',
        alias='DimDriver',
        materialized='table'
    )
}}

with src as (
    select
        driver_id                                 as driver_sk,
        driver_id                                 as source_driver_id,
        driver_ref                                as driver_ref,
        full_name                                 as full_name,
        forename                                  as forename,
        surname                                   as surname,
        driver_code                               as driver_code,
        permanent_number                          as permanent_number,
        driver_nationality                        as driver_nationality,
        date_of_birth                             as date_of_birth,
        wiki_url                                  as wiki_url
    from {{ ref('stg_drivers') }}
)

select
    driver_sk,
    source_driver_id,
    driver_ref,
    full_name,
    forename,
    surname,
    driver_code,
    permanent_number,
    driver_nationality,
    date_of_birth,
    wiki_url
from src
union all
select
    -1                                            as driver_sk,
    -1                                            as source_driver_id,
    cast(N'unknown' as nvarchar(100))             as driver_ref,
    cast(N'Unknown Driver' as nvarchar(201))      as full_name,
    cast(N'Unknown' as nvarchar(100))             as forename,
    cast(N'Driver' as nvarchar(100))              as surname,
    null                                          as driver_code,
    null                                          as permanent_number,
    cast(N'Unknown' as nvarchar(100))             as driver_nationality,
    null                                          as date_of_birth,
    null                                          as wiki_url

