-- Test that no foreign key in FactRaceResult is orphaned (points to a non-existent dimension SK)
select
    f.source_result_id,
    f.date_sk,
    f.race_sk,
    f.circuit_sk,
    f.driver_sk,
    f.constructor_sk,
    f.status_sk
from {{ ref('fact_race_result') }} f
left join {{ ref('dim_date') }} d on f.date_sk = d.date_sk
left join {{ ref('dim_race') }} r on f.race_sk = r.race_sk
left join {{ ref('dim_circuit') }} c on f.circuit_sk = c.circuit_sk
left join {{ ref('dim_driver') }} dr on f.driver_sk = dr.driver_sk
left join {{ ref('dim_constructor') }} co on f.constructor_sk = co.constructor_sk
left join {{ ref('dim_status') }} s on f.status_sk = s.status_sk
where d.date_sk is null
   or r.race_sk is null
   or c.circuit_sk is null
   or dr.driver_sk is null
   or co.constructor_sk is null
   or s.status_sk is null
