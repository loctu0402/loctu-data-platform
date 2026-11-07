{{ config(
    partition_by={'field': 'date_day', 'data_type': 'date'},
    cluster_by=['kitchen_id', 'platform']
) }}

select
    order_date as date_day,
    if(grouping(kitchen_id) = 1, 'all', kitchen_id) as kitchen_id,
    if(grouping(platform) = 1, 'all', platform) as platform,
    count(*) as orders,
    countif(is_completed) as completed_orders,
    countif(is_on_time) as on_time_orders,
    round(sum(if(is_completed, net_amount, 0)), 2) as net_revenue,
    round(sum(if(is_completed, delivery_minutes, 0)), 1) as delivery_minutes_sum,
    sum(if(is_completed, rating, 0)) as rating_sum,
    countif(is_completed and rating is not null) as rating_count
from {{ ref('fct_orders') }}
group by cube (order_date, kitchen_id, platform)
having grouping(order_date) = 0
