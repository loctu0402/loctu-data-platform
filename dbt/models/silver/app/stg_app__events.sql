select
    event_id,
    user_id,
    event_name,
    event_ts,
    date(event_ts, '{{ var("report_timezone") }}') as event_date
from {{ source('app', 'events') }}
