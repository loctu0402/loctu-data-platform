import copy

import pytest
from gate import area_problems, contract_problems, metric_problems, term_problems
from ground import ground_problems
from kb import MANIFEST, area_names, codeowners, column_refs, load_area, models

needs_manifest = pytest.mark.skipif(not MANIFEST.exists(), reason="run make parse first")


@pytest.fixture
def savings():
    return copy.deepcopy(load_area("savings"))


def test_every_area_passes_the_gate():
    rules = codeowners()
    areas = [load_area(n) for n in area_names()]
    assert [p for a in areas for p in area_problems(a, rules)] + term_problems(areas) == []


@needs_manifest
def test_contracts_and_ground_pass():
    areas = [load_area(n) for n in area_names()]
    assert contract_problems(models(), areas) == []
    assert ground_problems(areas, models())[0] == []


def test_column_refs_skip_functions_keywords_and_strings():
    assert column_refs("sum(orders) - sum(completed_orders)") == {"orders", "completed_orders"}
    assert column_refs("kitchen_id = 'all' and platform is not null") == {"kitchen_id", "platform"}


def test_gate_catches_a_formula_reading_an_undeclared_column(savings):
    savings.metrics["net_flow"].meta["numerator"] = "sum(cash_in_amount)"
    assert any("cash_in_amount" in p for p in metric_problems(savings))


def test_gate_catches_a_source_contract_table_that_drifts(savings):
    m = savings.metrics["balance"]
    m.body = m.body.replace("| aum_end | numerator |", "| aum_end | numerator |\n| cash_in_amount | numerator |")
    assert any("Source contract" in p for p in metric_problems(savings))


def test_gate_catches_a_ratio_without_a_denominator(savings):
    savings.metrics["deposit_conversion"].meta["denominator"] = None
    assert any("denominator" in p for p in metric_problems(savings))


def test_gate_catches_a_missing_section_and_a_placeholder(savings):
    m = savings.metrics["balance"]
    m.body = m.body.replace("## Example", "## Sample").replace("The savings balance is", "<FILL the definition>")
    problems = area_problems(savings, codeowners())
    assert any("sections" in p for p in problems)
    assert any("placeholder" in p for p in problems)


def test_gate_catches_an_atom_the_index_does_not_link(savings):
    savings.index.body = savings.index.body.replace("(metrics/net_flow.md)", "(metrics/balance.md)")
    assert any("net_flow.md is not linked" in p for p in area_problems(savings, codeowners()))


def test_gate_catches_owners_that_differ_from_codeowners(savings):
    savings.index.meta["owners"] = ["@someone-else"]
    assert any("CODEOWNERS" in p for p in area_problems(savings, codeowners()))


def test_gate_catches_a_synonym_claimed_by_two_metrics():
    areas = [copy.deepcopy(load_area(n)) for n in area_names()]
    kitchen = next(a for a in areas if a.name == "kitchen_ops")
    kitchen.metrics["orders"].meta["synonyms"].append("net inflow")
    assert any("net inflow" in p for p in term_problems(areas))


@needs_manifest
def test_contract_gate_catches_a_gold_model_without_a_table_atom(savings):
    areas = [savings]
    assert any("fct_orders has no table atom" in p for p in contract_problems(models(), areas))


@needs_manifest
def test_ground_catches_a_renamed_contract_column(savings):
    contracts = models()
    contracts["fct_savings_daily"]["columns"]["balance_end"] = contracts["fct_savings_daily"]["columns"].pop("aum_end")
    problems = ground_problems([savings], contracts)[0]
    assert any("balance.md reads ['aum_end']" in p for p in problems)
    assert any("leaves out contract column balance_end" in p for p in problems)


@needs_manifest
def test_ground_catches_a_changed_column_type(savings):
    contracts = models()
    contracts["agg_savings_flow_daily"]["columns"]["accounts"] = "float64"
    assert any("documents accounts as int64" in p for p in ground_problems([savings], contracts)[0])
