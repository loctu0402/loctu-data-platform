---
gotcha: read-one-cube-row-per-cut
area: kitchen_ops
applies_to: [orders, on_time_rate, cancel_rate, delivery_time, agg_kitchen_daily]
description: agg_kitchen_daily already holds an 'all' row for every cut, so summing rows across kitchens or platforms double counts.
---

# Read one cube row per cut

## The trap
Summing `orders` over the kitchen rows of a day with the platform pinned to `'all'` returns twice the total, because the kitchen `'all'` row sits next to the kitchen rows, and summing every row of a day returns four times the total.

## Why it happens
The table looks like an ordinary daily aggregate by kitchen and platform. The rolled-up rows written by `GROUP BY CUBE` are only visible as the value `'all'`.

## Do this instead
Pin every dimension you are not slicing by to `'all'`. To compare kitchens, keep `platform = 'all'` and exclude `kitchen_id = 'all'`; to compare platforms, do the opposite.

## Detection
The `'all'` and `'all'` row of a day must equal `count(*)` of `fct_orders` on that order date. A query result above it means rows were added together.
