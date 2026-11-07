select
    txn_id,
    account_id,
    txn_type,
    channel,
    cast(amount as numeric) as amount,
    if(txn_type = 'cash_out', -1, 1) * cast(amount as numeric) as signed_amount,
    status = 'success' as is_success,
    created_at,
    date(created_at, '{{ var("report_timezone") }}') as txn_date
from {{ source('wallet', 'transactions') }}
