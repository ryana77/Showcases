{{ config(
    materialized='table'
) }}

with stg_sales as (
    -- Reference staging model
    select * from {{ ref('stg_iowa_liquor__sales') }}
),

vendor_details as (select distinct
    vendor_id,
    vendor_name
  from stg_sales
  qualify row_number() over (
        partition by vendor_id
        order by order_date desc, sales_id desc
    ) = 1
)

select * from vendor_details