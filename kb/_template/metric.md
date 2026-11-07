---
metric: <file name without .md>
area: <area folder name>
label: <business name>
synonyms: [<words a stakeholder uses for it>]
model: <the gold model the metric reads>
type: <additive, snapshot or ratio>
numerator: <SQL expression over the model>
denominator: <SQL expression for a ratio, null for other types>
filters: [<SQL predicate the default answer applies>]
columns: [<every contract column the metric reads>]
grain: <the model grain>
period: <how a week or a month rolls up>
unit: <currency, accounts, users, orders, share or minutes>
---

# <Label>

## Definition
<One sentence that tells this metric apart from its look-alikes, then what it does not cover.>

## Formula
<The numerator and the denominator in words, then the SQL.>

## Grain and period
<What one row is and how a longer period reads.>

## Source contract
| Column | Role |
|---|---|
| <column> | <numerator, denominator, filter or period> |

## Gotchas
<A link to each gotcha this metric depends on.>

## Example
<A question in a stakeholder's words and the SQL that answers it.>
