# Answering rules

1. Answer only from the `gold` tables and only with a metric in `metrics.yml`. If the question needs anything else, say so and hand it to an analyst.
2. Every answer names the metric, the period, the denominator for any rate, and the date the data runs through.
3. Balance and funded accounts are end-of-day snapshots. For a week or a month, read the last day; never sum them.
4. Rates come from summed numerators over summed denominators. Never average a daily rate.
5. `agg_savings_flow_daily` and `agg_kitchen_daily` hold one row per cut. Filter `'all'` for the dimensions you are not slicing by, and never add up `accounts` across rows.
6. Dates are local business days in Asia/Ho_Chi_Minh. "Yesterday" is the latest `date_day`.
7. When the latest day is missing, say the data is late. Do not answer from an older day without saying so.
