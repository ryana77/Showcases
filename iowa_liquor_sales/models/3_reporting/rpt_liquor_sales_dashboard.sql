{{ config(
    materialized = 'table'
) }}

with sales as (

    select *
    from {{ ref('fct_liquor_sales') }}

),

stores as (

    select *
    from {{ ref('dim_store') }}

),

products as (

    select *
    from {{ ref('dim_product') }}

),

dates as (

    select *
    from {{ ref('dim_date') }}

)

select

    -- Sales
    sales.sales_id,
    sales.order_date,

    -- Date
    dates.year,
    dates.quarter,
    dates.month,
    dates.month_name,
    dates.month_short,
    dates.week,
    dates.day,
    dates.day_name,
    dates.year_month,
    dates.year_quarter,
    dates.is_weekend,

    -- Store
    sales.store_id,
    stores.store_name,
    stores.store_city,
    stores.store_county,
    stores.store_status,
    stores.store_location_geocoded,

    -- Product
    sales.product_id,
    products.product_description,
    products.product_category,
    products.bottles_per_case,
    products.bottle_volume_ml,

    -- Measures
    sales.wholesale_bottles_sold,
    sales.volume_sold_liters,
    sales.wholesale_bottle_cost,
    sales.wholesale_bottle_retail,
    sales.wholesale_revenue_dollars,
    sales.wholesale_profit_dollars,
    sales.estimated_retail_revenue_dollars

from sales

left join stores
    on sales.store_id = stores.store_id

left join products
    on sales.product_id = products.product_id

left join dates
    on sales.order_date = dates.date_id