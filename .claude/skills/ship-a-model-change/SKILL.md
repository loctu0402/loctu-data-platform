---
name: ship-a-model-change
description: Change a dbt model so its contract, the semantic layer, the knowledge base and the golden set move together. Use when adding, renaming or redefining any column in a silver or gold model.
---

1. Find what the change reaches: `dbt ls --select <model>+ --resource-type model` from `dbt/`.
2. Edit the SQL, then the model YAML: column, `data_type` and description. Gold models enforce their contract, so a mismatch fails the build.
3. If a gold column changes meaning or name, update the Cube model in `semantic/cube/model/`, the table atom in `kb/<area>/tables/` and every metric atom that lists the column. Add a changelog entry when a number moves.
4. Add or adjust a golden case that exercises the change, with a `check_sql` that recomputes it a second way.
5. Run `make check`. It parses dbt, lints SQL, runs the knowledge gate and the tests.
6. Run `dbt build --select <model>+` against your dev dataset and `python agent/eval_golden.py --live`, then open the pull request.
