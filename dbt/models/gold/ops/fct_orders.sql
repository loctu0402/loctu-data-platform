{{ config(
    materialized='incremental',
    incremental_strategy='merge',
    unique_key='order_id',
    partition_by={'field': 'order_date', 'data_type': 'date'},
    cluster_by=['kitchen_id', 'platform'],
    on_schema_change='append_new_columns'
) }}

select
    order_id,
    kitchen_id,
    brand,
    platform,
    ordered_at,
    order_date,
    net_amount,
    is_completed,
    courier_type,
    rating,
    round(prep_minutes, 1) as prep_minutes,
    round(delivery_minutes, 1) as delivery_minutes,
    is_completed and delivery_minutes <= {{ var('on_time_minutes') }} as is_on_time
from {{ ref('int_kitchen__orders_enriched') }}
{% if is_incremental() %}
    where order_date >= (select date_sub(max(t.order_date), interval 3 day) from {{ this }} as t)
{% endif %}
