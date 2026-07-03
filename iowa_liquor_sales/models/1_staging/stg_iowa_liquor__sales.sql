with source as (
    select * from {{ source('bigquery_public_data', 'sales') }}
    -- Limits the scan range during development
    where date >= '2026-01-01'
),

renamed as (

    select
        invoice_and_item_number as sales_id,
        date as sales_date,
        store_number as store_id,
        store_name,
        address as store_address,
        city as store_city,
        zip_code as store_zip_code,
        store_location as store_location_geocoded,
        county_number as store_county_number,
        county as store_county,
        category as product_category_code,
        category_name as product_category,
        vendor_number,
        vendor_name,
        item_number as product_id,
        item_description as product_description,
        pack as bottles_per_case,
        bottle_volume_ml,
        state_bottle_cost,
        state_bottle_retail,
        bottles_sold as state_bottles_sold,
        -- Wholesale revenue for the State / Wholesale cost for the store
        sale_dollars as state_wholesale_revenue,
        -- Calculate state profit
        (state_bottle_retail - state_bottle_cost) * bottles_sold as state_profit_dollars,
        volume_sold_liters,
        volume_sold_gallons         

    from source

)

select * from renamed