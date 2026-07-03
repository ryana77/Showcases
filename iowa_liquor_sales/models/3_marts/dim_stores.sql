with sales as (
    select * from {{ ref('stg_iowa_liquor__sales') }}
),

uniqued as (
    select
        store_id,
        min(sales_date) as first_active_date,
        max(sales_date) as most_recent_active_date,
        count(distinct sales_id) as total_lifetime_transactions
    from sales
    group by 1
)

select * from uniqued