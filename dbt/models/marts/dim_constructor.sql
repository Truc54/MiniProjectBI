{{
    config(
        schema='dw',
        alias='DimConstructor',
        materialized='table'
    )
}}

with src as (
    select
        constructor_id                                as constructor_sk,
        constructor_id                                as source_constructor_id,
        constructor_ref                               as constructor_ref,
        constructor_name                              as constructor_name,
        constructor_nationality                       as constructor_nationality,
        wiki_url                                      as wiki_url
    from {{ ref('stg_constructors') }}
)

select
    constructor_sk,
    source_constructor_id,
    constructor_ref,
    constructor_name,
    constructor_nationality,
    wiki_url
from src
union all
select
    -1                                                as constructor_sk,
    -1                                                as source_constructor_id,
    cast(N'unknown' as nvarchar(100))                 as constructor_ref,
    cast(N'Unknown Constructor' as nvarchar(200))     as constructor_name,
    cast(N'Unknown' as nvarchar(100))                 as constructor_nationality,
    null                                              as wiki_url

