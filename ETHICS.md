# Ethics Statement

Captured 2026-05-07. This document accompanies the Discovery Tetrad audit
dataset for the NeurIPS 2026 Evaluations & Datasets track submission.

## Subjects and data

The dataset audits public mathematical and scientific research artifacts. It
does not collect data from human subjects, does not contain personally
identifiable information, and does not involve any clinical, behavioral, or
biometric data. Institutional Review Board (IRB) review was therefore not
required. The audited artifacts are:

- the Formal Learning Theory kernel (Lean 4 formalization),
- the Statistical Learning Theory library by liminho123 et al.
  (arXiv:2602.02285, Lean 4),
- ten First-Proof benchmark proof attempts (the public Harvard / multi-author
  research mathematics benchmark),
- ten example papers from Sakana AI's *AI Scientist v1* release, and
- three ICLR 2025 ICBINB workshop submissions from Sakana AI's
  *AI Scientist v2* release.

All five substrates are publicly distributed under their respective licenses.
The dataset's structured audit records are released under Apache 2.0; upstream
artifacts retain their original licenses.

## LLM-judge use

The audit instrument is a closed-weight large language model (Claude Opus 4.7,
claude-opus-4-7), applied uniformly across all five substrates with a frozen
prompt and assembly mapping. For the First-Proof inter-judge concordance
appendix only, an additional GPT-5.5 Pro judge and human grading were also
applied to the same problems. The dataset is honest about this dependency:

- LLM-judge stochasticity is the dominant residual source of run-to-run
  variance. Verdicts are generated at temperature 0 with the locked prompt;
  multi-judge consensus is recommended for downstream uses that require
  stronger calibration.
- Sophism detection asks the judge to recognize concealment-style failure
  patterns. Borderline cases may produce false positives or false negatives
  in the absence of multi-judge cross-check.
- The judge is instructed via the orchestrator prompt to escalate (rather than
  guess) when the evidence is undecidable. A non-zero escalation rate is by
  design.

## Authorship and provenance disclosures

Three of the five substrates (FLT, FP, AS-v1) include the authors' own work as
audited artifacts. The audit application is identical across all substrates;
the same locked judge prompt, assembly mapping, and dispatch policy are used.
Readers should nonetheless consider this provenance when interpreting per-
substrate cell distributions, particularly the contrast between substrates with
high sophism density and substrates with low sophism density. A double-blind
preserving formulation of this disclosure appears in the main paper.

## Potential dual-use concerns

The Discovery Tetrad rubric is an audit instrument; it is not an automation of
research production. The dataset's intended uses are:

- evaluation methodology research (construct validity, multi-judge calibration,
  process-conformance metrics),
- training and evaluation of process-reward models (PRMs), and
- comparative analysis of evaluation frameworks.

We do not anticipate misuse of the audit records themselves. We note one
indirect dual-use concern: the rubric reveals concrete, citable structural
failure modes (sophism, hallucination, transport failure) in published autonomous-
research artifacts. This information is already implicit in the underlying
papers; the dataset surfaces it more accessibly. We believe surfacing such
failure modes net advances the field's epistemic hygiene.

## Computational footprint

The pipeline runs ~60-90 minutes wall-clock for the full 282-record dataset
on a single laptop using the cloud LLM API. No on-premise GPU is used. The
energy footprint is dominated by the upstream LLM provider's inference
infrastructure. The pipeline is deterministic with respect to the frozen
prompt and assembly mapping; replication does not require a new training run.

## Safety review

No safety review was conducted because the artifacts being audited are
already publicly distributed and the pipeline does not generate novel content
beyond structured verdicts on those public artifacts.

## Bias and limitations disclosed in the paper

The paper discloses, as load-bearing limitations:

- single-judge methodology with frozen prompt (no multi-judge ensemble in the
  primary run; FP three-way concordance is the only multi-judge evidence);
- backward-only scope (forward-mode "discovery instrument" use is explicitly
  out of scope for this submission);
- audit-time snapshot only (the audit produces a snapshot verdict at evaluation
  time; cell migration over time is not tracked);
- five substrates, each with intentional choices — the dataset is not a
  representative sample of "all autonomous research output" but a structured
  cross-substrate test of the rubric.

## Contact

[REDACTED FOR DOUBLE-BLIND REVIEW. To be populated at camera-ready.]
