{{ config(
    materialized='table'
) }}

with stg_sales as (
    -- Reference staging model
    select * from {{ ref('stg_iowa_liquor__sales') }}
),

product_details as (
    select distinct
        product_id,
        product_category_code,
        product_description,
        product_category,
        bottles_per_case,
        bottle_volume_ml
    from stg_sales
    qualify row_number() over (
        partition by product_id
        order by order_date desc, sales_id desc
    ) = 1
)

select * from product_details
