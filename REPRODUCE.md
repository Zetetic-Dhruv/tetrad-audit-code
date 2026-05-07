# Reproducibility Guide

This document describes how to reproduce the Discovery Tetrad audit pipeline
end-to-end. Captured 2026-05-07.

---

## Prerequisites

- Python 3.10 or newer.
- The `jsonschema` package (for `validate_outputs.py`).
- API access to Anthropic's `claude-opus-4-7` model (the LLM-judge instrument).
- For the First-Proof three-way comparison only: API access to a `gpt-5.5-pro`
  endpoint and access to the human-grading worksheet for the FP problems
  (included in `human_audit/pi_grading/` for the two gold-standard exemplars).

There are no GPU requirements. The pipeline calls the LLM provider's hosted
API; it does not perform local model inference.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install jsonschema
```

## Repository layout

```
empirical_analysis/
├── judge_prompt.txt            ← frozen LLM-judge prompt (the contract)
├── orchestrator_prompt*.txt    ← per-substrate orchestrator wrappers
├── assembly_mapping.json       ← verdict-bits → cell-name proto-compiler
├── output_schema.json          ← JSON Schema (Draft 7) for output records
├── dispatch_map.json           ← (goal_source, witness) pair manifest
├── SCHEMA.md                   ← schema specification with id-generation rules
├── DATASHEET.md                ← Gebru et al. datasheet
├── ETHICS.md                   ← ethics statement
├── LICENSE                     ← Apache 2.0
├── REPRODUCE.md                ← (this file)
├── croissant_metadata.json     ← Croissant ML metadata
├── aggregate_stats.py          ← cross-substrate aggregation
├── validate_outputs.py         ← schema + cascade + label validator
│
├── flt/                        ← Formal Learning Theory substrate
│   ├── proofs/                 ← .lean files (preserved from upstream)
│   ├── premise/                ← final.json + origin.json (world model)
│   ├── outputs/                ← per-goal audit JSONs
│   ├── SUBSTRATE_README.md
│   └── VERIFICATION_STATUS.md  ← operator-internal; pre-verification record
│
├── slt/                        ← Statistical Learning Theory substrate
│   └── (same structure)
│
├── fp/                         ← First-Proof substrate
│   ├── proofs/                 ← 10 PDF proof attempts
│   ├── datasets/               ← upstream YAML / CSV / xlsx
│   └── code/discovery_loop_prompt.yaml
│
├── asv1/                       ← AI Scientist v1 substrate
│   └── papers/<paper>/         ← 10 per-paper subfolders
│
├── asv2/                       ← AI Scientist v2 substrate
│   ├── compreg/, pest_detection/, label_noise/
│   └── outputs/                ← per-paper audit JSONs
│
└── human_audit/
    ├── pi_grading/             ← human-graded gold-standard exemplars
    └── gpt_judge_fp/           ← FP audits from GPT-5.5 Pro pass
                                  (used in the inter-judge concordance appendix)
```

## Method overview

The pipeline applies the locked Discovery Tetrad rubric (four invariant gates ×
two layers × 25-cell taxonomy) to long-horizon LLM-driven research artifacts
across five substrates. The rubric is fully specified by three frozen files:

1. `judge_prompt.txt` — the contract applied verbatim to every judge call.
2. `assembly_mapping.json` — the layer-aware mapping from the 4-bit verdict
   vector to the canonical cell label.
3. `output_schema.json` — the strict JSON Schema (Draft 7) every per-goal
   audit record must satisfy.

The dispatch map (`dispatch_map.json`) lists 131 (goal_source, witness) pairs
spanning all five substrates. Each pair produces zero or more per-goal audit
records, named by the goal's deterministic id (per `SCHEMA.md` §B).

**LLM-judge instrument.** All audits use Claude Opus 4.7 (`claude-opus-4-7`) at
temperature 0 with the locked prompt. The First-Proof three-way comparison
appendix additionally uses GPT-5.5 Pro (`gpt-5.5-pro`) and human grading on the
same FP problems to measure inter-judge concordance; the GPT-judge outputs are
included under `human_audit/gpt_judge_fp/` and the authors hand-graded exemplars under
`human_audit/pi_grading/`.

**No Lean toolchain is invoked.** The two formal-mathematics substrates (FLT,
SLT) were independently pre-verified before the audit and the verification
status is recorded in `flt/VERIFICATION_STATUS.md` and
`slt/VERIFICATION_STATUS.md`. The judge prompt explicitly does not invoke
`lake build`, `lean4checker`, or any sorry/axiom search; conceptual /
structural / mathematical content is the audit target.

## Step-by-step replication

### Step 1 — verify the spec files

The frozen contract is the three files plus the orchestrator wrappers and
dispatch map. To verify they are unchanged from the released versions:

```bash
shasum -a 256 judge_prompt.txt assembly_mapping.json output_schema.json \
              dispatch_map.json SCHEMA.md
```

(See the `croissant_metadata.json` distribution block for the canonical hashes
at release; values populated at camera-ready.)

### Step 2 — confirm substrate provenance

The substrate folders contain copied (not modified) upstream artifacts. Each
substrate carries a `SUBSTRATE_README.md` documenting upstream identity and a
top-level `MANIFEST.md` listing the import inventory. To verify substrate
provenance, inspect those files; the files are checked into the public release.

### Step 3 — validate the existing audit outputs

```bash
python3 validate_outputs.py --root .
```

Expected: 282 records validated; 0 failures. Output:
`validation_output/report.md`, `validation_output/report.csv`, and
`validation_output/failures.txt` (empty on a clean run).

### Step 4 — generate cross-substrate aggregates

```bash
python3 aggregate_stats.py --root .
```

Expected output: `aggregate_stats_output/summary.md` (Markdown report),
`aggregate_stats_output/per_substrate.csv`, `cell_distribution.csv`, and
`sophism_records.csv`.

### Step 5 (optional) — re-run the LLM-judge pipeline

To re-generate audit outputs from scratch, an orchestrator must:

1. Read each pair entry from `dispatch_map.json`.
2. Read the per-pair `goal_source`, `witness`, and `supplementary_context`
   files.
3. Apply `judge_prompt.txt` (with `assembly_mapping.json` reproduced inline in
   the prompt's §6 — already there) to each goal identified per the per-pair
   `extraction_policy`.
4. Validate each emitted JSON against `output_schema.json`.
5. Write to `<substrate>/outputs/<goal.id>.json`.

A reference orchestrator is included as `orchestrator_prompt.txt` (the frozen
text the orchestrator-agent receives at dispatch time). Specific implementations
may use any LLM-API client; the only constraint is faithful execution of the
locked prompt.

### Determinism note

The pipeline is deterministic with respect to:

- the locked `judge_prompt.txt`, `assembly_mapping.json`, `output_schema.json`,
  `dispatch_map.json`,
- the model identifier `claude-opus-4-7` at temperature 0,
- the per-pair extraction policy strings.

Run-to-run variance comes from the LLM provider's inference layer (sub-token-
sampling level non-determinism even at temperature 0 in some configurations).
Schema-conformance and cell-label consistency are enforced by
`validate_outputs.py`; cell verdicts on borderline cases may differ across
runs, which is why a non-zero escalation rate is required for credibility on
long-corpus evaluations.

## Three-way concordance appendix (FP only)

The First-Proof inter-judge concordance appendix combines three independent
audits of the same 10 problems:

1. Claude Opus 4.7 judge — primary instrument across all substrates.
2. GPT-5.5 Pro judge — second-instrument cross-check on FP only; outputs in
   `human_audit/gpt_judge_fp/`.
3. Human grading — the authors hand-written gold-standard exemplars on FP Problem 2
   and FLT KL Divergence module; in `human_audit/pi_grading/`.

The agreement statistics are computed by the aggregate harness's three-way
join on FP `goal.id`. (Implementation extension; the harness emits the per-
substrate CSVs needed for the join.)

## Known limitations

- FP Problem 1 audit exists only as a Markdown summary; the structured JSON
  was not produced by the upstream parallel run.
- AS-v2 label-noise paper has no upstream `idea.json`; the goal was reverse-
  engineered from the paper PDF per the documented fallback rule.
- Two FLT records share underlying content (one uses a non-namespaced
  goal.id from a hub-import file). Documented in `MANIFEST.md`.
- Sole-judge methodology is the dataset's largest credibility constraint.
  Multi-judge ensembles or human-validated subsets are recommended for
  downstream uses that require stronger calibration than a frozen single-
  instrument run can provide.

## Contact

[REDACTED FOR DOUBLE-BLIND REVIEW. To be populated at camera-ready.]
