with sales as (
    select * from {{ ref('stg_iowa_liquor__sales') }}
)

select
    sales_id,
    sales_date,
    store_id,
    product_id,
    bottles_sold,
    revenue_usd,
    volume_sold_liters
from sales