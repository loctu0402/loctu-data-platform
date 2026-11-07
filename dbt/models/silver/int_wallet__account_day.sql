{{ config(
    materialized='table',
    partition_by={'field': 'date_day', 'data_type': 'date'},
    cluster_by=['account_id']
) }}

with flows as (
    select
        account_id,
        txn_date as date_day,
        sum(if(txn_type = 'cash_in', amount, 0)) as cash_in_amount,
        sum(if(txn_type = 'cash_out', amount, 0)) as cash_out_amount,
        sum(if(txn_type = 'interest', amount, 0)) as interest_amount
    from {{ ref('stg_wallet__transactions') }}
    where is_success
    group by account_id, txn_date
),

grid as (
    select
        a.account_id,
        c.date_day
    from {{ ref('stg_wallet__accounts') }} as a
    inner join {{ ref('util_calendar') }} as c on a.opened_date <= c.date_day
),

balances as (
    select
        g.account_id,
        g.date_day,
        coalesce(f.cash_in_amount, 0) as cash_in_amount,
        coalesce(f.cash_out_amount, 0) as cash_out_amount,
        coalesce(f.interest_amount, 0) as interest_amount,
        sum(coalesce(f.cash_in_amount, 0) - coalesce(f.cash_out_amount, 0) + coalesce(f.interest_amount, 0))
            over (partition by g.account_id order by g.date_day rows between unbounded preceding and current row) as end_balance
    from grid as g
    left join flows as f on g.account_id = f.account_id and g.date_day = f.date_day
),

flagged as (
    select
        *,
        end_balance >= 1 as is_funded,
        coalesce(lag(end_balance >= 1) over by_account, false) as was_funded_yesterday,
        coalesce(max(if(end_balance >= 1, 1, 0))
            over (partition by account_id order by date_day rows between unbounded preceding and 1 preceding), 0) = 1 as was_ever_funded
    from balances
    window by_account as (partition by account_id order by date_day)
)

select
    account_id,
    date_day,
    cash_in_amount,
    cash_out_amount,
    interest_amount,
    round(end_balance, 2) as end_balance,
    is_funded,
    case
        when is_funded and not was_funded_yesterday and not was_ever_funded then 'new'
        when is_funded and not was_funded_yesterday then 'reactivated'
        when not is_funded and was_funded_yesterday then 'churned'
        when is_funded then 'retained'
        else 'inactive'
    end as lifecycle_state
from flagged
