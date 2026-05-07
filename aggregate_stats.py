#!/usr/bin/env python3
"""
Aggregate statistics harness for the Discovery Tetrad backward-audit dataset.

Reads all per-goal JSON outputs across the five substrates and the human-audit
directory, then emits per-substrate and cross-substrate aggregates suitable for
the empirical-results section of the paper and the §B appendix.

Outputs (written to ./aggregate_stats_output/):
  - summary.md          — human-readable Markdown report with all tables
  - per_substrate.csv   — substrate × metric long-form CSV
  - cell_distribution.csv  — substrate × layer × cell long-form CSV
  - sophism_records.csv — one row per sophism-flagged record (paper-level audit aid)

Usage:
    python3 aggregate_stats.py [--root <empirical_analysis path>]

The script is deterministic and side-effect-free except for writing to
./aggregate_stats_output/.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

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
    """Return substrate -> list of JSON output paths.

    fp paths come from human_audit/gpt_judge_fp/ (the 3-way comparison source).
    All other substrates read from <substrate>/outputs/.
    """
    out: dict[str, list[Path]] = {s: [] for s in SUBSTRATES}
    for sub in ("flt", "slt", "asv1"):
        d = root / sub / "outputs"
        if d.is_dir():
            out[sub] = sorted(p for p in d.glob("*.json"))
    asv2_dir = root / "asv2" / "outputs"
    if asv2_dir.is_dir():
        out["asv2"] = sorted(asv2_dir.rglob("*.json"))
    fp_dir = root / "human_audit" / "gpt_judge_fp"
    if fp_dir.is_dir():
        out["fp"] = sorted(p for p in fp_dir.glob("*.json"))
    return out


def gate_summary(record: dict, prefix_path: str = "tetrad_evaluation") -> dict:
    """Return per-gate counts for a record. prefix_path picks goal vs witness layer."""
    block = record.get(prefix_path, {})
    s = {g: {"fired": 0, "pass": 0, "fail": 0, "escalate": 0, "null": 0} for g in GATES}
    for g in GATES:
        ge = block.get(g, {})
        if ge.get("fired") is True:
            s[g]["fired"] = 1
            v = ge.get("verdict")
            if v == "pass":
                s[g]["pass"] = 1
            elif v == "fail":
                s[g]["fail"] = 1
            elif v == "escalate":
                s[g]["escalate"] = 1
        else:
            s[g]["null"] = 1
    return s


def witness_loop_summary(record: dict, key: str = "witness_loop") -> dict:
    wl = record.get(key, {})
    return {
        "iterations": wl.get("iterations"),
        "settled": wl.get("settled"),
        "halt_reason": wl.get("halt_reason"),
    }


def extract_witness_records(record: dict) -> list[dict]:
    """Return witness sub-records (with their tetrad_evaluation blocks)."""
    return record.get("witnesses") or []


def extract_step_records(record: dict) -> list[dict]:
    """Return all step sub-records across witnesses (FP only typically)."""
    out = []
    for w in record.get("witnesses") or []:
        steps = w.get("steps")
        if steps:
            out.extend(steps)
    return out


def aggregate_substrate(files: list[Path]) -> dict:
    """Aggregate a substrate's records into a flat summary dict."""
    n_goals = 0
    n_witnesses = 0
    n_steps = 0
    sophism_goal = 0
    sophism_witness = 0
    sophism_step = 0
    sophism_records: list[dict] = []
    goal_cells: Counter = Counter()
    witness_cells: Counter = Counter()
    step_cells: Counter = Counter()
    goal_gate_totals = {g: defaultdict(int) for g in GATES}
    witness_gate_totals = {g: defaultdict(int) for g in GATES}
    iter_hist: Counter = Counter()
    halt_reasons: Counter = Counter()

    for path in files:
        try:
            d = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if not isinstance(d, dict):
            continue
        n_goals += 1
        gid = d.get("goal", {}).get("id", path.stem)
        substrate = d.get("goal", {}).get("substrate", "?")

        outcome = d.get("outcome", {}) or {}
        gcell = str(outcome.get("cell", "")).strip()
        if gcell:
            goal_cells[gcell] += 1
        if outcome.get("sophism_flag") is True:
            sophism_goal += 1
            sophism_records.append({
                "substrate": substrate, "id": gid, "layer": "goal",
                "cell": gcell, "label": outcome.get("cell_name", ""),
                "interpretation": (outcome.get("interpretation") or "")[:200],
            })

        gs = gate_summary(d, "tetrad_evaluation")
        for g in GATES:
            for k, v in gs[g].items():
                goal_gate_totals[g][k] += v

        wl = witness_loop_summary(d)
        if wl["iterations"] is not None:
            iter_hist[int(wl["iterations"])] += 1
        if wl["halt_reason"]:
            halt_reasons[wl["halt_reason"]] += 1

        for wrec in extract_witness_records(d):
            n_witnesses += 1
            woutcome = wrec.get("outcome", {}) or {}
            wcell = str(woutcome.get("cell", "")).strip()
            if wcell:
                witness_cells[wcell] += 1
            if woutcome.get("sophism_flag") is True:
                sophism_witness += 1
                sophism_records.append({
                    "substrate": substrate, "id": gid, "layer": "witness",
                    "cell": wcell, "label": woutcome.get("cell_name", ""),
                    "interpretation": (woutcome.get("interpretation") or "")[:200],
                })
            ws = gate_summary(wrec, "tetrad_evaluation")
            for g in GATES:
                for k, v in ws[g].items():
                    witness_gate_totals[g][k] += v
            wwl = witness_loop_summary(wrec)
            if wwl["iterations"] is not None:
                iter_hist[int(wwl["iterations"])] += 1
            if wwl["halt_reason"]:
                halt_reasons[wwl["halt_reason"]] += 1

            for srec in (wrec.get("steps") or []):
                n_steps += 1
                soutcome = srec.get("outcome", {}) or {}
                scell = str(soutcome.get("cell", "")).strip()
                if scell:
                    step_cells[scell] += 1
                if soutcome.get("sophism_flag") is True:
                    sophism_step += 1
                    sophism_records.append({
                        "substrate": substrate, "id": gid, "layer": "step",
                        "cell": scell, "label": soutcome.get("cell_name", ""),
                        "interpretation": (soutcome.get("interpretation") or "")[:200],
                    })

    return {
        "n_goals": n_goals,
        "n_witnesses": n_witnesses,
        "n_steps": n_steps,
        "sophism_goal": sophism_goal,
        "sophism_witness": sophism_witness,
        "sophism_step": sophism_step,
        "sophism_total": sophism_goal + sophism_witness + sophism_step,
        "sophism_records": sophism_records,
        "goal_cells": dict(goal_cells),
        "witness_cells": dict(witness_cells),
        "step_cells": dict(step_cells),
        "goal_gate_totals": {g: dict(v) for g, v in goal_gate_totals.items()},
        "witness_gate_totals": {g: dict(v) for g, v in witness_gate_totals.items()},
        "witness_loop_iterations": dict(iter_hist),
        "witness_loop_halt_reasons": dict(halt_reasons),
    }


def gate_table(label: str, totals: dict, n_evals: int) -> str:
    rows = ["| Gate | Fired | Pass | Fail | Escalate | Cascade-blocked / Null |",
            "|------|------:|-----:|-----:|---------:|-----------------------:|"]
    for g in GATES:
        t = totals[g]
        rows.append(
            f"| {g.title()} | {t.get('fired', 0)} | {t.get('pass', 0)} | "
            f"{t.get('fail', 0)} | {t.get('escalate', 0)} | {t.get('null', 0)} |"
        )
    return f"### {label} gate totals (n_evals = {n_evals})\n\n" + "\n".join(rows) + "\n"


def cell_table(label: str, counts: dict, layer: str) -> str:
    if not counts:
        return f"### {label}\n\n(no records)\n\n"
    canonical = WITNESS_CELL_LABELS if layer == "witness" else GOAL_CELL_LABELS
    rows = [f"| Cell | Label | Count |", "|------|-------|------:|"]
    for cell_id, cnt in sorted(counts.items(), key=lambda kv: str(kv[0])):
        try:
            lookup_key = int(cell_id) if str(cell_id).isdigit() else str(cell_id)
        except ValueError:
            lookup_key = cell_id
        lab = canonical.get(lookup_key) or canonical.get(str(cell_id), "?")
        rows.append(f"| {cell_id} | `{lab}` | {cnt} |")
    return f"### {label}\n\n" + "\n".join(rows) + "\n"


def render_substrate_section(sub: str, agg: dict) -> str:
    lines = [f"## {sub.upper()}", ""]
    lines.append(f"- Goals audited: **{agg['n_goals']}**")
    lines.append(f"- Witness records: **{agg['n_witnesses']}**")
    lines.append(f"- Step records: **{agg['n_steps']}**")
    lines.append(f"- Sophism flags (goal+witness+step): "
                 f"**{agg['sophism_total']}** "
                 f"({agg['sophism_goal']} goal, "
                 f"{agg['sophism_witness']} witness, "
                 f"{agg['sophism_step']} step)")
    lines.append("")
    lines.append(gate_table("Goal-layer", agg["goal_gate_totals"], agg["n_goals"]))
    lines.append(gate_table("Witness-layer", agg["witness_gate_totals"],
                            agg["n_witnesses"]))
    lines.append(cell_table("Goal-layer cell distribution",
                            agg["goal_cells"], layer="goal"))
    lines.append(cell_table("Witness-layer cell distribution",
                            agg["witness_cells"], layer="witness"))
    if agg["step_cells"]:
        lines.append(cell_table("Step-layer cell distribution (FP only)",
                                agg["step_cells"], layer="witness"))
    lines.append("### Witness loop iterations\n")
    if agg["witness_loop_iterations"]:
        lines.append("| Iterations | Count |\n|-----------:|------:|")
        for it, cnt in sorted(agg["witness_loop_iterations"].items()):
            lines.append(f"| {it} | {cnt} |")
        lines.append("")
        lines.append("Halt reasons: " + ", ".join(
            f"`{k}` × {v}" for k, v in
            sorted(agg["witness_loop_halt_reasons"].items())))
    else:
        lines.append("(no records)")
    lines.append("")
    return "\n".join(lines)


def cross_substrate_summary(per_sub: dict) -> str:
    lines = ["## Cross-substrate summary",
             "",
             "| Substrate | Goals | Witnesses | Steps | Sophism flags | "
             "Sophism / goal |",
             "|-----------|------:|----------:|------:|--------------:|"
             "----------------:|"]
    for sub in SUBSTRATES:
        a = per_sub.get(sub, {})
        ng = a.get("n_goals", 0) or 0
        rate = (a.get("sophism_total", 0) / ng) if ng else 0.0
        lines.append(f"| {sub} | {ng} | {a.get('n_witnesses', 0)} | "
                     f"{a.get('n_steps', 0)} | {a.get('sophism_total', 0)} | "
                     f"{rate:.2f} |")
    lines.append("")
    return "\n".join(lines)


def write_csv_per_substrate(out_dir: Path, per_sub: dict) -> None:
    rows = []
    for sub in SUBSTRATES:
        a = per_sub.get(sub, {})
        if not a:
            continue
        rows.append({
            "substrate": sub,
            "n_goals": a.get("n_goals", 0),
            "n_witnesses": a.get("n_witnesses", 0),
            "n_steps": a.get("n_steps", 0),
            "sophism_total": a.get("sophism_total", 0),
            "sophism_per_goal": (
                (a.get("sophism_total", 0) / a["n_goals"]) if a.get("n_goals") else 0.0
            ),
        })
    path = out_dir / "per_substrate.csv"
    with path.open("w", newline="") as f:
        if not rows:
            return
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def write_csv_cell_distribution(out_dir: Path, per_sub: dict) -> None:
    rows = []
    for sub in SUBSTRATES:
        a = per_sub.get(sub, {})
        for cell, cnt in (a.get("goal_cells") or {}).items():
            rows.append({"substrate": sub, "layer": "goal",
                         "cell": cell, "count": cnt})
        for cell, cnt in (a.get("witness_cells") or {}).items():
            rows.append({"substrate": sub, "layer": "witness",
                         "cell": cell, "count": cnt})
        for cell, cnt in (a.get("step_cells") or {}).items():
            rows.append({"substrate": sub, "layer": "step",
                         "cell": cell, "count": cnt})
    path = out_dir / "cell_distribution.csv"
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["substrate", "layer", "cell", "count"])
        w.writeheader()
        w.writerows(rows)


def write_csv_sophisms(out_dir: Path, per_sub: dict) -> None:
    rows = []
    for sub in SUBSTRATES:
        a = per_sub.get(sub, {})
        for r in a.get("sophism_records") or []:
            rows.append(r)
    path = out_dir / "sophism_records.csv"
    with path.open("w", newline="") as f:
        if not rows:
            f.write("substrate,id,layer,cell,label,interpretation\n")
            return
        w = csv.DictWriter(f, fieldnames=["substrate", "id", "layer",
                                          "cell", "label", "interpretation"])
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".",
                    help="empirical_analysis root directory (default: .)")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    files_by_sub = find_outputs(root)
    per_sub = {sub: aggregate_substrate(paths) for sub, paths in files_by_sub.items()}

    out_dir = root / "aggregate_stats_output"
    out_dir.mkdir(exist_ok=True)

    md = ["# Discovery Tetrad — Aggregate Statistics", ""]
    md.append(f"Generated from {sum(len(v) for v in files_by_sub.values())} "
              f"per-goal JSON records under `{root}`.\n")
    md.append(cross_substrate_summary(per_sub))
    for sub in SUBSTRATES:
        md.append(render_substrate_section(sub, per_sub.get(sub, {})))

    summary_path = out_dir / "summary.md"
    summary_path.write_text("\n".join(md))

    write_csv_per_substrate(out_dir, per_sub)
    write_csv_cell_distribution(out_dir, per_sub)
    write_csv_sophisms(out_dir, per_sub)

    n_total = sum(a.get("n_goals", 0) for a in per_sub.values())
    print(f"Wrote {summary_path.relative_to(root)}")
    print(f"  total goal records: {n_total}")
    print(f"  per-substrate CSV: {(out_dir / 'per_substrate.csv').relative_to(root)}")
    print(f"  cell distribution: "
          f"{(out_dir / 'cell_distribution.csv').relative_to(root)}")
    print(f"  sophism records: "
          f"{(out_dir / 'sophism_records.csv').relative_to(root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
