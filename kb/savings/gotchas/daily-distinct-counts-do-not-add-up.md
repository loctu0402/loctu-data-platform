---
gotcha: daily-distinct-counts-do-not-add-up
area: savings
applies_to: [flow_by_channel, deposit_conversion, agg_savings_flow_daily, fct_deposit_funnel_daily]
description: Distinct accounts and users are counted per day, so a sum over days counts a returning account or user once per day.
---

# Daily distinct counts do not add up across days

## The trap
Summing `accounts` or `users_opened` over a week and calling the result the unique accounts or users of that week.

## Why it happens
Daily counts look additive like amounts. A user who opens the savings tab on five days is five rows of one, not one user.

## Do this instead
Say "account-days" or "user-days" when a period sums daily counts, as deposit conversion does for both its numerator and denominator. Unique accounts or users over a period need the silver models and are not a certified metric here, so hand that question to an analyst.

## Detection
A weekly unique count close to seven times a typical day is a sum of daily counts.
