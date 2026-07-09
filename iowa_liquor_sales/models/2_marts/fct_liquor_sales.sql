{{ config(
    materialized='table',
    partition_by={
      "field": "order_date",
      "data_type": "date",
      "granularity": "month"
    }
) }}

with stg_sales as (
    -- Reference staging model
    select * from {{ ref('stg_iowa_liquor__sales') }}
)

select
    -- Primary & Foreign Keys
    sales_id,
    order_date,
    store_id,
    product_id,
    vendor_id,
   
    -- Quantitative Metrics
    wholesale_bottles_sold,
    volume_sold_liters,
    
    -- Financial Metrics
    wholesale_bottle_cost,
    wholesale_bottle_retail,
    
    -- Wholesale revenue (State revenue / Store cost)
    wholesale_revenue_dollars, 
    
    -- Exact State Profit Calculation
    wholesale_profit_dollars,
    
    -- Mocked Consumer Retail Revenue (Assuming a standard 20% retail store markup)
    (wholesale_revenue_dollars * 1.20) as estimated_retail_revenue_dollars

from stg_sales
where order_date is not null
  and wholesale_revenue_dollars > 0
