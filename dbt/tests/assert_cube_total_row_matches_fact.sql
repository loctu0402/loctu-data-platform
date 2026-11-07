with cube_total as (
    select
        date_day,
        amount,
        accounts
    from {{ ref('agg_savings_flow_daily') }}
    where txn_type = 'cash_in' and channel = 'all' and segment = 'all'
)

select
    f.date_day,
    f.cash_in_amount,
    c.amount,
    f.depositing_accounts,
    c.accounts
from {{ ref('fct_savings_daily') }} as f
left join cube_total as c on f.date_day = c.date_day
where
    f.cash_in_amount > 0
    and (c.amount is null or abs(f.cash_in_amount - c.amount) > 1 or f.depositing_accounts != c.accounts)
