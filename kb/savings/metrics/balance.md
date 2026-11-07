---
metric: balance
area: savings
label: Savings balance
synonyms: [aum, savings balance, assets under management]
model: fct_savings_daily
type: snapshot
numerator: aum_end
denominator: null
filters: []
columns: [date_day, aum_end]
grain: date_day
period: read the last day of the period
unit: currency
---

# Savings balance

## Definition
The savings balance is the sum of every account's end-of-day balance, interest included. It is a snapshot of money held, so it is neither net flow nor cash in.

## Formula
The numerator is `aum_end` on one day. There is no denominator.

```sql
aum_end
```

## Grain and period
One row is one day for the whole product. A week or a month reads the row of its last day, and growth between two dates subtracts two snapshots.

## Source contract
| Column | Role |
|---|---|
| date_day | period |
| aum_end | numerator |

## Gotchas
- [Snapshots read the last day of a period](../gotchas/snapshots-read-the-last-day.md)
- [Interest moves the balance but is not a flow](../gotchas/interest-moves-balance-not-flow.md)

## Example
What did the product hold when the quarter closed?

```sql
select aum_end
from gold.fct_savings_daily
where date_day = @quarter_end
```
