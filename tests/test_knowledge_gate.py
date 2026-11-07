from pathlib import Path

import pytest
from eval_golden import MANIFEST, gold_contracts, offline_checks


@pytest.mark.skipif(not Path(MANIFEST).exists(), reason="run dbt parse first")
def test_knowledge_base_matches_dbt_contracts():
    _, _, problems = offline_checks(gold_contracts(MANIFEST))
    assert problems == []


def test_gate_catches_a_renamed_column():
    contracts = gold_contracts(MANIFEST) if Path(MANIFEST).exists() else {}
    if not contracts:
        pytest.skip("run dbt parse first")
    contracts["fct_savings_daily"] = contracts["fct_savings_daily"] - {"aum_end"} | {"balance_end"}
    _, _, problems = offline_checks(contracts)
    assert any("aum_end" in p for p in problems)
