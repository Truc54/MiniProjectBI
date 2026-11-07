select
    source_result_id,
    grid_position,
    finish_position,
    places_gained
from {{ ref('fact_race_result') }}
where places_gained is not null
  and (grid_position <= 0 or finish_position is null or places_gained != (grid_position - finish_position))

