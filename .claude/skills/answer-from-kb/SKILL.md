---
name: answer-from-kb
description: Answer a business question about savings or kitchen performance from the gold tables, using only metrics defined in the knowledge base. Use for any "how much", "how many", "what share" or "which kitchen" question.
---

1. Read `kb/rules.md`, then the area index, `kb/savings/index.md` or `kb/kitchen_ops/index.md`. Find the metric by name or synonym. No metric atom means hand the question to an analyst.
2. Open the metric atom and build the query from it: its model, numerator, denominator, filters and period rule. Open every gotcha it links.
3. Run the query against the gold dataset and check the latest `date_day` first.
4. Reply in two sentences: the number with its metric, period and denominator, then the date the data runs through.
5. Never open `evals/`. The golden cases are the exam the agent is graded on.
