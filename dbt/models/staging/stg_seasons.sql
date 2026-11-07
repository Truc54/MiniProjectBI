{{
    config(
        schema='stg_clean',
        materialized='view'
    )
}}

with src as (
    select
        year                                  as season_year,
        nullif(ltrim(rtrim(url)), N'')        as season_wiki_url,
        _source_file,
        _batch_key,
        _load_mode,
        _ingested_at_utc
    from {{ source('stg', 'seasons') }}
)

select
    season_year,
    season_wiki_url,
    _source_file,
    _batch_key,
    _load_mode,
    _ingested_at_utc
from src

