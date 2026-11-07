{{
    config(
        schema='stg_clean',
        materialized='view'
    )
}}

with src as (
    select
        constructorId                             as constructor_id,
        nullif(ltrim(rtrim(constructorRef)), N'') as constructor_ref,
        nullif(ltrim(rtrim(name)), N'')           as constructor_name,
        nullif(ltrim(rtrim(nationality)), N'')    as constructor_nationality,
        nullif(ltrim(rtrim(url)), N'')            as wiki_url,
        _source_file,
        _batch_key,
        _load_mode,
        _ingested_at_utc
    from {{ source('stg', 'constructors') }}
)

select
    constructor_id,
    constructor_ref,
    constructor_name,
    constructor_nationality,
    wiki_url,
    _source_file,
    _batch_key,
    _load_mode,
    _ingested_at_utc
from src

