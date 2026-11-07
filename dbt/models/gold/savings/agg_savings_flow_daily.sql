{{ config(
    partition_by={'field': 'date_day', 'data_type': 'date'},
    cluster_by=['txn_type', 'channel', 'segment']
) }}

select
    t.txn_date as date_day,
    t.txn_type,
    if(grouping(t.channel) = 1, 'all', t.channel) as channel,
    if(grouping(a.segment) = 1, 'all', a.segment) as segment,
    round(sum(t.amount), 2) as amount,
    count(*) as txn_count,
    count(distinct t.account_id) as accounts
from {{ ref('stg_wallet__transactions') }} as t
inner join {{ ref('stg_wallet__accounts') }} as a on t.account_id = a.account_id
where t.is_success and t.txn_type in ('cash_in', 'cash_out')
group by cube (t.txn_date, t.txn_type, t.channel, a.segment)
having grouping(t.txn_date) = 0 and grouping(t.txn_type) = 0
