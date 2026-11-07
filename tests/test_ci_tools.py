import json

import pytest
from ci_report import render
from detect import ROUNDS, dbt_impact, plan, unit_of
from kb import CODEOWNERS, MANIFEST, codeowners
from lint import lint


def ran(p):
    return [r for r in ROUNDS if p["rounds"][r]]


@pytest.mark.parametrize("path, unit", [
    ("dbt/models/gold/ops/fct_orders.sql", "dbt"),
    ("kb/savings/metrics/balance.md", "kb:savings"),
    ("kb/rules.md", "kb"),
    ("kb/_template/metric.md", "kb"),
    ("evals/golden/kitchen_ops/K01.yaml", "golden:kitchen_ops"),
    ("evals/template_case.yaml", "evals"),
    ("airflow/dags/platform_daily.py", "airflow"),
    ("deploy/sync_release.sh", "deploy"),
    (".github/workflows/deploy.yml", "deploy"),
    (".github/workflows/ci.yml", "ci"),
    ("tools/gate.py", "ci"),
    ("tests/test_daily_report.py", "tests"),
    ("README.md", "docs"),
])
def test_every_path_maps_to_one_unit(path, unit):
    assert unit_of(path) == unit


def test_a_kb_change_skips_the_dbt_rounds():
    p = plan(["kb/savings/metrics/balance.md"])
    assert ran(p) == ["gate", "ground", "eval"]
    assert p["kb_areas"] == ["savings"] and p["eval_areas"] == ["savings"] and not p["contracts"]


def test_a_golden_case_change_runs_lint_and_eval_for_its_area():
    p = plan(["evals/golden/kitchen_ops/K04.yaml"])
    assert ran(p) == ["lint", "eval"]
    assert p["kb_areas"] == [] and p["eval_areas"] == ["kitchen_ops"]


def test_a_readme_change_runs_nothing():
    assert ran(plan(["README.md"])) == []


def test_a_deploy_script_change_runs_lint_and_the_simulation():
    assert ran(plan(["deploy/smoke_check.sh"])) == ["lint", "simulate"]


def test_a_tooling_change_runs_every_round_on_every_area():
    p = plan(["tools/detect.py"])
    assert ran(p) == ROUNDS
    assert p["kb_areas"] == ["kitchen_ops", "savings"] and p["contracts"]


def test_downstream_models_route_to_their_kb_area():
    manifest = {
        "nodes": {
            "model.data_platform.stg_kitchen__orders": {"name": "stg_kitchen__orders", "original_file_path": "models/silver/kitchen/stg_kitchen__orders.sql"},
            "model.data_platform.fct_orders": {"name": "fct_orders", "original_file_path": "models/gold/ops/fct_orders.sql"},
        },
        "sources": {},
        "exposures": {"exposure.data_platform.daily_report": {"name": "daily_report"}},
        "child_map": {"model.data_platform.stg_kitchen__orders": ["model.data_platform.fct_orders"], "model.data_platform.fct_orders": ["exposure.data_platform.daily_report"]},
    }
    assert dbt_impact(["dbt/models/silver/kitchen/stg_kitchen__orders.sql"], manifest) == (["stg_kitchen__orders"], ["fct_orders", "stg_kitchen__orders"], ["daily_report"])
    p = plan(["dbt/models/silver/kitchen/stg_kitchen__orders.sql"], manifest)
    assert ran(p) == ["lint", "gate", "ground", "eval"]
    assert p["kb_areas"] == ["kitchen_ops"] and p["contracts"]


def test_a_project_file_counts_every_model_as_reached():
    manifest = {"nodes": {}, "sources": {}, "exposures": {}, "child_map": {}}
    p = plan(["dbt/dbt_project.yml"], manifest)
    assert p["dbt"]["all"] and p["kb_areas"] == ["kitchen_ops", "savings"]


@pytest.mark.skipif(not MANIFEST.exists(), reason="run make parse first")
def test_a_source_change_reaches_the_savings_marts_in_the_real_manifest():
    p = plan(["dbt/models/silver/wallet/stg_wallet__transactions.sql"], json.loads(MANIFEST.read_text(encoding="utf-8")))
    assert {"fct_savings_daily", "agg_savings_flow_daily", "dim_account"} <= set(p["dbt"]["reached"])
    assert "fct_orders" not in p["dbt"]["reached"]
    assert p["kb_areas"] == ["savings"] and "daily_report" in p["dbt"]["exposures"]


def test_codeowners_uses_only_patterns_detect_understands():
    rules = codeowners(CODEOWNERS)
    assert all(pattern == "*" or (pattern.startswith("/") and pattern.endswith("/")) for pattern, _ in rules)
    assert plan(["kb/savings/index.md"])["owners"] == {"kb:savings": ["@loctu0402"]}


def test_lint_rejects_broken_yaml_and_python(tmp_path):
    (tmp_path / "bad.yml").write_text("a: [1\n", encoding="utf-8")
    (tmp_path / "bad.py").write_text("def broken(:\n", encoding="utf-8")
    problems, counts = lint([str(tmp_path / "bad.yml"), str(tmp_path / "bad.py")])
    assert counts["YAML"] == 1 and counts["Python"] == 1 and len(problems) == 2


def test_lint_parses_golden_sql_as_bigquery(tmp_path):
    case = tmp_path / "evals" / "golden" / "savings" / "S99.yaml"
    case.parent.mkdir(parents=True)
    case.write_text("expected_sql: |\n  select from where\ncheck_sql: |\n  select 1\n", encoding="utf-8")
    problems, _ = lint([case.as_posix()])
    assert len(problems) == 1 and "expected_sql is not valid BigQuery SQL" in problems[0]


def test_report_shows_each_round_why_it_ran_and_what_stopped():
    p = plan(["kb/savings/metrics/balance.md"])
    needs = {"gate": {"result": "failure"}, "ground": {"result": "skipped"}, "eval": {"result": "skipped"}}
    logs = {"gate": "  - kb/savings/metrics/balance.md leaves sections empty: ['Formula']\ngate: KB savings; 1 problems\n"}
    report = render(p, needs, logs)
    assert "| lint | - | skipped | not needed by this change |" in report
    assert "| gate | kb:savings | failed | gate: KB savings; 1 problems |" in report
    assert "| ground | kb:savings | not run | an earlier round failed |" in report
    assert "- gate: kb/savings/metrics/balance.md leaves sections empty" in report
    assert "| kb:savings | @loctu0402 |" in report


def test_report_says_when_the_live_eval_had_no_warehouse():
    p = plan(["evals/golden/savings/S01.yaml"])
    report = render(p, {"lint": {"result": "success"}, "eval": {"result": "success"}}, {"eval": "eval offline: 17 cases; 0 problems\n"})
    assert "| eval live | warehouse secret | skipped | no GCP_SA_KEY secret" in report


def test_report_without_a_plan_points_at_detect():
    assert "Detect did not finish" in render(None, {}, {})
