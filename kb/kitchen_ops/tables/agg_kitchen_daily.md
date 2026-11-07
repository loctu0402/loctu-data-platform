---
table: agg_kitchen_daily
area: kitchen_ops
description: One row per day per cut of kitchen and platform, with 'all' rows and rate numerators and denominators, feeding the report and the agent.
---

# agg_kitchen_daily

## Description
One row is one day for one combination of kitchen and platform. `GROUP BY CUBE` writes a row for every combination, and `'all'` marks the rolled-up value. No rate is stored: each rate keeps its numerator and denominator, so a week, a kitchen or a platform recomputes it exactly.

## Essentials
| | |
|---|---|
| Primary key | date_day, kitchen_id, platform |
| Answers | Orders, completed orders, on-time orders, net revenue, delivery minutes and ratings for any kitchen and platform cut, on a day or summed over days. Not answerable here: brand, courier type or anything per order. |
| Partition | date_day |
| Built from | fct_orders |

## Columns
| Column | Type | Meaning |
|---|---|---|
| date_day | date | Local business day of the orders |
| kitchen_id | string | Kitchen, or 'all' for every kitchen |
| platform | string | Ordering platform, or 'all' for every platform |
| orders | int64 | Orders placed, completed or cancelled |
| completed_orders | int64 | Orders delivered |
| on_time_orders | int64 | Completed orders dropped off within the on-time window |
| net_revenue | numeric | Net amount of completed orders |
| delivery_minutes_sum | float64 | Total delivery minutes of completed orders |
| rating_sum | int64 | Total rating points of rated completed orders |
| rating_count | int64 | Rated completed orders |

## Query pattern
```sql
select date_day, orders, completed_orders, on_time_orders, delivery_minutes_sum
from gold.agg_kitchen_daily
where kitchen_id = 'all' and platform = 'all'
  and date_day between @start_date and @end_date
order by date_day
```

## Metrics
- [Orders](../metrics/orders.md)
- [On-time delivery rate](../metrics/on_time_rate.md)
- [Cancellation rate](../metrics/cancel_rate.md)
- [Delivery time](../metrics/delivery_time.md)
