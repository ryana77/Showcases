{{ config(
    materialized='table',
    cluster_by=["store_tier", "store_county"]
) }}

with stg_sales as (
    -- Reference staging model
    select * from {{ ref('stg_iowa_liquor__sales') }}
),

store_metrics as (
    select
        store_id,
        -- Remove NULL values in store information
        any_value(store_name) as store_name,
        any_value(store_county) as store_county,
        any_value(store_city) as store_city,
        -- Safely extracts the geocoded location without breaking the GROUP BY
        any_value(store_location_geocoded) as store_location_geocoded,
        count(distinct sales_id) as total_orders,
        sum(wholesale_revenue_dollars) as total_wholesale_revenue,
        max(order_date) as last_order_date
    from stg_sales
    group by store_id
),

store_tiering as (
    select
        *,
        -- Algorithmic Store Tiering based on purchase volume
        case 
            when total_wholesale_revenue >= 100000 then 'Gold'
            when total_wholesale_revenue >= 25000 then 'Silver'
            else 'Bronze'
        end as store_tier,
        
        -- Store Status
        case 
            when last_order_date >= date_sub(current_date(), interval 180 day) then 'Active'
            else 'Churned/Inactive'
        end as store_status

    from store_metrics
)

select * from store_tiering