# Kitchen operations changelog

The synthetic sources roll forward to yesterday on every load, so events are dated in days before the latest load.

## Own courier fleet, 122 days before the latest load
**Type:** operations-change. **Affects:** [delivery time](metrics/delivery_time.md), [on-time delivery rate](metrics/on_time_rate.md), [fct_orders](tables/fct_orders.md).

Deliveries moved from third-party couriers to an own fleet. Ride time fell by about a fifth, so delivery time dropped and the on-time rate rose from that day. A comparison across this date measures the fleet switch, not kitchen performance, so split the period at the switch.

## Fifth kitchen opens, 163 days before the latest load
**Type:** volatile-date. **Affects:** [orders](metrics/orders.md), [agg_kitchen_daily](tables/agg_kitchen_daily.md).

Kitchen K05 started taking orders, which lifted total orders by about a quarter. Compare kitchens over days when all of them were open, and read growth in total orders against the number of open kitchens.
