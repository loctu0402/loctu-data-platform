---
area: kitchen_ops
owners: ["@loctu0402"]
description: Cloud-kitchen order volume, delivery speed, on-time delivery and cancellations by kitchen and platform.
---

# Kitchen operations

## Scope
The business runs five cloud kitchens that take orders through its own app and two aggregator platforms. This area answers how many orders the kitchens took, how fast and how reliably they delivered, and how many orders were cancelled, for any kitchen and platform. The operations team asks these questions, and the daily report and the analytics agent answer them from two gold models.

## Metrics
| Metric | What it answers | Model |
|---|---|---|
| [Orders](metrics/orders.md) | How many orders were placed, completed or cancelled | agg_kitchen_daily |
| [On-time delivery rate](metrics/on_time_rate.md) | Share of completed orders delivered within 35 minutes | agg_kitchen_daily |
| [Cancellation rate](metrics/cancel_rate.md) | Share of orders that were cancelled | agg_kitchen_daily |
| [Delivery time](metrics/delivery_time.md) | Average minutes from order to drop-off | agg_kitchen_daily |

## Tables
| Table | One row is |
|---|---|
| [fct_orders](tables/fct_orders.md) | One kitchen order with its delivery outcome |
| [agg_kitchen_daily](tables/agg_kitchen_daily.md) | One day for one cut of kitchen and platform |

## Gotchas
| Gotcha | Applies to |
|---|---|
| [Read one cube row per cut](gotchas/read-one-cube-row-per-cut.md) | orders, on_time_rate, cancel_rate, delivery_time, agg_kitchen_daily |
| [Rates are ratios of sums](gotchas/rates-are-ratios-of-sums.md) | on_time_rate, cancel_rate, delivery_time |
| [The last three days can still change](gotchas/recent-days-can-restate.md) | fct_orders, agg_kitchen_daily, on_time_rate, delivery_time |

## Changelog
[changelog.md](changelog.md) records the two events that move these numbers: the switch to an own courier fleet and the opening of the fifth kitchen.

## Out of scope
The area holds net revenue but no food, packaging or courier cost, so it cannot answer margin or profit. Orders carry the courier type, not the courier, so questions about individual couriers go to an analyst. Ratings exist in the gold tables but are not a certified metric yet.
