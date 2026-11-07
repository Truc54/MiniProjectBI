{{
    config(
        schema='stg_clean',
        materialized='view'
    )
}}

with src as (
    select
        circuitId                             as circuit_id,
        nullif(ltrim(rtrim(circuitRef)), N'') as circuit_ref,
        nullif(ltrim(rtrim(name)), N'')       as circuit_name,
        nullif(ltrim(rtrim(location)), N'')   as locality,
        nullif(ltrim(rtrim(country)), N'')    as country,
        cast(lat as decimal(9, 6))            as latitude,
        cast(lng as decimal(9, 6))            as longitude,
        alt                                   as altitude_m,
        nullif(ltrim(rtrim(url)), N'')        as wiki_url,
        _source_file,
        _batch_key,
        _load_mode,
        _ingested_at_utc
    from {{ source('stg', 'circuits') }}
)

select
    circuit_id,
    circuit_ref,
    circuit_name,
    locality,
    country,
    latitude,
    longitude,
    altitude_m,
    wiki_url,
    _source_file,
    _batch_key,
    _load_mode,
    _ingested_at_utc
from src

