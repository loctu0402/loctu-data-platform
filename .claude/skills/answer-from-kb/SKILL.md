---
name: answer-from-kb
description: Answer a business question about savings or kitchen performance from the gold tables, using only metrics defined in the knowledge base. Use for any "how much", "how many", "what share" or "which kitchen" question.
---

1. Read `agent/knowledge/rules.md` and find the metric in `agent/knowledge/metrics.yml` by name or synonym. No match means hand the question to an analyst.
2. Open the closest case in `agent/golden/cases.yml` and adapt its `gold_sql`. Keep its filters on `'all'` rows and its numerator and denominator.
3. Run the query against the gold dataset and check the latest `date_day` first.
4. Reply in two sentences: the number with its metric, period and denominator, then the date the data runs through.
5. If the question was new, add it to `cases.yml` with a `check_sql` that recomputes it from silver, and run `make check`.
