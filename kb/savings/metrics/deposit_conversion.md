---
metric: deposit_conversion
area: savings
label: Deposit conversion
synonyms: [savings tab conversion, deposit funnel, deposit rate]
model: fct_deposit_funnel_daily
type: ratio
numerator: sum(users_deposited)
denominator: sum(users_opened)
filters: []
columns: [date_day, users_opened, users_deposited]
grain: date_day
period: sum the numerator and the denominator over the days, then divide
unit: share
---

# Deposit conversion

## Definition
Deposit conversion is users who completed a deposit over users who opened the savings tab, both counted on the same day. It divides two daily counts and does not follow a user's journey, so the numerator does not check that a depositor opened the tab that day.

## Formula
The numerator is users with a successful deposit, summed over the days. The denominator is users who opened the savings tab, summed over the same days.

```sql
safe_divide(sum(users_deposited), sum(users_opened))
```

## Grain and period
One row is one day. A week pools its days, which counts a user once per day they appear, and is never the average of seven daily rates.

## Source contract
| Column | Role |
|---|---|
| date_day | period |
| users_opened | denominator |
| users_deposited | numerator |

## Gotchas
- [Daily distinct counts do not add up across days](../gotchas/daily-distinct-counts-do-not-add-up.md)

## Example
What was deposit conversion over the campaign week?

```sql
select safe_divide(sum(users_deposited), sum(users_opened))
from gold.fct_deposit_funnel_daily
where date_day between @start_date and @end_date
```
