select
    account_id,
    user_id,
    opened_at,
    date(opened_at, '{{ var("report_timezone") }}') as opened_date,
    acquisition_channel,
    segment
from {{ source('wallet', 'accounts') }}
