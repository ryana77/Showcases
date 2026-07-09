{{ config(materialized='table') }}

with stg_sales as (
    select * from {{ ref('stg_iowa_liquor__sales') }}
),

metrics as (
    select
        -- Pipeline Freshness
        max(order_date) as max_data_date,
        current_date() as execution_date,
        date_diff(current_date(), max(order_date), day) as days_since_last_update,
        
        -- Data Volume
        count(*) as total_rows_processed,
        
        -- Data Quality Flags (Anomalies caught)
        countif(wholesale_revenue_dollars <= 0) as count_zero_or_negative_sales,
        countif(product_category is null) as count_missing_categories,
        countif(store_id is null) as count_missing_stores

    from stg_sales
)

select
    *
from metrics
