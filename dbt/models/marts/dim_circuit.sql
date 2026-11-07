{{
    config(
        schema='dw',
        alias='DimCircuit',
        materialized='table'
    )
}}

with src as (
    select
        circuit_id                                as circuit_sk,
        circuit_id                                as source_circuit_id,
        circuit_ref                               as circuit_ref,
        circuit_name                              as circuit_name,
        locality                                  as locality,
        country                                   as country,
        latitude                                  as latitude,
        longitude                                 as longitude,
        altitude_m                                as altitude_m,
        wiki_url                                  as wiki_url
    from {{ ref('stg_circuits') }}
)

select
    circuit_sk,
    source_circuit_id,
    circuit_ref,
    circuit_name,
    locality,
    country,
    latitude,
    longitude,
    altitude_m,
    wiki_url
from src
union all
select
    -1                                            as circuit_sk,
    -1                                            as source_circuit_id,
    cast(N'unknown' as nvarchar(100))             as circuit_ref,
    cast(N'Unknown Circuit' as nvarchar(200))     as circuit_name,
    cast(N'Unknown' as nvarchar(100))             as locality,
    cast(N'Unknown' as nvarchar(100))             as country,
    null                                          as latitude,
    null                                          as longitude,
    null                                          as altitude_m,
    null                                          as wiki_url

