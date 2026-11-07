with d as (
    select
        date_day,
        aum_end - lag(aum_end) over (order by date_day) as aum_change,
        cash_in_amount - cash_out_amount + interest_amount as booked_flow
    from {{ ref('fct_savings_daily') }}
)

select *
from d
where aum_change is not null and abs(aum_change - booked_flow) > 1
