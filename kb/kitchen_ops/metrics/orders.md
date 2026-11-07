---
metric: orders
area: kitchen_ops
label: Orders
synonyms: [order volume, orders placed, order count]
model: agg_kitchen_daily
type: additive
numerator: sum(orders)
denominator: null
filters: ["kitchen_id = 'all'", "platform = 'all'"]
columns: [date_day, kitchen_id, platform, orders]
grain: date_day x kitchen_id x platform
period: sum the days of the period
unit: orders
---

# Orders

## Definition
Orders counts every order placed with a kitchen on its local order day, whether it was completed or cancelled. Completed orders alone are the denominator of the delivery metrics, not this metric.

## Formula
The numerator is the sum of `orders` over the days asked, on the row of the kitchen and platform cut asked. There is no denominator.

```sql
sum(orders)
```

The default answer covers every kitchen and platform: `kitchen_id = 'all'` and `platform = 'all'`. Replace `'all'` with a value to slice.

## Grain and period
One row is one day for one combination of kitchen and platform, where `'all'` marks the rolled-up value. Orders add up across days.

## Source contract
| Column | Role |
|---|---|
| date_day | period |
| kitchen_id | filter |
| platform | filter |
| orders | numerator |

## Gotchas
- [Read one cube row per cut](../gotchas/read-one-cube-row-per-cut.md)

## Example
How many orders did the own app bring to kitchen K02 in a given month?

```sql
select sum(orders)
from gold.agg_kitchen_daily
where kitchen_id = 'K02' and platform = 'own_app'
  and date_day between @start_date and @end_date
```
