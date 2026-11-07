---
table: agg_savings_flow_daily
area: savings
description: One row per day per cut of transaction type, channel and segment, with 'all' rows, feeding dashboards and the agent.
---

# agg_savings_flow_daily

## Description
One row is one day for one combination of transaction type, funding channel and customer segment. `GROUP BY CUBE` writes a row for every combination, and `'all'` in channel or segment marks the rolled-up value, so distinct accounts are counted at each cut instead of summed. Transaction type has no `'all'` row, because adding cash in to cash out has no meaning. Only successful cash in and cash out land here.

## Essentials
| | |
|---|---|
| Primary key | date_day, txn_type, channel, segment |
| Answers | Cash in or cash out amount, transaction count and distinct accounts for any channel and segment cut, on a day or summed over days for amounts. Not answerable here: interest, balances, or distinct accounts over more than one day. |
| Partition | date_day |
| Built from | stg_wallet__transactions, stg_wallet__accounts |

## Columns
| Column | Type | Meaning |
|---|---|---|
| date_day | date | Local business day of the transaction |
| txn_type | string | cash_in or cash_out |
| channel | string | Funding channel, or 'all' for every channel |
| segment | string | Customer segment, or 'all' for every segment |
| amount | numeric | Successful amount moved on the cut |
| txn_count | int64 | Successful transactions on the cut |
| accounts | int64 | Distinct accounts that moved money on the cut that day |

## Query pattern
```sql
select channel, amount, accounts
from gold.agg_savings_flow_daily
where date_day = @day and txn_type = 'cash_in' and segment = 'all' and channel != 'all'
order by amount desc
```

## Metrics
- [Flow by channel](../metrics/flow_by_channel.md)
