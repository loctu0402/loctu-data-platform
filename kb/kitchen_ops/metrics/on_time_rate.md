---
metric: on_time_rate
area: kitchen_ops
label: On-time delivery rate
synonyms: [on-time delivery, delivery sla, on time]
model: agg_kitchen_daily
type: ratio
numerator: sum(on_time_orders)
denominator: sum(completed_orders)
filters: ["kitchen_id = 'all'", "platform = 'all'"]
columns: [date_day, kitchen_id, platform, on_time_orders, completed_orders]
grain: date_day x kitchen_id x platform
period: sum the numerator and the denominator over the days, then divide
unit: share
---

# On-time delivery rate

## Definition
The on-time delivery rate is the share of completed orders dropped off within 35 minutes of the order time. The clock starts when the customer orders, not when the courier picks up, and cancelled orders are outside both sides of the ratio.

## Formula
The numerator is completed orders delivered within the on-time window, summed. The denominator is completed orders, summed over the same rows. The 35-minute window is the dbt variable `on_time_minutes`.

```sql
safe_divide(sum(on_time_orders), sum(completed_orders))
```

## Grain and period
One row is one day for one combination of kitchen and platform. A period sums the numerator and the denominator over its days, then divides once.

## Source contract
| Column | Role |
|---|---|
| date_day | period |
| kitchen_id | filter |
| platform | filter |
| on_time_orders | numerator |
| completed_orders | denominator |

## Gotchas
- [Read one cube row per cut](../gotchas/read-one-cube-row-per-cut.md)
- [Rates are ratios of sums](../gotchas/rates-are-ratios-of-sums.md)
- [The last three days can still change](../gotchas/recent-days-can-restate.md)

## Example
How reliable were the aggregator platforms in a given month, platform by platform?

```sql
select platform, safe_divide(sum(on_time_orders), sum(completed_orders)) as on_time_rate
from gold.agg_kitchen_daily
where kitchen_id = 'all' and platform in ('aggregator_a', 'aggregator_b')
  and date_day between @start_date and @end_date
group by platform
```
