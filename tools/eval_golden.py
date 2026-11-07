import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml
from kb import CASE_TEMPLATE, MANIFEST, PLACEHOLDER, ROOT, area_names, load_area, load_cases, models

MIN_CASES_PER_METRIC = 2
RESULTS = ROOT / "evals" / "results"


def strings(value):
    if isinstance(value, dict):
        return [s for v in value.values() for s in strings(v)]
    if isinstance(value, list):
        return [s for v in value for s in strings(v)]
    return [str(value)]


def known_terms(areas):
    return {
        term.lower().replace("_", " "): f"{a.name}/{name}"
        for a in areas
        for name, m in a.metrics.items()
        for term in [name, str(m.meta.get("label")), *map(str, m.meta.get("synonyms") or [])]
    }


def case_problems(rel, case, shape, area, kb_area, models_, terms):
    problems = []
    if set(case) != set(shape):
        problems.append(f"{rel} has keys {sorted(case)}, evals/template_case.yaml has {sorted(shape)}")
        return problems
    rubric = case["rubric"] or {}
    if set(rubric) != set(shape["rubric"]):
        problems.append(f"{rel} rubric has {sorted(rubric)}, the template has {sorted(shape['rubric'])}")
        return problems
    if case["id"] != Path(rel).stem or case["area"] != area:
        problems.append(f"{rel} must carry id {Path(rel).stem} and area {area}")
    found = next((PLACEHOLDER.search(s) for s in strings(case) if PLACEHOLDER.search(s)), None)
    if found:
        problems.append(f"{rel} still holds a template placeholder: {found.group()}")
    if case.get("expect_refusal"):
        missing = str(rubric["missing"]).lower()
        if missing in terms:
            problems.append(f"{rel} expects a refusal for '{missing}', which the KB now defines as {terms[missing]}; make it an answerable case")
        return problems
    metric = kb_area.metrics.get(rubric["metric"])
    if not metric:
        problems.append(f"{rel} asks about {rubric['metric']}, which kb/{area} does not define")
    if not rubric["filters"]:
        problems.append(f"{rel} rubric lists no filter; every answer has at least a period")
    reads_gold = set(re.findall(r"\{gold\}\.(\w+)", case["expected_sql"]))
    reads_silver = set(re.findall(r"\{silver\}\.(\w+)", case["check_sql"]))
    if metric and metric.meta["model"] not in reads_gold:
        problems.append(f"{rel} expected_sql does not read {metric.meta['model']}, the model behind {rubric['metric']}")
    if "{silver}" in case["expected_sql"]:
        problems.append(f"{rel} expected_sql reads silver; the answer must come from gold")
    if "{gold}" in case["check_sql"] or not reads_silver:
        problems.append(f"{rel} check_sql must recompute the answer from silver only")
    for name, layer in [(n, "gold") for n in sorted(reads_gold)] + [(n, "silver") for n in sorted(reads_silver)]:
        if models_.get(name, {}).get("schema") != layer:
            problems.append(f"{rel} reads {{{layer}}}.{name}, which is not a {layer} model")
    return problems


def offline_checks(names, models_):
    answer_shape, refusal_shape = yaml.safe_load_all(CASE_TEMPLATE.read_text(encoding="utf-8"))
    every = {n: load_area(n) for n in area_names()}
    terms = known_terms(every.values())
    problems, cases, seen = [], [], {}
    for area in names:
        covered = {name: 0 for name in every[area].metrics}
        refusals = 0
        for cid, (path, case) in load_cases(area).items():
            rel = path.relative_to(ROOT).as_posix()
            if cid in seen:
                problems.append(f"{rel} reuses id {cid} from {seen[cid]}")
            seen[cid] = rel
            shape = refusal_shape if isinstance(case, dict) and case.get("expect_refusal") else answer_shape
            found = case_problems(rel, case or {}, shape, area, every[area], models_, terms)
            problems += found
            cases.append(case)
            if found:
                continue
            if case.get("expect_refusal"):
                refusals += 1
            elif case["rubric"]["metric"] in covered:
                covered[case["rubric"]["metric"]] += 1
        for name, count in sorted(covered.items()):
            if count < MIN_CASES_PER_METRIC:
                problems.append(f"kb/{area}/metrics/{name}.md has {count} golden cases, it needs {MIN_CASES_PER_METRIC}")
        if not refusals:
            problems.append(f"evals/golden/{area} has no case the agent must refuse")
    return cases, problems


def matches(answer, check, tolerance=0.005):
    if answer is None or check is None:
        return False
    if isinstance(answer, str) or isinstance(check, str):
        return answer == check
    return abs(float(answer) - float(check)) <= tolerance * max(1.0, abs(float(check)))


def live_checks(cases, project, gold, silver):
    from google.cloud import bigquery

    client = bigquery.Client(project=project)

    def scalar(sql):
        rows = list(client.query(sql.format(gold=gold, silver=silver)).result())
        return rows[0][0] if rows else None

    results = []
    for c in cases:
        if c.get("expect_refusal"):
            continue
        answer, check = scalar(c["expected_sql"]), scalar(c["check_sql"])
        results.append({"id": c["id"], "answer": str(answer), "check": str(check), "pass": matches(answer, check)})
    return results


def main(argv=None):
    ap = argparse.ArgumentParser(description="Eval round: golden cases offline, and against BigQuery with --live.")
    ap.add_argument("--plan", help="plan.json from tools/detect.py; without it every area runs")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--target", default="dev", choices=["dev", "prod"])
    ap.add_argument("--manifest", default=str(MANIFEST))
    args = ap.parse_args(argv)
    names = json.loads(Path(args.plan).read_text(encoding="utf-8"))["eval_areas"] if args.plan else area_names()

    cases, problems = offline_checks(names, models(args.manifest))
    for p in problems:
        print(f"  - {p}")
    refusals = sum(1 for c in cases if isinstance(c, dict) and c.get("expect_refusal"))
    metrics = sum(len(load_area(n).metrics) for n in names)
    print(f"eval offline: {len(cases)} cases ({len(cases) - refusals} answerable, {refusals} refusals) over {metrics} metrics in {', '.join(names)}; {len(problems)} problems")
    if problems or not args.live:
        return 1 if problems else 0

    prefix = "" if args.target == "prod" else os.environ.get("DBT_DEV_DATASET", "dbt_dev") + "_"
    results = live_checks(cases, os.environ.get("GCP_PROJECT_ID"), f"{prefix}gold", f"{prefix}silver")
    stamp = datetime.now(timezone.utc)
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / f"{stamp:%Y-%m-%d}.json").write_text(
        json.dumps({"_meta": {"as_of": stamp.isoformat(), "target": args.target, "areas": names}, "results": results}, indent=2), encoding="utf-8"
    )
    failed = [r for r in results if not r["pass"]]
    for r in failed:
        print(f"  - {r['id']}: gold answers {r['answer']}, silver recomputes {r['check']}")
    print(f"eval live: {len(results) - len(failed)}/{len(results)} cases match an independent recompute from silver on {args.target}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
