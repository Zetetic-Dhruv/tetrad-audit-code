#!/usr/bin/env python3
"""
Schema validator for the Discovery Tetrad audit dataset.

Walks all per-goal JSON output paths and validates each against
output_schema.json (JSON Schema Draft 7). Also enforces:

  - filename stem matches goal.id (when goal.id is present)
  - goal.id matches the locked regex from the schema
  - cell labels match the locked assembly_mapping for the relevant layer
  - witness-layer cascade rule: when Pl, Coh, or Comp fail, Inv must be
    {fired: false, verdict: null, fired_false_reason: cascade_blocked}
  - escalation reason is recorded whenever a verdict is escalate

Outputs to ./validation_output/:
  - report.md     — human-readable per-substrate validation report
  - report.csv    — long-form CSV with one row per file × check
  - failures.txt  — list of files that fail any check (for triage)

Exit code 0 if every file passes every check; 1 otherwise.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("FATAL: jsonschema not installed. `pip install jsonschema`", file=sys.stderr)
    sys.exit(2)

GATES = ["plausibility", "coherence", "completeness", "invariance"]

WITNESS_CELL_LABELS = {
    1: "total_failure", 2: "sophism", 3: "hallucination", 4: "counterfactual",
    5: "exploration_episode", 6: "fallacy", 7: "open_step",
    8: "merely_true", 9: "established_result",
}

GOAL_CELL_LABELS = {
    "1A": "pseudo_problem", "1B": "private_theory",
    "2A": "zombie_theorem", "2B": "bold_conjecture",
    "3A": "idle_speculation", "3B": "productive_speculation",
    "4A": "closed_refutation", "4B": "boundary_result",
    "5A": "proto_hypothesis", "5B": "frontier_direction",
    "6A": "orphan_result", "6B": "novel_discovery",
    "7A": "minor_open_question", "7B": "research_programme",
    "8": "supporting_argument", "9": "fundamental_result",
}

SUBSTRATES = ["flt", "slt", "fp", "asv1", "asv2"]


def find_outputs(root: Path) -> dict[str, list[Path]]:
    out: dict[str, list[Path]] = {s: [] for s in SUBSTRATES}
    for sub in ("flt", "slt", "asv1"):
        d = root / sub / "outputs"
        if d.is_dir():
            out[sub] = sorted(p for p in d.glob("*.json"))
    asv2 = root / "asv2" / "outputs"
    if asv2.is_dir():
        out["asv2"] = sorted(asv2.rglob("*.json"))
    fp = root / "human_audit" / "gpt_judge_fp"
    if fp.is_dir():
        out["fp"] = sorted(p for p in fp.glob("*.json"))
    return out


def check_filename_id(path: Path, record: dict) -> list[str]:
    issues = []
    gid = record.get("goal", {}).get("id")
    if not gid:
        issues.append("missing goal.id")
        return issues
    if path.stem != gid:
        issues.append(f"filename stem '{path.stem}' != goal.id '{gid}'")
    return issues


def check_cell_label(outcome: dict, layer: str) -> list[str]:
    issues = []
    cell = outcome.get("cell")
    name = outcome.get("cell_name")
    if cell is None or name is None:
        return ["outcome missing cell or cell_name"]
    if layer == "witness":
        try:
            expected = WITNESS_CELL_LABELS.get(int(cell))
        except (TypeError, ValueError):
            expected = None
    else:
        key = str(cell)
        expected = GOAL_CELL_LABELS.get(key)
    if expected is None:
        issues.append(f"unknown cell '{cell}' for {layer} layer")
    elif name != expected:
        issues.append(
            f"cell {cell} expects label '{expected}', got '{name}' ({layer} layer)"
        )
    return issues


def check_cascade(witness: dict) -> list[str]:
    issues = []
    te = witness.get("tetrad_evaluation", {}) or {}
    pl = te.get("plausibility", {})
    coh = te.get("coherence", {})
    comp = te.get("completeness", {})
    inv = te.get("invariance", {})

    pl_ok = pl.get("fired") is True and pl.get("verdict") == "pass"
    coh_ok = coh.get("fired") is True and coh.get("verdict") == "pass"
    comp_ok = comp.get("fired") is True and comp.get("verdict") == "pass"
    expects_fire = pl_ok and coh_ok and comp_ok

    if expects_fire:
        if inv.get("fired") is not True:
            issues.append("witness Inv should fire (Pl/Coh/Comp all pass) but did not")
    else:
        if inv.get("fired") is True:
            issues.append("witness Inv should be cascade-blocked but fired")
        elif inv.get("verdict") is not None:
            issues.append("witness Inv blocked but verdict is not null")
        elif inv.get("fired_false_reason") not in ("cascade_blocked", None):
            issues.append(
                f"witness Inv reason '{inv.get('fired_false_reason')}' "
                "should be 'cascade_blocked'"
            )
    return issues


def check_escalation_reasons(record: dict, prefix: str) -> list[str]:
    issues = []
    te = record.get("tetrad_evaluation", {}) or {}
    for g in GATES:
        ge = te.get(g, {}) or {}
        if ge.get("verdict") == "escalate" and not ge.get("escalation_reason"):
            issues.append(f"{prefix}.{g} verdict=escalate but no escalation_reason")
    return issues


def validate_one(path: Path, schema: dict, validator: jsonschema.Draft7Validator
                 ) -> tuple[list[str], list[str]]:
    """Return (failures, warnings)."""
    failures: list[str] = []
    warnings: list[str] = []
    try:
        record = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return [f"JSON parse error: {e}"], warnings

    # Schema validation
    schema_errors = list(validator.iter_errors(record))
    for err in schema_errors:
        failures.append(f"schema: {err.message[:200]}")

    # Filename / id
    failures.extend(check_filename_id(path, record))

    # Goal-layer cell label
    failures.extend(check_cell_label(record.get("outcome", {}), "goal"))

    # Goal-layer escalation reasons
    failures.extend(check_escalation_reasons(record, "goal"))

    # Witnesses: cascade + cell label + escalation reasons
    for w in record.get("witnesses") or []:
        failures.extend(check_cell_label(w.get("outcome", {}), "witness"))
        failures.extend(check_cascade(w))
        failures.extend(check_escalation_reasons(w, "witness"))
        for s in (w.get("steps") or []):
            failures.extend(check_cell_label(s.get("outcome", {}), "witness"))
            failures.extend(check_escalation_reasons(s, "step"))

    return failures, warnings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".",
                    help="empirical_analysis root (default: .)")
    ap.add_argument("--schema", default="output_schema.json",
                    help="path to output_schema.json relative to root")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    schema_path = root / args.schema
    schema = json.loads(schema_path.read_text())
    validator = jsonschema.Draft7Validator(schema)

    files_by_sub = find_outputs(root)
    out_dir = root / "validation_output"
    out_dir.mkdir(exist_ok=True)

    rows = []
    failed_files: list[str] = []
    md = ["# Schema Validation Report", "",
          f"Schema: `{schema_path.relative_to(root)}`", ""]

    for sub in SUBSTRATES:
        files = files_by_sub.get(sub, [])
        n_pass = 0
        n_fail = 0
        sub_lines = []
        for path in files:
            failures, _ = validate_one(path, schema, validator)
            rel = str(path.relative_to(root))
            if failures:
                n_fail += 1
                failed_files.append(rel)
                sub_lines.append(f"- **{rel}**")
                for f in failures:
                    sub_lines.append(f"  - {f}")
                rows.append({"substrate": sub, "file": rel, "status": "FAIL",
                             "issues": " | ".join(failures)})
            else:
                n_pass += 1
                rows.append({"substrate": sub, "file": rel, "status": "PASS",
                             "issues": ""})
        md.append(f"## {sub.upper()}")
        md.append(f"Pass: **{n_pass}** / Fail: **{n_fail}** / Total: {len(files)}")
        if sub_lines:
            md.append("")
            md.extend(sub_lines)
        md.append("")

    (out_dir / "report.md").write_text("\n".join(md))
    with (out_dir / "report.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["substrate", "file", "status", "issues"])
        w.writeheader()
        w.writerows(rows)
    (out_dir / "failures.txt").write_text("\n".join(failed_files))

    total = len(rows)
    failed = len(failed_files)
    print(f"Validated {total} files. Failures: {failed}")
    print(f"  report: {(out_dir / 'report.md').relative_to(root)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
