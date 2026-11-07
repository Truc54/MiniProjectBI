{{
    config(
        schema='dw',
        alias='DimDate',
        materialized='table'
    )
}}

with digits as (
    select 0 as n union all select 1 union all select 2 union all select 3 union all select 4
    union all select 5 union all select 6 union all select 7 union all select 8 union all select 9
),
numbers as (
    select top (datediff(day, '1950-01-01', '2026-12-31') + 1)
        row_number() over (order by (select null)) - 1 as n
    from digits d1
    cross join digits d2
    cross join digits d3
    cross join digits d4
    cross join digits d5
),
dates as (
    select dateadd(day, n, cast('1950-01-01' as date)) as full_date
    from numbers
),
race_dates as (
    select distinct race_date
    from {{ ref('stg_races') }}
    where race_date is not null
),
final_dates as (
    select
        cast(convert(char(8), d.full_date, 112) as int)                 as date_sk,
        d.full_date                                                     as full_date,
        cast(datepart(day, d.full_date) as int)                         as day_of_month,
        cast(datepart(month, d.full_date) as int)                       as month_number,
        case datepart(month, d.full_date)
            when 1 then 'January'
            when 2 then 'February'
            when 3 then 'March'
            when 4 then 'April'
            when 5 then 'May'
            when 6 then 'June'
            when 7 then 'July'
            when 8 then 'August'
            when 9 then 'September'
            when 10 then 'October'
            when 11 then 'November'
            when 12 then 'December'
        end                                                             as month_name,
        case datepart(month, d.full_date)
            when 1 then 'Jan'
            when 2 then 'Feb'
            when 3 then 'Mar'
            when 4 then 'Apr'
            when 5 then 'May'
            when 6 then 'Jun'
            when 7 then 'Jul'
            when 8 then 'Aug'
            when 9 then 'Sep'
            when 10 then 'Oct'
            when 11 then 'Nov'
            when 12 then 'Dec'
        end                                                             as month_short,
        cast(datepart(quarter, d.full_date) as int)                     as quarter_number,
        concat('Q', datepart(quarter, d.full_date))                     as quarter_label,
        cast(datepart(year, d.full_date) as int)                        as year_number,
        convert(char(7), d.full_date, 120)                              as year_month,
        cast((datediff(day, '19000101', d.full_date) % 7) + 1 as int)   as day_of_week_number,
        case (datediff(day, '19000101', d.full_date) % 7) + 1
            when 1 then 'Monday'
            when 2 then 'Tuesday'
            when 3 then 'Wednesday'
            when 4 then 'Thursday'
            when 5 then 'Friday'
            when 6 then 'Saturday'
            when 7 then 'Sunday'
        end                                                             as day_name,
        case when ((datediff(day, '19000101', d.full_date) % 7) + 1) in (6, 7)
            then cast(1 as bit) else cast(0 as bit) end                 as is_weekend,
        case when rd.race_date is not null
            then cast(1 as bit) else cast(0 as bit) end                 as is_race_day
    from dates d
    left join race_dates rd on d.full_date = rd.race_date
)

select * from final_dates
union all
select
    -1              as date_sk,
    null            as full_date,
    null            as day_of_month,
    null            as month_number,
    'Unknown'       as month_name,
    'Unknown'       as month_short,
    null            as quarter_number,
    'Unknown'       as quarter_label,
    null            as year_number,
    'Unknown'       as year_month,
    null            as day_of_week_number,
    'Unknown'       as day_name,
    null            as is_weekend,
    cast(0 as bit)  as is_race_day

