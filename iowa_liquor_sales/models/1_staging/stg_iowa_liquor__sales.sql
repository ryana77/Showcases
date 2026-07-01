with source as (
    select * from {{ source('bigquery_public_data', 'sales') }}
    -- Limits the scan range during development
    where date >= '2026-01-01'
),

renamed as (
    select
        invoice_and_item_number as sales_id,
        cast(date as date) as sales_date,
        cast(store_number as string) as store_id,
        cast(item_number as string) as product_id,
        category_name as product_category,
        vendor_name,
        cast(bottles_sold as int64) as bottles_sold,
        cast(sale_dollars as float64) as revenue_usd,
        cast(volume_sold_liters as float64) as volume_sold_liters
    from source
)

select * from renamed