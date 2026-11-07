select
    order_id,
    kitchen_id,
    brand,
    platform,
    ordered_at,
    date(ordered_at, '{{ var("report_timezone") }}') as order_date,
    cast(subtotal as numeric) as gross_amount,
    cast(discount as numeric) as discount_amount,
    cast(subtotal as numeric) - cast(discount as numeric) as net_amount,
    status = 'completed' as is_completed
from {{ source('kitchen', 'orders') }}
