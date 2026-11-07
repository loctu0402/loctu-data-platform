select
    kitchen_id,
    city_zone,
    opened_on
from {{ source('kitchen', 'kitchens') }}
