---
table: <dbt model name, the same as the file name>
area: <area folder name>
description: <one line on what one row is and what it feeds>
---

# <model name>

## Description
<What one row is, what the table feeds, and anything about it that looks wrong but is correct.>

## Essentials
| | |
|---|---|
| Primary key | <columns> |
| Answers | <the question shapes this table is certified for> |
| Partition | <column, or none> |
| Built from | <upstream models> |

## Columns
| Column | Type | Meaning |
|---|---|---|
| <column> | <contract data type> | <meaning> |

## Query pattern
<One runnable SELECT with the required filters already in it.>

## Metrics
<A link to each metric this table backs.>
