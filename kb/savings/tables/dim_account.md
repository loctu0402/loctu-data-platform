---
table: dim_account
area: savings
description: One row per savings account with acquisition attributes and its latest lifecycle state, feeding dashboards.
---

# dim_account

## Description
One row is one savings account: how and when it was acquired, when it was first funded, and its balance and lifecycle state on the latest day. It feeds the Looker Studio dashboards through Cube. The current columns describe the latest day only, so they cannot answer what an account looked like in the past.

## Essentials
| | |
|---|---|
| Primary key | account_id |
| Answers | Attributes of an account and its state today, for slicing dashboards. Not answerable here: certified product metrics, which come from the daily facts. |
| Partition | none |
| Built from | stg_wallet__accounts, int_wallet__account_day |

## Columns
| Column | Type | Meaning |
|---|---|---|
| account_id | string | Savings account identifier |
| user_id | string | App user who owns the account |
| opened_date | date | Local business day the account was opened |
| acquisition_channel | string | Where the account was acquired: app_home, referral, campaign or partner_bank |
| segment | string | Customer segment: mass, affluent or student |
| first_funded_date | date | First day the account held at least 1 unit, null if never funded |
| current_balance | numeric | Balance at the end of the latest day |
| current_state | string | Lifecycle state on the latest day: new, retained, reactivated, churned or inactive |

## Query pattern
```sql
select acquisition_channel, count(*) as accounts, countif(current_state in ('new', 'retained', 'reactivated')) as funded_now
from gold.dim_account
group by acquisition_channel
```

## Metrics
No certified metric reads this table. It backs dashboard slicing only.
