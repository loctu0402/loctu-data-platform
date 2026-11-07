---
gotcha: rates-are-ratios-of-sums
area: kitchen_ops
applies_to: [on_time_rate, cancel_rate, delivery_time]
description: A rate over a period or a group divides summed numerators by summed denominators, never averages daily or per-kitchen rates.
---

# Rates are ratios of sums

## The trap
Averaging seven daily on-time rates, or the rates of five kitchens, gives a quiet day or a small kitchen the same weight as a busy one.

## Why it happens
A daily rate is easy to compute per row, and `avg()` over a column of rates looks like the obvious roll-up. The table helps by storing only numerators and denominators, but a query can still divide first and average after.

## Do this instead
Sum the numerator and the denominator over every row in scope, then divide once with `safe_divide`. The same holds for delivery time, whose numerator is the stored minute total.

## Detection
Recompute the rate from `fct_orders` with `countif` over the same orders. A different answer means rates were averaged.
