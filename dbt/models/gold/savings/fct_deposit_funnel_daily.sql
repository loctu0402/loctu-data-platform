select
    event_date as date_day,
    count(distinct if(event_name = 'open_savings_tab', user_id, null)) as users_opened,
    count(distinct if(event_name = 'start_deposit', user_id, null)) as users_started_deposit,
    count(distinct if(event_name = 'deposit_success', user_id, null)) as users_deposited
from {{ ref('stg_app__events') }}
group by event_date
