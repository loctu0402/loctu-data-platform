import argparse
import json
import sys
from pathlib import Path

from kb import MANIFEST, area_names, load_area, models, table_rows


def ground_problems(areas, models_):
    problems, columns, metrics, tables = [], set(), 0, 0
    for area in areas:
        for m in area.metrics.values():
            metrics += 1
            name = m.meta.get("model")
            contract = models_.get(name)
            if not contract or contract["schema"] != "gold":
                problems.append(f"{m.rel} reads {name}, which is not a gold model in the dbt manifest")
                continue
            missing = [c for c in m.meta.get("columns") or [] if c not in contract["columns"]]
            if missing:
                problems.append(f"{m.rel} reads {missing}, not in the {name} contract")
            columns |= {(name, c) for c in m.meta.get("columns") or []}
        for t in area.tables.values():
            tables += 1
            contract = models_.get(t.name)
            if not contract:
                problems.append(f"{t.rel} documents {t.name}, which is not in the dbt manifest")
                continue
            documented = {row[0]: row[1].lower() for row in table_rows(t.section("Columns")) if len(row) > 1}
            for column, data_type in contract["columns"].items():
                if column not in documented:
                    problems.append(f"{t.rel} leaves out contract column {column}")
                elif documented[column] != data_type:
                    problems.append(f"{t.rel} documents {column} as {documented[column]}, the contract says {data_type}")
            for column in sorted(set(documented) - set(contract["columns"])):
                problems.append(f"{t.rel} documents {column}, which is not in the {t.name} contract")
    return problems, metrics, len(columns), tables


def main(argv=None):
    ap = argparse.ArgumentParser(description="Ground round: every KB metric and table atom maps to dbt contract columns.")
    ap.add_argument("--plan", help="plan.json from tools/detect.py; without it every area is grounded")
    ap.add_argument("--manifest", default=str(MANIFEST))
    args = ap.parse_args(argv)
    names = json.loads(Path(args.plan).read_text(encoding="utf-8"))["kb_areas"] if args.plan else area_names()
    problems, metrics, columns, tables = ground_problems([load_area(n) for n in names], models(args.manifest))
    for p in problems:
        print(f"  - {p}")
    print(f"ground: {metrics} metrics read {columns} contract columns, {tables} table atoms checked against their contracts; {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
