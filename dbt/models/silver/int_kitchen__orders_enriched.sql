select
    o.order_id,
    o.kitchen_id,
    o.brand,
    o.platform,
    o.ordered_at,
    o.order_date,
    o.gross_amount,
    o.discount_amount,
    o.net_amount,
    o.is_completed,
    d.courier_type,
    d.rating,
    timestamp_diff(d.picked_up_at, o.ordered_at, second) / 60 as prep_minutes,
    timestamp_diff(d.delivered_at, d.picked_up_at, second) / 60 as ride_minutes,
    timestamp_diff(d.delivered_at, o.ordered_at, second) / 60 as delivery_minutes
from {{ ref('stg_kitchen__orders') }} as o
left join {{ ref('stg_kitchen__deliveries') }} as d on o.order_id = d.order_id
