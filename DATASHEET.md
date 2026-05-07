# Datasheet: Discovery Tetrad Audit Dataset

Datasheet structure follows Gebru et al. (2021), *Datasheets for Datasets*.
Captured: 2026-05-07 (submission preparation).

---

## Motivation

**For what purpose was the dataset created?**
The dataset records the application of a four-gate process-conformance audit (the Discovery Tetrad) to long-horizon LLM-driven research artifacts across five substrates. Its purpose is to make process evidence in autonomous research systems reusable: each record types every audited goal and witness into a layer-aware cell of a 25-cell taxonomy and surfaces structural failure modes (e.g., sophistry, hallucination, transport failure) that one-shot accept/reject benchmarks miss.

**Who created the dataset and on behalf of which entity?**
[AUTHORS REDACTED FOR DOUBLE-BLIND REVIEW]

**Who funded the creation of the dataset?**
[FUNDING SOURCES REDACTED FOR DOUBLE-BLIND REVIEW]

**Any other comments?**
The dataset is intentionally small-N (282 records) but cross-substrate. Its
discriminative claim is not a leaderboard score; it is that the rubric resolves
clean Lean proofs (~0 sophism density) and autonomous AI research papers (~3.5
sophism flags per paper) cleanly.

## Composition

**What do the instances represent?**
Each instance is a per-goal JSON record conforming to `output_schema.json` (JSON
Schema Draft 7). A record contains:
- a goal block (id, substrate, type, class, parent_artifact, source location)
- a goal-layer four-gate evaluation (Plausibility, Coherence, Completeness,
  Invariance) with verdict, reasoning, and citations per gate
- a goal-layer outcome (cell ∈ 16-cell goal taxonomy, label, interpretation,
  sophism flag)
- one or more witness records, each with their own four-gate evaluation
  (cascade-aware: Inv fires only if Pl=Coh=Comp=1) and outcome (cell ∈ 9-cell
  witness taxonomy)
- optional step records (FP only: per-proof-step evaluations)

**How many instances are there in total?**
282 schema-valid records:
- 108 FLT (Formal Learning Theory kernel, Lean 4)
- 95 SLT (Statistical Learning Theory in Lean 4, third-party library)
- 56 AS-v1 (Sakana AI Scientist v1, 10 example_papers)
- 14 AS-v2 (Sakana AI Scientist v2, 3 ICLR 2025 ICBINB workshop submissions)
- 9 FP (First-Proof benchmark, 10 problems; Problem 1 has summary only)

**Does the dataset contain all possible instances or is it a sample?**
For the four substrates with public artifact collections (FLT, SLT, FP, AS-v2),
the dataset attempts goal-level coverage of every named theorem / problem /
hypothesis. AS-v1 covers all 10 published example_papers. The Lean substrates
(FLT, SLT) are evaluated at the granularity of named results; auxiliary lemmas
not named in the substrate's world model are not emitted as separate goals (per
the locked extraction policy). FP Problem 5 was added late (after the initial
download dump) and is fully covered; FP Problem 1 has a Markdown summary only.

**What data does each instance consist of?**
"Raw" data: the locked judge prompt + assembly mapping + per-substrate
extraction policy were applied to each (goal_source, witness) file pair to
produce the structured JSON record. The witness PDFs / Lean files / paper
artifacts themselves are NOT redistributed; the dataset references them by
location.

**Is there a label or target associated with each instance?**
Yes. Each record carries a four-gate verdict pattern at goal layer and at each
witness layer, plus the derived cell assignment (label) per layer.

**Is any information missing?**
- FP Problem 1: only a Markdown summary is included (no full structured JSON).
- AS-v2 label-noise paper: the upstream `idea.json` file does not exist in the
  Sakana release; per the documented the authors fallback rule the goal was reverse-
  engineered from the paper PDF.

**Are relationships between individual instances made explicit?**
Goals within the same parent_artifact share the artifact field; the dispatch
map (`dispatch_map.json`) records the (goal_source, witness) pair that produced
each record.

**Are there recommended data splits?**
Not applicable. The dataset is an audit dataset, not a benchmark for predictive
modeling.

**Are there any errors, sources of noise, or redundancies?**
- LLM-judge stochasticity. Verdicts are produced by a frozen Claude Opus 4.7
  judge prompt at temperature 0; nonetheless, deeper convergence requires
  multi-judge ensembling, which this dataset does not yet include.
- One AS-v2 paper (label-noise) lacks upstream provenance; goals were reverse-
  engineered.
- Two FLT records emerged from a hub-import file that re-exports declarations
  belonging to `Compression.lean`; one record uses an incorrect (non-namespaced)
  goal.id. Documented as a known issue.

**Is the dataset self-contained, or does it link to external resources?**
The dataset references upstream substrate artifacts (FLT kernel, SLT library,
Sakana AS papers, First-Proof submission) by relative path. Substrate context
files (`SUBSTRATE_README.md`, `final.json`, `origin.json`, etc.) are included as
provenance.

**Does the dataset contain confidential information?**
No. All audited artifacts are publicly available.

**Does the dataset contain data that, if viewed directly, might be offensive?**
No.

**Does the dataset relate to people?**
No. The dataset records audits of mathematical/scientific artifacts; it does
not collect personal information.

## Collection Process

**How was the data acquired?**
For each (goal_source, witness) pair in the locked dispatch map, the orchestrator
read the locked judge prompt, the goal-source files, the witness file, and any
substrate-context supplements; applied the Discovery Tetrad gates per layer; and
emitted one structured JSON record per identified goal.

**What mechanisms or procedures were used to collect the data?**
- LLM-judge instrument: Claude Opus 4.7 (claude-opus-4-7), used uniformly across
  all five substrates.
- For the FP three-way comparison appendix, a second judge (GPT-5.5 Pro) and the authors
  human grading were applied to the same FP problems for inter-judge agreement
  measurement.
- All judge calls used the locked `judge_prompt.txt` and `assembly_mapping.json`;
  no stochastic temperature setting outside what is documented in the per-run
  protocol record.

**Who was involved in the data collection process?**
[REDACTED FOR DOUBLE-BLIND REVIEW]. The the authors human-grading pass for the FP
gold-standard exemplars (Problem 2 and the FLT KL Divergence module) is
documented in `human_audit/pi_grading/`.

**Over what timeframe was the data collected?**
2026-05-07 (single-day pipeline run for the LLM-judge passes; the authors human
exemplars hand-written same day).

**Were any ethical review processes conducted?**
Not applicable; the dataset audits public artifacts only.

## Preprocessing / Cleaning / Labeling

**Was any preprocessing/cleaning/labeling done?**
- Substrate artifacts were copied (not modified) from upstream sources into
  per-substrate folders.
- Lean substrates were pre-verified clean (0 sorry, 0 errors, 0 warnings, 0
  axioms beyond Lean+Mathlib base) via comparator and lean4checker before the
  audit, and the pre-verification status was recorded in
  `flt/VERIFICATION_STATUS.md` and `slt/VERIFICATION_STATUS.md`. The audit
  judge does NOT re-run any Lean toolchain.
- Output JSON records were validated against `output_schema.json` and against
  the locked assembly mapping for cell-label consistency.

**Was the "raw" data saved?**
Yes; substrate artifacts are preserved verbatim in `flt/proofs/`, `slt/proofs/`,
`fp/proofs/`, `asv1/papers/`, `asv2/{compreg,pest_detection,label_noise}/`.

**Is the software used to preprocess/clean/label the data available?**
Yes; `validate_outputs.py` (schema + cascade + label consistency checks) and
`aggregate_stats.py` (cross-substrate aggregation) are released with the dataset.

## Uses

**Has the dataset been used for any tasks already?**
The dataset is the empirical core of [PAPER REDACTED FOR DOUBLE-BLIND REVIEW],
submitted to the NeurIPS 2026 Evaluations & Datasets track.

**Is there a repository that links to any or all papers / systems that use the dataset?**
[REDACTED — to be populated at camera-ready.]

**What (other) tasks could the dataset be used for?**
- Calibration of LLM-judge reliability on long-horizon research artifacts
- Construct-validity studies for evaluation frameworks
- Comparative analysis of process-conformance vs outcome-only benchmarks
- Training/fine-tuning of process-reward models (PRMs) for research-grade tasks

**Is there anything about the composition of the dataset or the way it was collected and preprocessed/cleaned/labeled that might impact future uses?**
- The judge instrument is a single closed-weight LLM (Claude Opus 4.7); users
  who require open-weight reproducibility or multi-judge consensus should run
  additional passes.
- Sophism detection requires the LLM-judge to recognize concealed-failure
  patterns; absent multi-judge cross-check, false positives or false negatives
  on borderline cases cannot be fully ruled out.

**Are there tasks for which the dataset should not be used?**
- The dataset should not be used as ground truth for the underlying mathematical
  or scientific claims being audited. A goal-layer `fundamental_result` verdict
  is a structural claim about the goal's plausibility, coherence, completeness,
  and foundation potential, not a verification of its mathematical correctness.
- The dataset should not be used as a leaderboard for AI-research systems. It
  is descriptive (which structural failure modes are present?), not normative
  (which system is better?).

## Distribution

**Will the dataset be distributed to third parties?**
Yes; planned public release on a permanent persistent-identifier platform
(Zenodo, Hugging Face, or similar) at camera-ready.

**How will the dataset be distributed?**
Anonymous archive at submission; permanent DOI at camera-ready.

**When will the dataset be distributed?**
- Submission: anonymized supplementary archive.
- Camera-ready (if accepted): public release with DOI.

**Will the dataset be distributed under a copyright or other intellectual property (IP) license, and/or under applicable terms of use (ToU)?**
Apache License 2.0 (see `LICENSE`).

**Have any third parties imposed IP-based or other restrictions on the data associated with the instances?**
The substrate artifacts are governed by their own upstream licenses:
- FLT kernel: see upstream LICENSE
- SLT library (liminho123 et al., arXiv:2602.02285): see upstream LICENSE
- First-Proof submission: Apache 2.0 per upstream
- AS-v1, AS-v2 (Sakana AI): Sakana's *AI Scientist Source Code License*
  (see upstream)

The dataset's structured audit records (the 282 JSONs) are released under
Apache 2.0; the upstream artifacts referenced by location retain their
original licenses.

## Maintenance

**Who will be supporting/hosting/maintaining the dataset?**
[REDACTED — populated at camera-ready.]

**How can the owner/curator/manager of the dataset be contacted?**
[REDACTED — populated at camera-ready.]

**Is there an erratum?**
A `CHANGELOG.md` will track post-submission corrections (e.g., the documented
FLT goal_id duplicate noted under "Errors").

**Will the dataset be updated?**
Possibly, in a versioned way, after camera-ready: (a) inter-judge concordance
expansion, (b) additional human-graded subsets, (c) FP Problem 1 full JSON
when the upstream parallel run produces it.

**If others want to extend/augment/build on/contribute to the dataset, is there a mechanism for them to do so?**
Pull requests on the public repository at camera-ready; an issue template will
gate audits added to the corpus by requiring schema conformance and substrate-
specific extraction-policy compliance.
