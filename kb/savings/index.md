---
area: savings
owners: ["@loctu0402"]
description: Savings wallet balance, cash flows, account lifecycle and the deposit funnel.
---

# Savings

## Scope
The savings wallet holds a balance for each account and credits interest every day. This area answers how much money the product holds, how much moved in and out, how many accounts hold money, how many emptied, and how many savings tab visitors deposit. Product, finance and growth teams ask these questions, and the daily report and the analytics agent answer them from four gold models.

## Metrics
| Metric | What it answers | Model |
|---|---|---|
| [Savings balance](metrics/balance.md) | How much money the product holds at the end of a day | fct_savings_daily |
| [Net flow](metrics/net_flow.md) | Cash in minus cash out over a period | fct_savings_daily |
| [Funded accounts](metrics/funded_accounts.md) | How many accounts hold money at the end of a day | fct_savings_daily |
| [Account churn](metrics/account_churn.md) | How many funded accounts emptied over a period | fct_savings_daily |
| [Flow by channel](metrics/flow_by_channel.md) | Cash in or cash out, and distinct accounts, by channel and segment | agg_savings_flow_daily |
| [Deposit conversion](metrics/deposit_conversion.md) | Share of savings tab visitors who deposit the same day | fct_deposit_funnel_daily |

## Tables
| Table | One row is |
|---|---|
| [fct_savings_daily](tables/fct_savings_daily.md) | One day for the whole product |
| [agg_savings_flow_daily](tables/agg_savings_flow_daily.md) | One day for one cut of transaction type, channel and segment |
| [fct_deposit_funnel_daily](tables/fct_deposit_funnel_daily.md) | One day of the deposit funnel |
| [dim_account](tables/dim_account.md) | One savings account with its acquisition attributes and current state |

## Gotchas
| Gotcha | Applies to |
|---|---|
| [Snapshots read the last day of a period](gotchas/snapshots-read-the-last-day.md) | balance, funded_accounts, fct_savings_daily |
| [Interest moves the balance but is not a flow](gotchas/interest-moves-balance-not-flow.md) | balance, net_flow, fct_savings_daily |
| [Read one cube row per cut](gotchas/read-one-cube-row-per-cut.md) | flow_by_channel, agg_savings_flow_daily |
| [Daily distinct counts do not add up across days](gotchas/daily-distinct-counts-do-not-add-up.md) | flow_by_channel, deposit_conversion, agg_savings_flow_daily, fct_deposit_funnel_daily |

## Changelog
[changelog.md](changelog.md) records the two events that move these numbers: an interest rate cut and an acquisition campaign.

## Out of scope
The area holds no revenue, cost or customer value data, so it cannot answer profitability or lifetime value. App events cover the three savings tab steps only, so questions about installs, uninstalls or other screens go to an analyst. Account attributes in `dim_account` back dashboards, not certified metrics.
