with source as (
    select * from {{ source('entsoe', 'raw_entsoe_generation') }}
),

renamed as (
    select
        timestamp_utc,
        area_code,
        lower(replace(production_type, ' ', '_')) as production_type_code,
        production_type as production_type_label,
        cast(actual_generation_mw as numeric) as actual_generation_mw,
        ingested_at
    from source
)

select * from renamed