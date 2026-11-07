---
metric: flow_by_channel
area: savings
label: Flow by channel
synonyms: [cash in by channel, deposit channel mix, cash in, cash out, withdrawals]
model: agg_savings_flow_daily
type: additive
numerator: sum(amount)
denominator: null
filters: ["txn_type = 'cash_in'", "channel = 'all'", "segment = 'all'"]
columns: [date_day, txn_type, channel, segment, amount, accounts]
grain: date_day x txn_type x channel x segment
period: sum amount over the days; read accounts from one row of one day
unit: currency and accounts
---

# Flow by channel

## Definition
Flow by channel is the money that successfully moved in or out of savings on one cut of funding channel and customer segment, with the distinct accounts that moved it. It covers cash in and cash out only; interest is not in this table.

## Formula
The numerator is the sum of `amount` over the days asked, on the row of the cut asked. There is no denominator. Distinct accounts come from `accounts` on one row for one day and are never summed.

```sql
sum(amount)
```

The default answer is total cash in: `txn_type = 'cash_in'` with `'all'` for channel and segment. Set `txn_type` to the direction asked, and replace `'all'` with a value to slice by that dimension.

## Grain and period
One row is one day for one combination of transaction type, channel and segment, where `'all'` marks the rolled-up value. Amounts add up across days. Accounts do not.

## Source contract
| Column | Role |
|---|---|
| date_day | period |
| txn_type | filter |
| channel | filter |
| segment | filter |
| amount | numerator |
| accounts | distinct accounts on one row |

## Gotchas
- [Read one cube row per cut](../gotchas/read-one-cube-row-per-cut.md)
- [Daily distinct counts do not add up across days](../gotchas/daily-distinct-counts-do-not-add-up.md)

## Example
How much did student customers deposit through linked cards in a given week?

```sql
select sum(amount)
from gold.agg_savings_flow_daily
where txn_type = 'cash_in' and channel = 'linked_card' and segment = 'student'
  and date_day between @start_date and @end_date
```
