{{ config(partition_by={'field': 'date_day', 'data_type': 'date'}) }}

with daily as (
    select
        date_day,
        sum(end_balance) as aum_end,
        sum(cash_in_amount) as cash_in_amount,
        sum(cash_out_amount) as cash_out_amount,
        sum(interest_amount) as interest_amount,
        countif(is_funded) as funded_accounts,
        countif(lifecycle_state = 'new') as new_funded_accounts,
        countif(lifecycle_state = 'reactivated') as reactivated_accounts,
        countif(lifecycle_state = 'churned') as churned_accounts,
        countif(cash_in_amount > 0) as depositing_accounts,
        countif(cash_out_amount > 0) as withdrawing_accounts
    from {{ ref('int_wallet__account_day') }}
    group by date_day
)

select
    d.date_day,
    round(d.aum_end, 2) as aum_end,
    round(d.cash_in_amount, 2) as cash_in_amount,
    round(d.cash_out_amount, 2) as cash_out_amount,
    round(d.interest_amount, 2) as interest_amount,
    round(d.cash_in_amount - d.cash_out_amount, 2) as net_flow_amount,
    d.funded_accounts,
    d.new_funded_accounts,
    d.reactivated_accounts,
    d.churned_accounts,
    d.depositing_accounts,
    d.withdrawing_accounts,
    r.annual_rate
from daily as d
left join {{ ref('stg_wallet__daily_rates') }} as r on d.date_day = r.rate_date
