---
metric: delivery_time
area: kitchen_ops
label: Delivery time
synonyms: [average delivery minutes, delivery minutes, delivery speed]
model: agg_kitchen_daily
type: ratio
numerator: sum(delivery_minutes_sum)
denominator: sum(completed_orders)
filters: ["kitchen_id = 'all'", "platform = 'all'"]
columns: [date_day, kitchen_id, platform, delivery_minutes_sum, completed_orders]
grain: date_day x kitchen_id x platform
period: sum the numerator and the denominator over the days, then divide
unit: minutes
---

# Delivery time

## Definition
Delivery time is the average number of minutes from the customer's order to drop-off, over completed orders. It covers preparation and the ride together; cancelled orders have no delivery and are left out.

## Formula
The numerator is the total delivery minutes of completed orders, summed. The denominator is completed orders, summed over the same rows. The table stores the minute total, never the average, so any roll-up stays exact.

```sql
safe_divide(sum(delivery_minutes_sum), sum(completed_orders))
```

## Grain and period
One row is one day for one combination of kitchen and platform. A period sums the minute total and the completed orders over its days, then divides once.

## Source contract
| Column | Role |
|---|---|
| date_day | period |
| kitchen_id | filter |
| platform | filter |
| delivery_minutes_sum | numerator |
| completed_orders | denominator |

## Gotchas
- [Read one cube row per cut](../gotchas/read-one-cube-row-per-cut.md)
- [Rates are ratios of sums](../gotchas/rates-are-ratios-of-sums.md)
- [The last three days can still change](../gotchas/recent-days-can-restate.md)

## Example
How long did deliveries take for each kitchen in a given week?

```sql
select kitchen_id, safe_divide(sum(delivery_minutes_sum), sum(completed_orders)) as avg_minutes
from gold.agg_kitchen_daily
where platform = 'all' and kitchen_id != 'all'
  and date_day between @start_date and @end_date
group by kitchen_id
```
