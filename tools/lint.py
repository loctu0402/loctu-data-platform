import argparse
import json
import subprocess
import sys
from pathlib import Path

import sqlfluff
import yaml
from kb import ROOT, git_files
from sqlfluff.api import APIParsingError

SQL_DIRS = ("dbt/models/", "dbt/tests/")


def sql_problems(paths):
    if not paths:
        return []
    out = subprocess.run([sys.executable, "-m", "sqlfluff", "lint", "--format", "json", *paths], cwd=ROOT, capture_output=True, text=True)
    return [
        f"{f['filepath'].replace(chr(92), '/')}:{v['start_line_no']} {v['code']} {v['description']}"
        for f in json.loads(out.stdout or "[]")
        for v in f["violations"]
    ]


def golden_sql_problems(path, case):
    problems = []
    for key in ("expected_sql", "check_sql"):
        if isinstance(case, dict) and case.get(key):
            try:
                sqlfluff.parse(case[key].format(gold="gold", silver="silver"), dialect="bigquery")
            except (APIParsingError, KeyError, ValueError) as e:
                problems.append(f"{path} {key} is not valid BigQuery SQL: {' '.join(str(e).split())[:200]}")
    return problems


def lint(paths):
    files = sorted(p for p in paths if (ROOT / p).is_file())
    groups = {
        "SQL": [p for p in files if p.endswith(".sql") and p.startswith(SQL_DIRS)],
        "Python": [p for p in files if p.endswith(".py")],
        "shell": [p for p in files if p.endswith(".sh")],
        "YAML": [p for p in files if p.endswith((".yml", ".yaml"))],
    }
    problems = sql_problems(groups["SQL"])
    for p in groups["Python"]:
        try:
            compile((ROOT / p).read_text(encoding="utf-8"), p, "exec")
        except SyntaxError as e:
            problems.append(f"{p}:{e.lineno} {e.msg}")
    for p in groups["shell"]:
        result = subprocess.run(["bash", "-n", p], cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            problems.append(" ".join(result.stderr.split()))
    for p in groups["YAML"]:
        try:
            docs = list(yaml.safe_load_all((ROOT / p).read_text(encoding="utf-8")))
        except yaml.YAMLError as e:
            problems.append(f"{p}: {' '.join(str(e).split())}")
            continue
        if "evals/golden/" in p:
            problems += golden_sql_problems(p, docs[0] if docs else None)
    return problems, {k: len(v) for k, v in groups.items()}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Lint round: SQL, Python, shell and YAML files, each by its own tool.")
    ap.add_argument("paths", nargs="*", help="files to lint; without them every tracked or new file")
    ap.add_argument("--plan", help="plan.json from tools/detect.py; lints its lint_files")
    args = ap.parse_args(argv)
    if args.plan:
        paths = json.loads(Path(args.plan).read_text(encoding="utf-8"))["lint_files"]
    else:
        paths = args.paths or git_files("ls-files", "--cached", "--others", "--exclude-standard")
    problems, counts = lint(paths)
    for p in problems:
        print(f"  - {p}")
    print(f"lint: {sum(counts.values())} files ({', '.join(f'{n} {k}' for k, n in counts.items())}); {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
