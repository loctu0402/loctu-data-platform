---
table: fct_orders
area: kitchen_ops
description: One row per kitchen order with its delivery outcome, merged daily with a three-day lookback.
---

# fct_orders

## Description
One row is one order placed with a kitchen, with its delivery outcome when it completed. It feeds `agg_kitchen_daily`, the `orders` Cube model and the analytics agent. The model is incremental: each run merges the last three order days again so late deliveries update their orders. Delivery fields are null for cancelled orders.

## Essentials
| | |
|---|---|
| Primary key | order_id |
| Answers | Order-level detail such as brand, courier type, rating, preparation and delivery minutes. Certified metrics read `agg_kitchen_daily` instead; this table is for drilling into the orders behind them. |
| Partition | order_date |
| Built from | int_kitchen__orders_enriched |

## Columns
| Column | Type | Meaning |
|---|---|---|
| order_id | string | Order identifier |
| kitchen_id | string | Kitchen that prepared the order |
| brand | string | Virtual brand the order was placed under |
| platform | string | own_app, aggregator_a or aggregator_b |
| ordered_at | timestamp | Order time in UTC |
| order_date | date | Local business day of the order in Asia/Ho_Chi_Minh |
| net_amount | numeric | Subtotal minus discount |
| is_completed | bool | True when the order was delivered, false when cancelled |
| courier_type | string | fleet or third_party, null for cancelled orders |
| rating | int64 | Customer rating from 1 to 5, null when not rated |
| prep_minutes | float64 | Minutes from order to courier pickup |
| delivery_minutes | float64 | Minutes from order to drop-off |
| is_on_time | bool | Completed and dropped off within the on-time window from the order time |

## Query pattern
```sql
select order_id, kitchen_id, platform, courier_type, delivery_minutes, is_on_time
from gold.fct_orders
where order_date = @day and is_completed and not is_on_time
order by delivery_minutes desc
```

## Metrics
No certified metric reads this table directly. It is the order grain behind [agg_kitchen_daily](agg_kitchen_daily.md) and its four metrics.
