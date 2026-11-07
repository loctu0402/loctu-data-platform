---
metric: account_churn
area: savings
label: Account churn
synonyms: [churned accounts, lost savers, emptied accounts]
model: fct_savings_daily
type: additive
numerator: sum(churned_accounts)
denominator: null
filters: []
columns: [date_day, churned_accounts]
grain: date_day
period: sum the days of the period
unit: accounts
---

# Account churn

## Definition
Account churn counts accounts that were funded at the end of the previous day and hold less than 1 currency unit at the end of the day. It counts events, not accounts, so an account that empties twice in a month counts twice.

## Formula
The numerator is the sum of `churned_accounts` over the days asked. There is no denominator, and this metric is not a churn rate.

```sql
sum(churned_accounts)
```

## Grain and period
One row is one day for the whole product. Days add up, so a week or a month sums its days.

## Source contract
| Column | Role |
|---|---|
| date_day | period |
| churned_accounts | numerator |

## Gotchas
None. Churn is an event count, so the snapshot rule for funded accounts does not apply.

## Example
How many accounts emptied during the campaign weeks?

```sql
select sum(churned_accounts)
from gold.fct_savings_daily
where date_day between @start_date and @end_date
```
