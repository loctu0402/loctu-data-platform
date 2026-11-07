select date_day
from unnest(generate_date_array(
    (select min(txn_date) from {{ ref('stg_wallet__transactions') }}),
    date_sub(current_date('{{ var("report_timezone") }}'), interval 1 day)
)) as date_day
