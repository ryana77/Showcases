{{ config(materialized='table') }}

with dates as (

    select date_day

    from unnest(
        generate_date_array(
            date('2020-01-01'),
            current_date(),
            interval 1 day
        )
    ) as date_day

)

select

    date_day as date_id,

    extract(year from date_day) as year,

    extract(quarter from date_day) as quarter,

    extract(month from date_day) as month,

    format_date('%B', date_day) as month_name,

    format_date('%b', date_day) as month_short,

    extract(isoweek from date_day) as week,

    extract(day from date_day) as day,

    extract(dayofweek from date_day) as day_of_week,

    format_date('%A', date_day) as day_name,

    extract(dayofweek from date_day) in (1,7) as is_weekend,

    format_date('%Y-%m', date_day) as year_month,

    concat(
        cast(extract(year from date_day) as string),
        '-Q',
        cast(extract(quarter from date_day) as string)
    ) as year_quarter

from dates