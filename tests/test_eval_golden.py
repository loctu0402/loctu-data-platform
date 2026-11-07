import copy
from decimal import Decimal

import eval_golden
import pytest
import yaml
from eval_golden import case_problems, known_terms, matches, offline_checks
from kb import CASE_TEMPLATE, MANIFEST, area_names, load_area, load_cases, models

pytestmark = pytest.mark.skipif(not MANIFEST.exists(), reason="run make parse first")


@pytest.fixture
def ctx():
    answer, refusal = yaml.safe_load_all(CASE_TEMPLATE.read_text(encoding="utf-8"))
    areas = {n: load_area(n) for n in area_names()}
    return {"answer": answer, "refusal": refusal, "areas": areas, "models": models(), "terms": known_terms(areas.values())}


def check(ctx, cid, case):
    area = "savings" if cid.startswith("S") else "kitchen_ops"
    shape = ctx["refusal"] if case.get("expect_refusal") else ctx["answer"]
    return case_problems(f"evals/golden/{area}/{cid}.yaml", case, shape, area, ctx["areas"][area], ctx["models"], ctx["terms"])


def case(cid):
    area = "savings" if cid.startswith("S") else "kitchen_ops"
    return copy.deepcopy(load_cases(area)[cid][1])


def test_every_golden_case_passes_offline():
    cases, problems = offline_checks(area_names(), models())
    assert problems == []
    assert len(cases) >= 30


def test_check_sql_that_reads_gold_is_rejected(ctx):
    c = case("K04")
    c["check_sql"] = c["check_sql"].replace("{silver}.int_kitchen__orders_enriched", "{gold}.fct_orders")
    assert any("recompute the answer from silver" in p for p in check(ctx, "K04", c))


def test_expected_sql_must_read_the_metric_model(ctx):
    c = case("S01")
    c["expected_sql"] = c["expected_sql"].replace("fct_savings_daily", "agg_savings_flow_daily")
    assert any("does not read fct_savings_daily" in p for p in check(ctx, "S01", c))


def test_case_must_match_the_template_keys(ctx):
    c = case("S01")
    c["answer"] = 42
    assert any("template_case.yaml" in p for p in check(ctx, "S01", c))


def test_refusal_for_a_metric_the_kb_defines_is_stale(ctx):
    c = case("S16")
    c["rubric"]["missing"] = "net inflow"
    assert any("make it an answerable case" in p for p in check(ctx, "S16", c))


def test_a_metric_with_one_case_fails_coverage(monkeypatch):
    real = eval_golden.load_cases
    monkeypatch.setattr(eval_golden, "load_cases", lambda area: {k: v for k, v in real(area).items() if k not in ("S02", "S03")})
    _, problems = offline_checks(["savings"], models())
    assert any("balance.md has 1 golden cases" in p for p in problems)


def test_live_comparison_tolerates_rounding_but_not_a_wrong_answer():
    assert matches(Decimal("1000000.00"), 1000004.0)
    assert not matches(1000.0, 1100.0)
    assert matches("bank_transfer", "bank_transfer")
    assert not matches("K01", "K02")
    assert not matches(None, None)
