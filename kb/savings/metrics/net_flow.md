---
metric: net_flow
area: savings
label: Net flow
synonyms: [net inflow, net cash, net deposits]
model: fct_savings_daily
type: additive
numerator: sum(net_flow_amount)
denominator: null
filters: []
columns: [date_day, net_flow_amount]
grain: date_day
period: sum the days of the period
unit: currency
---

# Net flow

## Definition
Net flow is successful cash in minus successful cash out. Interest credited by the product is not a flow, so net flow never explains the whole change in the balance.

## Formula
The numerator is the sum of `net_flow_amount` over the days asked. There is no denominator. The column already equals `cash_in_amount - cash_out_amount` for each day.

```sql
sum(net_flow_amount)
```

## Grain and period
One row is one day for the whole product. Days add up, so a week or a month sums its days. A negative value means more money left than arrived.

## Source contract
| Column | Role |
|---|---|
| date_day | period |
| net_flow_amount | numerator |

## Gotchas
- [Interest moves the balance but is not a flow](../gotchas/interest-moves-balance-not-flow.md)

## Example
What was net flow in the first half of the year?

```sql
select sum(net_flow_amount)
from gold.fct_savings_daily
where date_day between @start_date and @end_date
```
