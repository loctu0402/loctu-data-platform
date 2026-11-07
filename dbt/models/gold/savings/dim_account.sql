with latest as (
    select
        account_id,
        end_balance,
        lifecycle_state
    from {{ ref('int_wallet__account_day') }}
    where true
    qualify row_number() over (partition by account_id order by date_day desc) = 1
),

first_funded as (
    select
        account_id,
        min(date_day) as first_funded_date
    from {{ ref('int_wallet__account_day') }}
    where is_funded
    group by account_id
)

select
    a.account_id,
    a.user_id,
    a.opened_date,
    a.acquisition_channel,
    a.segment,
    f.first_funded_date,
    l.end_balance as current_balance,
    l.lifecycle_state as current_state
from {{ ref('stg_wallet__accounts') }} as a
left join first_funded as f on a.account_id = f.account_id
left join latest as l on a.account_id = l.account_id
