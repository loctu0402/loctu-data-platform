select
    order_id,
    courier_type,
    picked_up_at,
    delivered_at,
    cast(distance_km as float64) as distance_km,
    cast(rating as int64) as rating
from {{ source('kitchen', 'deliveries') }}
