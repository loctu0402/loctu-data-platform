---
gotcha: read-one-cube-row-per-cut
area: savings
applies_to: [flow_by_channel, agg_savings_flow_daily]
description: agg_savings_flow_daily already holds an 'all' row for every cut, so summing rows double counts and summing accounts overcounts.
---

# Read one cube row per cut

## The trap
Summing `amount` over the channels of one segment returns twice the total, because the channel `'all'` row sits next to the channel rows, and summing every row of a day returns four times the total. Summing `accounts` over channels counts an account once per channel it used.

## Why it happens
The table looks like an ordinary daily aggregate, so `group by date_day` with `sum()` feels safe. The rolled-up rows written by `GROUP BY CUBE` are only visible as the value `'all'`.

## Do this instead
Pin every dimension you are not slicing by to `'all'`, and slice a dimension by filtering it to a value or excluding `'all'`. Read `accounts` from the single row of the cut, never as a sum.

## Detection
The singular test `assert_cube_total_row_matches_fact` checks that the cash in `'all'` row equals `fct_savings_daily` on amount and accounts. A query result above that total means rows were added together.
