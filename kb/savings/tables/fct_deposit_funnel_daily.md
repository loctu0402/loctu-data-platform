---
table: fct_deposit_funnel_daily
area: savings
description: One row per day of the savings deposit funnel from app events, distinct users per step.
---

# fct_deposit_funnel_daily

## Description
One row is one day of the deposit funnel built from app events: distinct users who opened the savings tab, started a deposit and completed one. Each step is counted on its own, so a step can hold users who skipped the step before it on that day.

## Essentials
| | |
|---|---|
| Primary key | date_day |
| Answers | Daily users at each funnel step and the conversion between steps, on a day or pooled over days. Not answerable here: unique users over a week or a month, or anything outside the savings tab. |
| Partition | none |
| Built from | stg_app__events |

## Columns
| Column | Type | Meaning |
|---|---|---|
| date_day | date | Local business day of the events |
| users_opened | int64 | Distinct users who opened the savings tab |
| users_started_deposit | int64 | Distinct users who started a deposit |
| users_deposited | int64 | Distinct users with a successful deposit |

## Query pattern
```sql
select date_day, users_opened, users_started_deposit, users_deposited
from gold.fct_deposit_funnel_daily
where date_day between @start_date and @end_date
order by date_day
```

## Metrics
- [Deposit conversion](../metrics/deposit_conversion.md)
