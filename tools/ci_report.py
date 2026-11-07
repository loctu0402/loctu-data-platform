import argparse
import json
import sys
from pathlib import Path

ROUNDS = ["lint", "test", "gate", "ground", "eval", "simulate"]
RESULTS = {"success": "passed", "failure": "failed", "cancelled": "cancelled", "skipped": "skipped"}
APPROVAL = "A merge needs an approving review from a code owner of each unit, and the deploy job waits for a reviewer on the production environment."


def read_log(text):
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    problems = [line.strip()[2:] for line in lines if line.startswith("  - ")]
    rest = [line for line in lines if not line.startswith("  - ")]
    return (rest[-1] if rest else "see the job log"), problems


def cell(text):
    return text.replace("|", "\\|")


def render(plan, needs, logs):
    if plan is None:
        return "## CI report\n\nDetect did not finish, so no round ran. Open the detect job log.\n"
    lines = ["## CI report", "", f"{len(plan['files'])} changed files in {len(plan['units'])} units: {', '.join(plan['units']) or 'none'}."]
    d = plan["dbt"]
    if d and d["all"]:
        lines.append("dbt: a project-wide file changed or dbt did not parse, so every model counts as reached.")
    elif d:
        lines.append(f"dbt: changed {', '.join(d['changed']) or 'no model'}; reaches {', '.join(d['reached']) or 'no model'}; "
                     f"exposures {', '.join(d['exposures']) or 'none'}.")
    lines += ["", "| Round | Ran because | Result | Summary |", "|---|---|---|---|"]
    problems = []
    for r in ROUNDS:
        reasons, result = plan["rounds"][r], needs.get(r, {}).get("result", "skipped")
        summary, found = read_log(logs.get(r, ""))
        problems += [(r, p) for p in found]
        if not reasons:
            status, summary = "skipped", "not needed by this change"
        elif result == "skipped":
            status, summary = "not run", "an earlier round failed"
        else:
            status = RESULTS.get(result, result)
        lines.append(f"| {r} | {', '.join(reasons) or '-'} | {status} | {cell(summary)} |")
        if r == "eval" and reasons and result != "skipped":
            if "eval-live" in logs:
                summary, found = read_log(logs["eval-live"])
                problems += [("eval live", p) for p in found]
                lines.append(f"| eval live | warehouse secret | {'failed' if result == 'failure' else 'passed'} | {cell(summary)} |")
            elif result == "success":
                lines.append("| eval live | warehouse secret | skipped | no SAOLA_GCP_SA_KEY secret, so gold and silver were not compared on BigQuery |")
    if problems:
        lines += ["", "### Problems", ""] + [f"- {r}: {p}" for r, p in problems]
    lines += ["", "### Approval", "", "| Unit | Code owners |", "|---|---|"]
    lines += [f"| {unit} | {' '.join(owners) or '-'} |" for unit, owners in plan["owners"].items()]
    lines += ["", APPROVAL]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Render the CI rounds as one Markdown report.")
    ap.add_argument("--dir", default="ci", help="folder with plan.json and one <round>.log per round that ran")
    ap.add_argument("--needs", default="{}", help="the needs context of the report job, as JSON")
    args = ap.parse_args(argv)
    folder = Path(args.dir)
    plan = json.loads((folder / "plan.json").read_text(encoding="utf-8")) if (folder / "plan.json").exists() else None
    logs = {p.stem: p.read_text(encoding="utf-8") for p in folder.glob("*.log")}
    sys.stdout.write(render(plan, json.loads(args.needs), logs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
