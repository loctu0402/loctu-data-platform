import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "kb"
TEMPLATES = KB / "_template"
GOLDEN = ROOT / "evals" / "golden"
CASE_TEMPLATE = ROOT / "evals" / "template_case.yaml"
MANIFEST = ROOT / "dbt" / "target" / "manifest.json"
CODEOWNERS = ROOT / ".github" / "CODEOWNERS"
PLACEHOLDER = re.compile(r"<[A-Za-z][^<>\n]*>")
SQL_WORDS = {"and", "or", "not", "in", "is", "null", "true", "false", "between", "like", "case", "when", "then", "else", "end", "distinct"}


@dataclass
class Atom:
    path: Path
    meta: dict
    body: str

    @property
    def name(self):
        return self.path.stem

    @property
    def rel(self):
        return self.path.relative_to(ROOT).as_posix()

    def sections(self):
        return re.findall(r"^## (.+?)\s*$", self.body, re.M)

    def section(self, title):
        m = re.search(rf"^## {re.escape(title)}\s*$(.*?)(?=^## |\Z)", self.body, re.M | re.S)
        return m.group(1).strip() if m else ""


@dataclass
class Area:
    name: str
    index: Atom | None
    changelog: Atom | None
    metrics: dict
    tables: dict
    gotchas: dict

    def atoms(self):
        return [a for a in (self.index, self.changelog) if a] + [*self.metrics.values(), *self.tables.values(), *self.gotchas.values()]


def read_atom(path):
    path = Path(path)
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)\Z", text, re.S)
    return Atom(path, yaml.safe_load(m.group(1)) or {}, m.group(2)) if m else Atom(path, {}, text)


def area_names(kb=KB):
    return sorted(p.name for p in kb.iterdir() if p.is_dir() and not p.name.startswith("_"))


def load_area(name, kb=KB):
    root = kb / name

    def folder(sub):
        return {p.stem: read_atom(p) for p in sorted((root / sub).glob("*.md"))}

    return Area(name, read_atom(root / "index.md"), read_atom(root / "changelog.md"), folder("metrics"), folder("tables"), folder("gotchas"))


def table_rows(text):
    lines = [line.strip() for line in text.splitlines() if line.strip().startswith("|")]
    return [[cell.strip().strip("`") for cell in line.strip("|").split("|")] for line in lines[2:]]


def column_refs(expr):
    text = re.sub(r"'[^']*'", "", str(expr or ""))
    return {w for w in re.findall(r"\b([a-z_][a-z0-9_]*)\b(?!\s*\()", text) if w not in SQL_WORDS}


def models(manifest=MANIFEST):
    nodes = json.loads(Path(manifest).read_text(encoding="utf-8"))["nodes"].values()
    return {
        n["name"]: {
            "schema": n["config"].get("schema"),
            "enforced": n["config"].get("contract", {}).get("enforced", False),
            "columns": {c: (v.get("data_type") or "").lower() for c, v in n["columns"].items()},
        }
        for n in nodes
        if n["resource_type"] == "model"
    }


def codeowners(path=CODEOWNERS):
    rules = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            pattern, *owners = line.split()
            rules.append((pattern, owners))
    return rules


def owners_of(path, rules):
    found = []
    for pattern, owners in rules:
        if pattern == "*" or f"/{path}".startswith(pattern):
            found = owners
    return found


def git_files(*args):
    out = subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True)
    return [line for line in out.stdout.splitlines() if line]


def load_cases(area, golden=GOLDEN):
    return {p.stem: (p, yaml.safe_load(p.read_text(encoding="utf-8"))) for p in sorted((golden / area).glob("*.yaml"))}
