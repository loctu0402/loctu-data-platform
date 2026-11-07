---
table: fct_savings_daily
area: savings
description: One row per day for the whole savings product, feeding the daily report, the agent and Cube.
---

# fct_savings_daily

## Description
One row is one day for the whole savings product: the end-of-day balance, the day's flows and the account lifecycle counts. It feeds the daily report, the analytics agent and the `savings_daily` Cube model. Balance and funded accounts are snapshots and do not add up across days; flows and lifecycle counts do. The balance moves by cash in minus cash out plus interest, and a dbt test fails the build when a day breaks that identity.

## Essentials
| | |
|---|---|
| Primary key | date_day |
| Answers | End-of-day balance and funded accounts on a date. Cash in, cash out, net flow, interest and lifecycle counts over any period. Not answerable here: anything by channel, segment or account. |
| Partition | date_day |
| Built from | int_wallet__account_day, stg_wallet__daily_rates |

## Columns
| Column | Type | Meaning |
|---|---|---|
| date_day | date | Local business day in Asia/Ho_Chi_Minh |
| aum_end | numeric | Sum of end-of-day balances across all accounts |
| cash_in_amount | numeric | Successful cash in on the day |
| cash_out_amount | numeric | Successful cash out on the day, as a positive amount |
| interest_amount | numeric | Interest credited on the day |
| net_flow_amount | numeric | Cash in minus cash out; interest is excluded |
| funded_accounts | int64 | Accounts holding at least 1 unit at end of day |
| new_funded_accounts | int64 | Accounts funded for the first time on the day |
| reactivated_accounts | int64 | Previously funded accounts funded again on the day |
| churned_accounts | int64 | Accounts funded the day before and empty at end of day |
| depositing_accounts | int64 | Accounts with any successful cash in on the day |
| withdrawing_accounts | int64 | Accounts with any successful cash out on the day |
| annual_rate | float64 | Annual interest rate in force on the day |

## Query pattern
```sql
select date_day, aum_end, net_flow_amount, funded_accounts, churned_accounts
from gold.fct_savings_daily
where date_day between @start_date and @end_date
order by date_day
```

## Metrics
- [Savings balance](../metrics/balance.md)
- [Net flow](../metrics/net_flow.md)
- [Funded accounts](../metrics/funded_accounts.md)
- [Account churn](../metrics/account_churn.md)
