---
gotcha: recent-days-can-restate
area: kitchen_ops
applies_to: [fct_orders, agg_kitchen_daily, on_time_rate, delivery_time]
description: fct_orders merges the last three order days again on every run, so their delivery numbers can still move.
---

# The last three days can still change

## The trap
Quoting yesterday's on-time rate or delivery time as final, then finding a different number in the same table a day later.

## Why it happens
`fct_orders` is incremental. Each run merges the last three order days again so that deliveries confirmed late update their orders, and `agg_kitchen_daily` is rebuilt from it.

## Do this instead
Say that the last three days are provisional when an answer covers them. For a trend or a target check, end the period three days before the latest day.

## Detection
Compare the same day's `on_time_orders` across two consecutive runs. A change inside the three-day window is expected; a change outside it is a pipeline problem.
