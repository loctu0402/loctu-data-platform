---
metric: cancel_rate
area: kitchen_ops
label: Cancellation rate
synonyms: [cancellations, cancelled orders share, cancel share]
model: agg_kitchen_daily
type: ratio
numerator: sum(orders) - sum(completed_orders)
denominator: sum(orders)
filters: ["kitchen_id = 'all'", "platform = 'all'"]
columns: [date_day, kitchen_id, platform, orders, completed_orders]
grain: date_day x kitchen_id x platform
period: sum the numerator and the denominator over the days, then divide
unit: share
---

# Cancellation rate

## Definition
The cancellation rate is cancelled orders over all orders placed. Every order that did not complete counts as cancelled, whoever cancelled it.

## Formula
The numerator is orders minus completed orders, summed. The denominator is orders, summed over the same rows.

```sql
safe_divide(sum(orders) - sum(completed_orders), sum(orders))
```

## Grain and period
One row is one day for one combination of kitchen and platform. A period sums the numerator and the denominator over its days, then divides once.

## Source contract
| Column | Role |
|---|---|
| date_day | period |
| kitchen_id | filter |
| platform | filter |
| orders | numerator and denominator |
| completed_orders | numerator |

## Gotchas
- [Read one cube row per cut](../gotchas/read-one-cube-row-per-cut.md)
- [Rates are ratios of sums](../gotchas/rates-are-ratios-of-sums.md)

## Example
How did cancellations compare across kitchens in a given week?

```sql
select kitchen_id, safe_divide(sum(orders) - sum(completed_orders), sum(orders)) as cancel_rate
from gold.agg_kitchen_daily
where platform = 'all' and kitchen_id != 'all'
  and date_day between @start_date and @end_date
group by kitchen_id
order by cancel_rate desc
```
