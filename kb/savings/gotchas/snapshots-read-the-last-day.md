---
gotcha: snapshots-read-the-last-day
area: savings
applies_to: [balance, funded_accounts, fct_savings_daily]
description: Balance and funded accounts are end-of-day snapshots, so a week or a month reads its last day and never sums its days.
---

# Snapshots read the last day of a period

## The trap
Summing `aum_end` or `funded_accounts` over a week returns about seven times the real balance or account count.

## Why it happens
The same table holds flows that do add up, such as `cash_in_amount` and `churned_accounts`, so `sum()` over a date range looks like the natural roll-up for every column.

## Do this instead
Filter the snapshot to the last day of the period, or take the value on that day with `max(if(date_day = @period_end, aum_end, null))`. For growth, subtract the snapshot at the start from the snapshot at the end.

## Detection
A weekly balance that is several times the latest daily balance, or a monthly funded count larger than all accounts in `dim_account`, means days were summed.
