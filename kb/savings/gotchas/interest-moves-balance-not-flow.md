---
gotcha: interest-moves-balance-not-flow
area: savings
applies_to: [balance, net_flow, fct_savings_daily]
description: The balance grows by net flow plus interest, so balance growth and net flow never match.
---

# Interest moves the balance but is not a flow

## The trap
Explaining a change in the balance with net flow alone leaves a gap, and reading the gap as missing money or a data error.

## Why it happens
Net flow sounds like everything that moved, but it counts only customer cash in and cash out. Interest is credited by the product every day and lands in the balance without passing through net flow.

## Do this instead
Reconcile with `aum_end` at the end minus `aum_end` at the start equals `sum(net_flow_amount) + sum(interest_amount)` over the days in between. Quote net flow for customer behaviour and balance growth for the size of the book.

## Detection
The dbt test `assert_aum_moves_only_by_flows` fails the build on any day where the balance change differs from booked flows plus interest by more than 1 unit.
