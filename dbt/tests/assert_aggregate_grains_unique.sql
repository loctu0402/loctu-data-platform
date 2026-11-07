select
    'agg_savings_flow_daily' as model_name,
    date_day,
    count(*) as row_count
from {{ ref('agg_savings_flow_daily') }}
group by date_day, txn_type, channel, segment
having count(*) > 1

union all

select
    'agg_kitchen_daily' as model_name,
    date_day,
    count(*) as row_count
from {{ ref('agg_kitchen_daily') }}
group by date_day, kitchen_id, platform
having count(*) > 1
