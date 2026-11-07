import argparse
import json
import re
import sys
from pathlib import Path

from kb import KB, MANIFEST, PLACEHOLDER, TEMPLATES, area_names, codeowners, column_refs, load_area, models, read_atom, table_rows

TYPES = {"additive", "snapshot", "ratio"}
LINK = re.compile(r"\]\(([^)\s#]+)(?:#[^)]*)?\)")
CODE = re.compile(r"```.*?```|`[^`\n]*`", re.S)


def contract_problems(models_, areas):
    gold = {n: m for n, m in models_.items() if m["schema"] == "gold"}
    documented = {t: a.name for a in areas for t in a.tables}
    problems = []
    for name, m in sorted(gold.items()):
        if not m["enforced"]:
            problems.append(f"gold model {name} does not enforce its contract")
        untyped = sorted(c for c, t in m["columns"].items() if not t)
        if untyped:
            problems.append(f"gold model {name} has columns without a data_type: {untyped}")
        if name not in documented:
            problems.append(f"gold model {name} has no table atom under kb/")
    for name, area in sorted(documented.items()):
        if name not in gold:
            problems.append(f"kb/{area}/tables/{name}.md documents {name}, which is not a gold model")
    return problems


def shape_problems(atom, kind, area, key):
    template = read_atom(TEMPLATES / f"{kind}.md")
    problems = []
    missing, extra = sorted(set(template.meta) - set(atom.meta)), sorted(set(atom.meta) - set(template.meta))
    if missing or extra:
        problems.append(f"{atom.rel} frontmatter differs from kb/_template/{kind}.md: missing {missing}, extra {extra}")
    if atom.sections() != template.sections():
        problems.append(f"{atom.rel} has sections {atom.sections()}, kb/_template/{kind}.md has {template.sections()}")
    empty = [s for s in template.sections() if s in atom.sections() and not atom.section(s)]
    if empty:
        problems.append(f"{atom.rel} leaves sections empty: {empty}")
    if atom.meta.get("area") != area:
        problems.append(f"{atom.rel} says area {atom.meta.get('area')}, but it lives in kb/{area}")
    if key and atom.meta.get(key) != atom.name:
        problems.append(f"{atom.rel} names itself {atom.meta.get(key)}, but the file is {atom.name}.md")
    found = PLACEHOLDER.search(CODE.sub("", atom.body) + " ".join(str(v) for v in atom.meta.values()))
    if found:
        problems.append(f"{atom.rel} still holds a template placeholder: {found.group()}")
    return problems


def metric_problems(area):
    problems = []
    for m in area.metrics.values():
        kind, denominator = m.meta.get("type"), m.meta.get("denominator")
        if kind not in TYPES:
            problems.append(f"{m.rel} has type {kind}, not one of {sorted(TYPES)}")
        if (kind == "ratio") != (denominator is not None):
            problems.append(f"{m.rel} must have a denominator if and only if its type is ratio")
        if m.meta.get("model") not in area.tables:
            problems.append(f"{m.rel} reads {m.meta.get('model')}, which has no table atom in kb/{area.name}/tables")
        columns = set(m.meta.get("columns") or [])
        used = column_refs(m.meta.get("numerator")) | column_refs(denominator)
        for predicate in m.meta.get("filters") or []:
            used |= column_refs(predicate)
        if used - columns:
            problems.append(f"{m.rel} formula reads {sorted(used - columns)}, which its columns list leaves out")
        listed = {row[0] for row in table_rows(m.section("Source contract"))}
        if listed != columns:
            problems.append(f"{m.rel} Source contract lists {sorted(listed)}, the frontmatter lists {sorted(columns)}")
    return problems


def link_problems(atom):
    problems = []
    for target in LINK.findall(CODE.sub("", atom.body)):
        if "://" not in target and not (atom.path.parent / target).exists():
            problems.append(f"{atom.rel} links to {target}, which does not exist")
    return problems


def area_problems(area, owner_rules):
    if not area.index or not area.changelog:
        return [f"kb/{area.name} needs index.md and changelog.md, copied from kb/_template"]
    problems = shape_problems(area.index, "index", area.name, None)
    for kind, atoms in (("metric", area.metrics), ("table", area.tables), ("gotcha", area.gotchas)):
        for atom in atoms.values():
            problems += shape_problems(atom, kind, area.name, kind)
    if not area.metrics or not area.tables:
        problems.append(f"kb/{area.name} needs at least one metric atom and one table atom")
    problems += metric_problems(area)
    for g in area.gotchas.values():
        unknown = sorted(set(g.meta.get("applies_to") or []) - set(area.metrics) - set(area.tables))
        if unknown:
            problems.append(f"{g.rel} applies to {unknown}, which kb/{area.name} does not define")
    entries = re.split(r"^## ", area.changelog.body, flags=re.M)[1:]
    if not entries:
        problems.append(f"{area.changelog.rel} has no entry")
    for entry in entries:
        if "**Type:**" not in entry or "**Affects:**" not in entry:
            problems.append(f"{area.changelog.rel} entry '{entry.splitlines()[0]}' misses its Type or Affects line")
    for atom in area.atoms():
        problems += link_problems(atom)
    linked = {(area.index.path.parent / t).resolve() for t in LINK.findall(area.index.body)}
    for atom in area.atoms()[1:]:
        if atom.path.resolve() not in linked:
            problems.append(f"{atom.rel} is not linked from {area.index.rel}")
    lines = [owners for pattern, owners in owner_rules if pattern == f"/kb/{area.name}/"]
    if not lines:
        problems.append(f".github/CODEOWNERS has no line for /kb/{area.name}/")
    elif sorted(area.index.meta.get("owners") or []) != sorted(lines[-1]):
        problems.append(f"{area.index.rel} names owners {area.index.meta.get('owners')}, CODEOWNERS names {lines[-1]}")
    return problems


def term_problems(areas):
    seen, problems = {}, []
    for area in areas:
        for m in area.metrics.values():
            terms = {m.name, str(m.meta.get("label")), *map(str, m.meta.get("synonyms") or [])}
            for term in sorted({t.lower().replace("_", " ") for t in terms}):
                owner = f"{area.name}/{m.name}"
                if seen.setdefault(term, owner) != owner:
                    problems.append(f"'{term}' names both {seen[term]} and {owner}, so a question cannot route to one metric")
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description="Gate round: dbt contracts, KB template conformance and definition of done.")
    ap.add_argument("--plan", help="plan.json from tools/detect.py; without it every check runs")
    ap.add_argument("--manifest", default=str(MANIFEST))
    args = ap.parse_args(argv)
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8")) if args.plan else None
    every = [load_area(n) for n in area_names()]
    selected = [a for a in every if not plan or a.name in plan["kb_areas"]]
    check_contracts = not plan or plan["contracts"]

    problems = contract_problems(models(args.manifest), every) if check_contracts else []
    if selected:
        rules = codeowners()
        for area in selected:
            problems += area_problems(area, rules)
        problems += term_problems(every) + link_problems(read_atom(KB / "rules.md"))

    for p in problems:
        print(f"  - {p}")
    scope = []
    if check_contracts:
        gold = sum(1 for m in models(args.manifest).values() if m["schema"] == "gold")
        scope.append(f"contracts of {gold} gold models")
    if selected:
        counts = [sum(len(getattr(a, k)) for a in selected) for k in ("metrics", "tables", "gotchas")]
        scope.append(f"KB {', '.join(a.name for a in selected)} with {counts[0]} metrics, {counts[1]} tables and {counts[2]} gotchas")
    print(f"gate: {'; '.join(scope) or 'nothing in scope'}; {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
