import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "agent" / "golden" / "cases.yml"
MANIFEST = ROOT / "dbt" / "target" / "manifest.json"
sys.path.insert(0, str(ROOT / "tools"))
from kb import area_names, load_area


def gold_contracts(manifest_path):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    return {
        n["name"]: set(n["columns"])
        for n in manifest["nodes"].values()
        if n["resource_type"] == "model" and "gold" in n["fqn"]
    }


def offline_checks(contracts):
    metrics = {name: {**m.meta, "name": name} for a in area_names() for name, m in load_area(a).metrics.items()}
    cases = yaml.safe_load(CASES.read_text(encoding="utf-8"))["cases"]
    problems = []
    for m in metrics.values():
        if m["model"] not in contracts:
            problems.append(f"KB metric {m['name']} points at {m['model']}, which is not a gold model")
            continue
        documented = contracts[m["model"]]
        missing = [c for c in m["columns"] if documented and c not in documented]
        if missing:
            problems.append(f"KB metric {m['name']} uses {missing}, not in the {m['model']} contract")
    for c in cases:
        if c["metric"] not in metrics:
            problems.append(f"case {c['id']} asks about {c['metric']}, which the KB does not define")
        for model in re.findall(r"\{gold\}\.(\w+)", c["gold_sql"]):
            if model not in contracts:
                problems.append(f"case {c['id']} reads {model}, which is not a gold model")
    uncovered = sorted(set(metrics) - {c["metric"] for c in cases})
    if uncovered:
        problems.append(f"KB metrics without a golden case: {uncovered}")
    return metrics, cases, problems


def live_checks(cases, project, gold, silver, tolerance=0.005):
    from google.cloud import bigquery

    client = bigquery.Client(project=project)
    results = []
    for c in cases:
        def scalar(sql):
            rows = list(client.query(sql.format(gold=gold, silver=silver)).result())
            return rows[0][0] if rows else None

        gold_value, check_value = scalar(c["gold_sql"]), scalar(c["check_sql"])
        if isinstance(gold_value, str) or isinstance(check_value, str):
            ok = gold_value == check_value
        else:
            ok = gold_value is not None and check_value is not None and abs(float(gold_value) - float(check_value)) <= tolerance * max(1.0, abs(float(check_value)))
        results.append({"id": c["id"], "gold": str(gold_value), "check": str(check_value), "pass": ok})
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--target", default="dev", choices=["dev", "prod"])
    ap.add_argument("--manifest", default=str(MANIFEST))
    args = ap.parse_args()

    metrics, cases, problems = offline_checks(gold_contracts(args.manifest))
    print(f"{len(metrics)} KB metrics, {len(cases)} golden cases, {len(problems)} problems")
    for p in problems:
        print(f"  - {p}")
    if problems:
        sys.exit(1)
    if not args.live:
        return

    prefix = "" if args.target == "prod" else os.environ.get("SAOLA_DEV_DATASET", "dbt_dev") + "_"
    results = live_checks(cases, os.environ.get("SAOLA_GCP_PROJECT"), f"{prefix}gold", f"{prefix}silver")
    stamp = datetime.now(timezone.utc)
    out = ROOT / "agent" / "golden" / "results"
    out.mkdir(exist_ok=True)
    (out / f"{stamp:%Y-%m-%d}.json").write_text(json.dumps({"_meta": {"as_of": stamp.isoformat(), "target": args.target}, "results": results}, indent=2))
    failed = [r for r in results if not r["pass"]]
    print(f"{len(results) - len(failed)}/{len(results)} golden cases match an independent recompute")
    for r in failed:
        print(f"  - {r['id']}: gold {r['gold']} vs check {r['check']}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
