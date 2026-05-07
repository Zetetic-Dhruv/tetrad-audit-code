# Empirical Analysis — Import Manifest

Imported 2026-05-07 for the Discovery Tetrad backward-audit experiment.
All files are **copies**; originals remain untouched.

## Substrate inventory

| Substrate | Files imported | Source | Notes |
|-----------|----------------|--------|-------|
| **flt/** | 53 .lean files (FLT_Proofs/ tree preserved) + premise/{final.json, origin.json} + SUBSTRATE_README.md (110KB) + VERIFICATION_STATUS.md | `formal-learning-theory-kernel/` | 354 theorems / 21,728 lines / 0 sorry / 0 errors / 0 warnings / 0 axioms — pre-verified |
| **slt/** | 55 .lean files (SLT/ tree preserved) + SUBSTRATE_README.md + VERIFICATION_STATUS.md | `Formal Learning Theory/prior-art/lean-stat-learning-theory/` | 865 traced theorems / 18,669 tactic steps — pre-verified clean (liminho123, arXiv:2602.02285) |
| **fp/** | 10 PDFs in proofs/ + 7 yamls + 6 csvs + xlsx in datasets/ + discovery_loop_prompt.yaml in code/ + SUBSTRATE_README.md | `First-Proof-Benchmark-Results/` | 10 problems, 85 audited proof steps; existing GPT-as-judge yamls present for 3-way comparison appendix |
| **asv1/** | 10 per-paper subfolders in papers/ (each: PDF + ideas.json + seed_ideas.json + prompt.json + review.txt + notes.txt) + SUBSTRATE_README.md | `external_repos/AI-Scientist/example_papers/` | Sakana AS-v1; templates: NanoGPT, 2D Diffusion, Grokking. ideas.json has ~50 evaluated ideas per paper (Name, Title, Experiment, Interestingness, Feasibility, Novelty). |
| **asv2/** | compositional-regularization/ + pest-detection/ + label-noise/ (each: paper.pdf, review.pdf, idea.json, ideation_seed.py, topic.md, ai_reviews/, inventory.md, inventory_BETA.md) + INVENTORY.md + SUBSTRATE_README.md | `external_repos/as_v2_workshop_assets/` + `external_repos/AI-Scientist-v2/` | 3 ICLR 2025 ICBINB Workshop submissions; compositional-regularization is the headline ACCEPTED case (scores 6,7,6) |

## Goal-source map (per the authors 2026-05-07: NO separate goals.json extraction)

The orchestrator agent reads goal-level structure directly from substrate-native sources:

| Substrate | Goal-source | Goal unit | Witness pointer |
|-----------|-------------|-----------|-----------------|
| flt | `flt/premise/final.json` + `flt/premise/origin.json` (paradigm joints, hub files, type health, break points, counterdefinitions) | per Lean theorem declaration | proof term in same `.lean` file |
| slt | NO goal-level file. Fallback rule: each Lean theorem statement IS its goal; goal = "what the witness tries to prove" | per Lean theorem declaration | proof term in same `.lean` file |
| fp | `fp/datasets/yaml/proof_summary.yaml` + `fp/datasets/yaml/tactic_data.yaml` | per problem (10) and per step (85) | `fp/proofs/zetesis_proof_attempt_P<n>.pdf` |
| asv1 | `asv1/papers/<name>/ideas.json` + `asv1/papers/<name>/seed_ideas.json` | per evaluated idea | `asv1/papers/<name>/<name>.pdf` |
| asv2 | `asv2/<name>/idea.json` (main hypothesis); `asv2/<name>/topic.md` (workshop scope) | per main hypothesis + reverse-engineered sub-hypotheses/arguments from paper | `asv2/<name>/paper.pdf` + `asv2/<name>/review.pdf` + `asv2/<name>/ai_reviews/` |

**Fallback rule (when goal-level file is unavailable):** evaluate ONLY theorems and experiments, with the goal defined as "what the witness tries to prove." Per the authors lock 2026-05-07.

## Output directories (created, empty)

```
fp/outputs/           # one JSON per goal × layer (filename = goal.id + .json)
flt/outputs/
slt/outputs/
asv1/outputs/
asv2/outputs/
```

## Human audit directories (created, empty)

```
human_audit/
├── pi_grading/        # the authors's hand-graded subset (FP + FLT subset incl. VC bounds in Gold + optional)
├── gpt_judge_fp/      # the authors's prior GPT-5.2-as-judge FP yamls go here for 3-way comparison
└── claude_judge_fp/   # Claude-as-judge FP results extracted from fp/outputs/ for comparison
```

## Locked spec files (in place)

- `SCHEMA.md` — full per-goal JSON schema specification (§B id generator + §C JSON shape + §D required/optional + §E validation)
- `output_schema.json` — strict JSON Schema (Draft 7) for output validation
- `assembly_mapping.json` — verdict-bits → cell-number → cell-label proto-compiler (single source of truth)
- `judge_prompt.txt` — frozen single-profile judge prompt; assembly mapping reproduced inline
- `judge_protocol_template.txt` — per-run record template (drop a copy alongside outputs/ per substrate run)
- `dispatch_map.json` — 131 (goal_source, witness) pairs across 5 substrates; one pair = one parallel-agent unit; 14 batches at 10 agents/batch. Each pair carries an `extraction_policy` string for agent-runtime goal discovery.

## Pending

- `aggregate_stats.py` — stratified-aggregation harness (post-output query layer)
- Validation script (per `SCHEMA.md` §E)

## Sequencing per the authors lock (2026-05-07)

1. **FLT first** — calibration batch, then full sweep
2. **SLT second** — once FLT throughput is calibrated
3. **FP** with Claude-as-judge run, then 3-way comparison appendix (Claude ↔ GPT ↔ the authors)
4. **AS-v2** — including the compositional-regularization headline case study
5. **AS-v1** — as the broader autonomous-research-systems baseline

## Pre-verification note

FLT and SLT have been pre-verified via comparator + lean4checker (per VERIFICATION_STATUS.md in each substrate folder). The audit-running agents must not re-run any Lean toolchain commands. Verification status is operator-internal context; the same note appears at the bottom of `judge_prompt.txt` marked for deletion before serving to the LLM-judge.

## VC bounds in Gold Paradigm — human-reviewer surface track

Per the authors: this theorem will be submitted separately as the canonical "human reviewer extracts K, U, c(K) from a closed FLT theorem" worked example for the rubric. Likely lives in `flt/proofs/Theorem/Gold.lean` (also `Complexity/DualVC.lean` is a candidate). the authors to confirm exact theorem name / location when the human-grading pass starts.
