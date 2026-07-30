with source as (
    select * from {{ source('entsoe', 'raw_entsoe_cross_border_flow') }}
),

renamed as (
    select
        timestamp_utc,
        out_area_code as export_area_code,
        in_area_code as import_area_code,
        cast(flow_mw as numeric) as flow_mw,
        -- Categorize direction relative to Switzerland (CH)
        case 
            when in_area_code = 'CH' then 'import'
            when out_area_code = 'CH' then 'export'
            else 'internal'
        end as flow_direction,
        ingested_at
    from source
)

select * from renamed