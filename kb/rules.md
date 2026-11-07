# Answering rules

These rules hold for every area. Start at the area index, [savings](savings/index.md) or [kitchen operations](kitchen_ops/index.md), then open the one metric atom the question needs.

1. Answer only from the `gold` tables and only with a metric that has an atom in an area's `metrics/` folder. If the question needs anything else, say so and hand it to an analyst.
2. Build the query from the metric atom: its model, numerator, denominator, filters and period rule, and every gotcha it links.
3. Every answer names the metric, the period, the denominator for any rate, and the date the data runs through.
4. Balance and funded accounts are end-of-day snapshots. For a week or a month, read the last day; never sum them.
5. Rates come from summed numerators over summed denominators. Never average a daily rate.
6. `agg_savings_flow_daily` and `agg_kitchen_daily` hold one row per cut. Filter `'all'` for the dimensions you are not slicing by, and never add up `accounts` across rows.
7. Dates are local business days in Asia/Ho_Chi_Minh. "Yesterday" is the latest `date_day`.
8. When the latest day is missing, say the data is late. Do not answer from an older day without saying so.
9. Never read `evals/`. The golden cases are the exam the agent is graded on.
