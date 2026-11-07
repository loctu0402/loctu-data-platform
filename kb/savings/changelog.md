# Savings changelog

The synthetic sources roll forward to yesterday on every load, so events are dated in days before the latest load.

## Interest rate cut, 78 days before the latest load
**Type:** ratio-change. **Affects:** [balance](metrics/balance.md), [net flow](metrics/net_flow.md), [fct_savings_daily](tables/fct_savings_daily.md).

The annual rate fell from 4.5% to 3.8%. Withdrawals ran at about two and a half times their usual rate for the next three weeks, so net flow turned weaker and the balance grew more slowly. A comparison that crosses this date should use the expected-value band of the daily report, not a plain week-on-week change.

## Acquisition campaign, 53 to 47 days before the latest load
**Type:** volatile-date. **Affects:** [funded accounts](metrics/funded_accounts.md), [account churn](metrics/account_churn.md), [dim_account](tables/dim_account.md).

A seven-day campaign tripled new accounts. Funded accounts step up during the campaign, and churned accounts rise in the months after because the funded base is larger. Leave these seven days out of any baseline used for a trend.
