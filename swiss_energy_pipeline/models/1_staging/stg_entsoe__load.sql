with source as (
    select * from {{ source('entsoe', 'raw_entsoe_load') }}
),

renamed as (
    select
        timestamp_utc,
        area_code,
        cast(actual_load_mw as numeric) as actual_load_mw,
        cast(forecasted_load_mw as numeric) as forecasted_load_mw,
        -- Calculate forecast variance at staging level
        cast(actual_load_mw - forecasted_load_mw as numeric) as load_forecast_error_mw,
        ingested_at
    from source
)

select * from renamed