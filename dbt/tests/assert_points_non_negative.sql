select
    source_result_id,
    points
from {{ ref('fact_race_result') }}
where points < 0

