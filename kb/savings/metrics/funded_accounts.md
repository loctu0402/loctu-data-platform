---
metric: funded_accounts
area: savings
label: Funded accounts
synonyms: [active savers, funded users, accounts with money]
model: fct_savings_daily
type: snapshot
numerator: funded_accounts
denominator: null
filters: []
columns: [date_day, funded_accounts]
grain: date_day
period: read the last day of the period
unit: accounts
---

# Funded accounts

## Definition
Funded accounts are accounts holding at least 1 currency unit at the end of the day. An opened account with no money is not funded, and an account that deposited and withdrew everything on the same day is not funded either.

## Formula
The numerator is `funded_accounts` on one day. There is no denominator.

```sql
funded_accounts
```

## Grain and period
One row is one day for the whole product. A week or a month reads the row of its last day. Adding days together counts the same account once per day.

## Source contract
| Column | Role |
|---|---|
| date_day | period |
| funded_accounts | numerator |

## Gotchas
- [Snapshots read the last day of a period](../gotchas/snapshots-read-the-last-day.md)

## Example
How many accounts held money when the quarter closed?

```sql
select funded_accounts
from gold.fct_savings_daily
where date_day = @quarter_end
```
