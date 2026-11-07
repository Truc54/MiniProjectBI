{{
    config(
        schema='stg_clean',
        materialized='view'
    )
}}

with src as (
    select
        statusId                              as status_id,
        nullif(ltrim(rtrim(status)), N'')     as status_label,
        _source_file,
        _batch_key,
        _load_mode,
        _ingested_at_utc
    from {{ source('stg', 'status') }}
),
classified as (
    select
        status_id,
        status_label,
        case
            when status_label in (N'Finished', N'Lapped')
              or status_label like N'+[0-9]% Lap' or status_label like N'+[0-9]% Laps'
                then 'FINISHED_OR_LAPPED'
            when status_label in (N'Did not start', N'Withdrew')
                then 'DID_NOT_START'
            when status_label in (N'Disqualified', N'Excluded', N'Underweight')
                then 'DISQUALIFIED'
            when status_label in (N'107% Rule', N'Did not prequalify', N'Did not qualify', N'Not classified',
                                  N'Not restarted')
                then 'NOT_QUALIFIED_OR_NOT_CLASSIFIED'
            when status_label in (N'Alternator', N'Axle', N'Battery', N'Brake duct', N'Brakes', N'CV joint',
                                  N'Chassis', N'Clutch', N'Cooling system', N'Crankshaft', N'Differential',
                                  N'Distributor', N'Driver Seat', N'Driveshaft', N'Drivetrain', N'ERS',
                                  N'Electrical', N'Electronics', N'Engine', N'Engine fire', N'Engine misfire',
                                  N'Exhaust', N'Fire', N'Fuel', N'Fuel leak', N'Fuel pipe', N'Fuel pressure',
                                  N'Fuel pump', N'Fuel system', N'Gearbox', N'Halfshaft', N'Handling',
                                  N'Heat shield fire', N'Hydraulics', N'Ignition', N'Injection',
                                  N'Launch control', N'Magneto', N'Mechanical', N'Oil leak', N'Oil line',
                                  N'Oil pipe', N'Oil pressure', N'Oil pump', N'Overheating', N'Pneumatics',
                                  N'Power Unit', N'Power loss', N'Puncture', N'Radiator', N'Rear wing',
                                  N'Safety belt', N'Seat', N'Spark plugs', N'Stalled', N'Steering',
                                  N'Supercharger', N'Suspension', N'Technical', N'Throttle', N'Track rod',
                                  N'Transmission', N'Turbo', N'Tyre', N'Tyre puncture', N'Undertray',
                                  N'Vibrations', N'Water leak', N'Water pipe', N'Water pressure', N'Water pump',
                                  N'Wheel', N'Wheel bearing', N'Wheel nut', N'Wheel rim')
                then 'MECHANICAL'
            when status_label in (N'Accident', N'Broken wing', N'Collision', N'Collision damage', N'Damage',
                                  N'Debris', N'Fatal accident', N'Front wing', N'Spun off')
                then 'ACCIDENT_DAMAGE'
            when status_label in (N'Driver unwell', N'Eye injury', N'Illness', N'Injured', N'Injury',
                                  N'Physical')
                then 'DRIVER_MEDICAL'
            when status_label in (N'Fuel rig', N'Out of fuel', N'Refuelling', N'Retired', N'Safety',
                                  N'Safety concerns')
                then 'OTHER_RETIREMENT'
            else 'UNREVIEWED'
        end as outcome_category,
        _source_file,
        _batch_key,
        _load_mode,
        _ingested_at_utc
    from src
)
select
    status_id,
    status_label,
    case outcome_category
        when 'FINISHED_OR_LAPPED'              then 'CLASSIFIED'
        when 'DID_NOT_START'                   then 'DNS'
        when 'DISQUALIFIED'                    then 'DSQ'
        when 'NOT_QUALIFIED_OR_NOT_CLASSIFIED' then 'OTHER'
        when 'UNREVIEWED'                      then 'OTHER'
        else 'RETIREMENT_DNF'
    end as outcome_group,
    outcome_category,
    _source_file,
    _batch_key,
    _load_mode,
    _ingested_at_utc
from classified

