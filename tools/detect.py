import argparse
import json
import os
import sys
from pathlib import Path

from kb import MANIFEST, area_names, codeowners, git_files, load_area, owners_of

ROUNDS = ["lint", "test", "gate", "ground", "eval", "simulate"]
UNIT_ROUNDS = {
    "dbt": {"lint", "gate"},
    "kb": {"gate"},
    "golden": {"lint"},
    "evals": {"lint"},
    "airflow": {"lint"},
    "report": {"lint", "test"},
    "semantic": {"lint"},
    "ingestion": {"lint"},
    "deploy": {"lint", "simulate"},
    "tests": {"test"},
    "ci": set(ROUNDS),
    "docs": set(),
}
PATHS = [
    ("dbt/", "dbt"),
    ("kb/", "kb"),
    ("evals/", "evals"),
    ("airflow/", "airflow"),
    ("report/", "report"),
    ("semantic/", "semantic"),
    ("ingestion/", "ingestion"),
    (".github/workflows/deploy.yml", "deploy"),
    ("deploy/", "deploy"),
    ("tests/", "tests"),
    ("tools/", "ci"),
    (".github/", "ci"),
    ("Makefile", "ci"),
    ("requirements.txt", "ci"),
    (".sqlfluff", "ci"),
]


def unit_of(path):
    parts = path.split("/")
    if parts[0] == "kb" and len(parts) > 2 and not parts[1].startswith("_"):
        return f"kb:{parts[1]}"
    if parts[:2] == ["evals", "golden"] and len(parts) > 3:
        return f"golden:{parts[2]}"
    return next((unit for prefix, unit in PATHS if path == prefix or (prefix.endswith("/") and path.startswith(prefix))), "docs")


def dbt_impact(paths, manifest):
    nodes = {**manifest["nodes"], **manifest["sources"]}

    def files_of(node):
        return {node.get("original_file_path", "").replace("\\", "/"), (node.get("patch_path") or "").split("://")[-1].replace("\\", "/")}

    start = set()
    for path in paths:
        hits = {uid for uid, node in nodes.items() if path.removeprefix("dbt/") in files_of(node)}
        if not hits:
            return None
        start |= hits
    reached, todo = set(start), list(start)
    while todo:
        for child in manifest["child_map"].get(todo.pop(), []):
            if child not in reached:
                reached.add(child)
                todo.append(child)

    def models(uids):
        return sorted(manifest["nodes"][u]["name"] for u in uids if u.startswith("model."))

    exposures = sorted(manifest["exposures"][u]["name"] for u in reached if u.startswith("exposure."))
    return models(start), models(reached), exposures


def plan(paths, manifest=None):
    files = {p: unit_of(p) for p in sorted(paths)}
    units = sorted(set(files.values()))
    areas = area_names()
    every = "ci" in units
    kb_areas = set(areas) if every or "kb" in units else {u.split(":")[1] for u in units if u.startswith("kb:")}
    eval_areas = set(areas) if every or "evals" in units else {u.split(":")[1] for u in units if u.startswith("golden:")}
    dbt, dbt_areas = None, set()
    if "dbt" in units:
        impact = dbt_impact([p for p, u in files.items() if u == "dbt"], manifest) if manifest else None
        if impact is None:
            dbt, dbt_areas = {"all": True, "changed": [], "reached": [], "exposures": []}, set(areas)
        else:
            changed, reached, exposures = impact
            model_area = {t: a for a in areas for t in load_area(a).tables}
            dbt = {"all": False, "changed": changed, "reached": reached, "exposures": exposures}
            dbt_areas = {model_area[m] for m in reached if m in model_area}
    kb_areas |= dbt_areas
    eval_areas |= kb_areas

    rounds = {r: {u for u in units if r in UNIT_ROUNDS[u.split(":")[0]]} for r in ROUNDS}
    area_units = {u for u in units if u.split(":")[0] in ("kb", "ci") or (u == "dbt" and dbt_areas)}
    golden_units = {u for u in units if u.split(":")[0] in ("golden", "evals")}
    rounds["gate"] |= area_units
    rounds["ground"] = rounds["ground"] | area_units if kb_areas else set()
    rounds["eval"] = rounds["eval"] | area_units | golden_units if eval_areas else set()

    rules = codeowners()
    owners = {}
    for path, unit in files.items():
        owners.setdefault(unit, set()).update(owners_of(path, rules))
    return {
        "files": files,
        "units": units,
        "dbt": dbt,
        "contracts": every or "dbt" in units,
        "kb_areas": sorted(kb_areas),
        "eval_areas": sorted(eval_areas),
        "lint_files": git_files("ls-files") if every else sorted(files),
        "rounds": {r: sorted(rounds[r]) for r in ROUNDS},
        "owners": {u: sorted(o) for u, o in sorted(owners.items())},
    }


def render(p):
    lines = [f"{len(p['files'])} changed files in {len(p['units'])} units: {', '.join(p['units']) or 'none'}"]
    if len(p["files"]) <= 40:
        lines += [f"  {unit:<20} {path}" for path, unit in p["files"].items()]
    if p["dbt"]:
        d = p["dbt"]
        lines.append("dbt: a project-wide file changed or dbt did not parse, so every model counts as reached" if d["all"]
                     else f"dbt: changed {', '.join(d['changed']) or 'no model'}; reaches {', '.join(d['reached']) or 'no model'}; "
                          f"exposures {', '.join(d['exposures']) or 'none'}")
    lines.append(f"KB areas for gate and ground: {', '.join(p['kb_areas']) or 'none'}. Golden areas for eval: {', '.join(p['eval_areas']) or 'none'}.")
    lines += [f"  {r:<9} {'runs' if p['rounds'][r] else 'skips':<6} {', '.join(p['rounds'][r])}" for r in ROUNDS]
    lines += [f"  approve  {unit:<20} {' '.join(owners) or 'no code owner'}" for unit, owners in p["owners"].items()]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Map changed files to units and decide which CI rounds run.")
    ap.add_argument("--base", default="", help="base commit; empty or all zeros means every tracked file counts as changed")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--files", nargs="*", help="changed paths to route instead of a git diff")
    ap.add_argument("--manifest", default=str(MANIFEST))
    ap.add_argument("--out", help="write the plan as JSON for the round jobs")
    ap.add_argument("--github-output", action="store_true", help="write one true or false step output per round")
    args = ap.parse_args(argv)
    if args.files is not None:
        paths = args.files
    elif not args.base.strip("0"):
        paths = git_files("ls-files")
    else:
        paths = git_files("diff", "--name-only", f"{args.base}...{args.head}")
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8")) if Path(args.manifest).exists() else None
    p = {"base": args.base, "head": args.head, **plan(paths, manifest)}
    print(render(p))
    if args.out:
        Path(args.out).write_text(json.dumps(p, indent=2), encoding="utf-8")
    if args.github_output:
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
            fh.writelines(f"{r}={'true' if p['rounds'][r] else 'false'}\n" for r in ROUNDS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
