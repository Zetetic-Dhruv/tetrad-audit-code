# Empirical Analysis Schema — goal-keyed JSON entries

**Captured:** 2026-05-07
**Purpose:** Specification for `goal_<id>.json` files that hold the Discovery Tetrad audit state per goal-object across all substrates. Designed for LLM-judge generation and for `jq`-based query of cross-substrate patterns.

---

## A. File layout

```
empirical_analysis/
  SCHEMA.md                         (this file)
  yaml_view.py                      (JSON ↔ YAML converter for human inspection)
  flt/    goal_<id>.json            (~354 files)
  slt/    goal_<id>.json            (~865 files)
  fp/     goal_<id>.json            (~10 files; witness includes step-level depth)
  asv1/   goal_<id>.json            (~50 files)
  asv2/   goal_<id>.json            (~15 files)
```

One JSON per goal. Subdirectories by substrate. No nesting beyond substrate dir.

---

## B. Goal ID generator rules

A `goal.id` is generated deterministically from the goal's substrate, type, parent artifact, and (optionally) descriptor. An LLM applying these rules to the same input must produce the same id every time.

### B.1 Format

```
<substrate>_<type>_<artifact_id>[_<descriptor>][_<index>]
```

Constraints applied in order:

1. ASCII only, lowercase.
2. Word separator: `_` (single underscore).
3. Sub-component separator: `__` (double underscore) — used to preserve hierarchy inside the `artifact_id` component.
4. Total length ≤ 80 characters. If exceeded, truncate `descriptor` (drop trailing words); never truncate `substrate`, `type`, `artifact_id`, or `index`.
5. The full id is also the filename stem (e.g., `flt_thm_pac__realizable_implies_pac_learnable.json`).

### B.2 Component values

#### `substrate` (fixed enum)

| Value | Substrate |
|---|---|
| `fp` | First-Proof Benchmark |
| `flt` | Formal Learning Theory kernel (your work) |
| `slt` | lean-stat-learning-theory (liminho123 et al.) |
| `asv1` | AI Scientist v1 |
| `asv2` | AI Scientist v2 |

#### `type` (fixed enum)

| Value | Use case | `goal.class` |
|---|---|---|
| `thm` | Lean4 theorem declaration | `theorem` |
| `prob` | First-Proof problem statement | `problem` |
| `hyp` | Main hypothesis of an AI-research paper (testable, has objective witness) | `hypothesis` |
| `subhyp` | Sub-hypothesis (testable, narrower objective witness) | `hypothesis` |
| `arg` | Argument (auditable only against literature; no objective witness possible) | `argument` |

The `class` is a separate field in the JSON body (see §C) that mirrors the `type` value. Both are recorded for clarity; `type` is for the id, `class` is the load-bearing semantic.

#### `artifact_id` (per-substrate generator)

| Substrate | Generator |
|---|---|
| `flt` | Lean4 namespace path with `.` → `__`, lowercased, `theorem` keyword stripped. Example: `FLT.PAC.RealizableImpliesPacLearnable` → `pac__realizable_implies_pac_learnable` |
| `slt` | Same as FLT. Example: `SLT.Dudley.entropyIntegral` → `dudley__entropy_integral` |
| `fp` | `problem_<n>` where n ∈ {1..10}. Example: `problem_3` |
| `asv1` | Paper directory short-name in snake_case, ≤ 16 chars. Example: `adaptive_dual_scale_denoising` → `adapt_dual_scale` |
| `asv2` | Same convention. Examples: `compositional-regularization` → `compreg`; `pest-detection` → `pest_detect`; `label-noise` → `label_noise` |

The artifact_id may itself contain `__` to preserve hierarchy (e.g., a Lean4 module path).

#### `descriptor` (optional)

Free-form snake_case phrase that distinguishes one goal from another within the same `<substrate>_<type>_<artifact_id>` namespace. Required for AS papers when multiple goals share the same paper. Optional for theorems/problems where artifact_id is already unique.

Constraints:
- ≤ 5 words (joined by `_`)
- ASCII lowercase
- Drops articles, prepositions when redundant
- Preserves load-bearing nouns

Examples:
- `compreg_argument_mechanism_compositional` → descriptor = `mechanism_compositional`
- `compreg_argument_evaluation_validity` → descriptor = `evaluation_validity`

#### `index` (optional)

Integer suffix (`_2`, `_3`, ...) used only when two goals collide on `<substrate>_<type>_<artifact_id>_<descriptor>`. Default omitted; first instance does not receive `_1`.

### B.3 Worked examples

| Source | Generated id |
|---|---|
| FLT theorem `FLT.PAC.RealizableImpliesPacLearnable` | `flt_thm_pac__realizable_implies_pac_learnable` |
| SLT theorem `SLT.Dudley.entropyIntegral` | `slt_thm_dudley__entropy_integral` |
| FP problem 3 ("Markov kernel construction") | `fp_prob_problem_3` |
| AS v2 compreg main hypothesis | `asv2_hyp_compreg_main` |
| AS v2 compreg argument: regularization mechanism is genuinely compositional | `asv2_arg_compreg_mechanism_compositional` |
| AS v2 compreg argument: synthetic arithmetic captures compositional generalization | `asv2_arg_compreg_eval_validity_synthetic` |
| AS v2 label-noise main hypothesis | `asv2_hyp_label_noise_main` |
| AS v2 pest-detection sub-hypothesis on real-world transfer | `asv2_subhyp_pest_detect_real_world_transfer` |

### B.4 LLM generator instructions (verbatim, for inclusion in prompts)

> When producing a `goal.id`, follow the schema strictly:
> 1. Identify the substrate from the source file path or context. Use one of: `fp`, `flt`, `slt`, `asv1`, `asv2`.
> 2. Identify the type. For Lean4 theorems use `thm`. For First-Proof problems use `prob`. For AS-paper main hypotheses use `hyp`. For sub-hypotheses use `subhyp`. For arguments (literature-reviewable claims with no objective experimental witness) use `arg`.
> 3. Identify the artifact_id per the substrate's generator rule (§B.2.artifact_id).
> 4. For AS papers, append a snake_case `descriptor` distinguishing this goal from sibling goals in the same paper. Keep ≤ 5 words.
> 5. Append `_<index>` only if a collision exists with a previously generated id in the same substrate directory.
> 6. Verify the result is ≤ 80 characters, ASCII lowercase, snake_case, ends with no trailing underscore.
> 7. The result is also the filename: `<id>.json`.

---

## C. JSON schema (per-goal entry)

### C.1 Top-level structure

```json
{
  "schema_version": "0.1",
  "goal": { ... },
  "tetrad_evaluation": { ... },
  "witness_loop": { ... },
  "outcome": { ... },
  "witnesses": [ ... ]
}
```

### C.2 `goal` block

```json
{
  "goal": {
    "id": "asv2_hyp_compreg_main",
    "substrate": "asv2",
    "type": "hyp",
    "class": "hypothesis",
    "parent_artifact": "compositional-regularization",
    "source": {
      "extraction_method": "ideation_json",
      "location": "AI-Scientist-v2/ai_scientist/ideas/i_cant_believe_its_not_better.json[0]",
      "verbatim_quote": "Introducing a compositional regularization term during training can encourage neural networks to develop compositional representations, thereby improving their ability to generalize to novel combinations of known components."
    },
    "description": "Free-text restatement if the source is not already a clean prose statement.",
    "captured_at": "2026-05-07T00:00:00Z",
    "evaluator": "llm_judge_<model>_<config>"
  }
}
```

`class` values: `theorem` | `problem` | `hypothesis` | `argument`. Differs from `type` (which is the id-component) in that `class` carries the load-bearing semantic the rubric reasons over.

`extraction_method` values: `ideation_json` | `lean_theorem_decl` | `fp_yaml` | `paper_internal` | `reverse_engineered_from_pdf`.

### C.3 `tetrad_evaluation` block (applied to the goal itself)

```json
{
  "tetrad_evaluation": {
    "plausibility": {
      "fired": true,
      "verdict": "pass",
      "reasoning": "Multi-line reasoning explaining why the verdict was issued.",
      "citations": [
        {
          "source": "external_repos/AI-Scientist-v2/ai_scientist/ideas/i_cant_believe_its_not_better.json:5",
          "quote": "Introducing a compositional regularization term during training..."
        }
      ]
    },
    "coherence": { "fired": true, "verdict": "pass", "reasoning": "...", "citations": [] },
    "completeness": { "fired": true, "verdict": "fail", "reasoning": "...", "citations": [] },
    "invariance": { "fired": false, "verdict": null, "reasoning": "Comp failed; Inv does not fire per cascade rule.", "citations": [] }
  }
}
```

Verdict values: `"pass"` | `"fail"` | `"escalate"` | `null` (only when `fired: false`).

`fired: false` cases:
- Comp/Inv when prerequisite gates failed (cascade rule)
- Pl when the entry is a pure axiom declaration (Pl-undefined)
- Any gate when the LLM-judge determines the gate is structurally inapplicable to the goal's class (e.g., goal-Inv on a pure-argument may default to `escalate`)

### C.4 `witness_loop` block

```json
{
  "witness_loop": {
    "iterations": 1,
    "settled": true,
    "halt_reason": "no_further_articulation"
  }
}
```

`iterations` ∈ {1, 2, 3} per the locked max-3 rule.
`settled: true` if no further articulation produced; `false` if halted at iteration 3 without convergence.
`halt_reason` ∈ {`no_further_articulation` | `max_iterations_reached`}.

### C.5 `outcome` block

```json
{
  "outcome": {
    "cell": 7,
    "cell_name": "open_step",
    "interpretation": "Goal is plausible and coherent under named mechanism, but completeness fails because scope inflates beyond what the artifact operationalizes (Abstract promises 'uncertainty estimation' coverage with no operationalization in the experiment plan)."
  }
}
```

`cell` ∈ {1..9}, derived deterministically from the verdict-vector (Pl, Coh, Comp, Inv) per the canonical 9-cell taxonomy.

`cell_name` is the the authors-locked operational label. **CRITICAL: cells 8 and 9 carry DIFFERENT labels at witness layer vs goal layer despite same verdict bits.** See `C.5.2` below for goal-layer taxonomy.

#### C.5.1 Witness-layer 9-cell taxonomy (cell ∈ {1..9})

1. `total_failure` — Pl=0, Coh=0, Comp=0
2. `sophism` — Pl=0, Coh=0, Comp=1 (template-shaped output with refuted premise and broken logic; deception or fabrication connotation)
3. `hallucination` — Pl=0, Coh=1, Comp=0 (internally consistent, refuted premise, not in valid result form; classical LLM failure mode)
4. `counterfactual` — Pl=0, Coh=1, Comp=1 (refuted but coherent and templated; alternative construction the field has considered and rejected)
5. `exploration_episode` — Pl=1, Coh=0, Comp=0 (canonical in-flight state)
6. `fallacy` — Pl=1, Coh=0, Comp=1 (Aristotle→Hamblin lineage; valid form, broken logic)
7. `open_step` — Pl=1, Coh=1, Comp=0. **Note**: negative results ARE valid template members; a closed negative result is cell 9, not cell 7. Cell 7 is "no closure yet," not "did not work yet."
8. `merely_true` — Pl=1, Coh=1, Comp=1, Inv=0. **WITNESS-LAYER SPECIFIC.** Captures: trivializing proof, exhaustive case-enumeration, inline-definition restatements, vacuous truth (a strict subset), p-hacking, Goodhart-overfitting. Closure is technically achieved without earning the structural import. *At goal layer, the same verdict bits carry a different label — see `supporting_argument` / `corollary` in C.5.2.*
9. `established_result` — Pl=1, Coh=1, Comp=1, Inv=1. **WITNESS-LAYER SPECIFIC.** Includes both positive and negative robust findings (a robust negative finding is also cell 9). *At goal layer, the same verdict bits carry a different label — see `fundamental_result` in C.5.2.*

#### C.5.2 Goal-layer 16-cell taxonomy (cell ∈ {1A, 1B, ..., 7B, 8, 9})

At goal layer, all four gates fire INDEPENDENTLY (no cascade). The verdict-vector space is full 2^4 = 16 cells, with sub-cells A (Inv=0) and B (Inv=1) for cells where Pl/Coh/Comp don't all pass.

| Cell | (Pl, Coh, Comp, Inv) | Label | Lineage anchor |
|---|---|---|---|
| 1A | (0,0,0,0) | `pseudo_problem` | Carnap 1928 *Scheinprobleme*; Ryle 1949 (category mistake); Wittgenstein |
| 1B | (0,0,0,1) | `private_theory` | the authors-coined; mechanism: coherent counterfactual mass eventually subsumes existing knowledge (a structured-inquiry framework itself, non-Euclidean geometry, Cantor's naive set theory). the authors: "the MOST generative category in the table." |
| 2A | (0,0,1,0) | `zombie_theorem` | the authors-coined; informal but vivid |
| 2B | (0,0,1,1) | `bold_conjecture` (refuted-but-foundational) | Popper 1959/1963; Laudan 1977; Vaihinger 1911; Magnani 2009 |
| 3A | (0,1,0,0) | `idle_speculation` | Currie & Sterelny 2017; Currie 2021 *Erkenntnis*; Laudan 1977 |
| 3B | (0,1,0,1) | `productive_speculation` | Currie 2021; Stent 1972 (premature theory); Laudan 1977 + Šešelja-Straßer 2014 |
| 4A | (0,1,1,0) | `closed_refutation` | (no canonical typology; "disproved conjecture" is descriptive) |
| 4B | (0,1,1,1) | `boundary_result` | Quine 1966 *Ways of Paradox* (veridical paradox; Cantor + Gödel as canonical instances); Hilbert 1926 ("Cantor's paradise") |
| 5A | (1,0,0,0) | `proto_hypothesis` | Steinle 2002/2016; Schaffner 1993; Reichenbach 1938; Magnani. the authors-relabel 2026-05-07 from `working_hypothesis` to defuse lab-science everyday-usage collision (Coh=0 means "no extant field mechanism captures it" but `working_hypothesis` in everyday lab usage implies Coh=1). |
| 5B | (1,0,0,1) | `frontier_direction` | Label the authors-locked (intuitive); classical lineage anchor = `programmatic_call` (Corry 1997 on Hilbert's Problem 6); Kuhn 1962 (candidate paradigm). the authors-relabel 2026-05-07 from `frontier_problem` to highlight that Comp=0 makes this a directional call rather than a template-shaped problem. |
| 6A | (1,0,1,0) | `orphan_result` | (no canonical typology; closest = Boden P-creativity; informal absorbed-anomaly) |
| 6B | (1,0,1,1) | `novel_discovery` | Kuhn 1962 (novelty of fact); Hanson 1958 (retroductive); Popper bold conjecture; Hacking |
| 7A | (1,1,0,0) | `minor_open_question` | (no canonical typology; informal "loose end / curiosity") |
| 7B | (1,1,0,1) | `research_programme` | **Lakatos** *Methodology of Scientific Research Programmes* (the authors-confirmed: Lakatos citation OK in this context, overriding the general Lakatos exclusion that applies elsewhere in this rubric). Also Hilbert 1900 (per Gray); Corry on Hilbert's 6th; Langlands 1967 |
| 8 | (1,1,1,0) | `supporting_argument` (general) / `corollary` (math-specific) | **GOAL-LAYER SPECIFIC.** Kuhn 1962 (normal-science puzzle solution); Polya 1954 (closed problem); Hardy 1940; Mancosu/Tappenden (non-fruitful theorem). *At witness layer, the same verdict bits carry the label `merely_true` — see C.5.1.* |
| 9 | (1,1,1,1) | `fundamental_result` | **GOAL-LAYER SPECIFIC.** Cluster anchor: Tappenden 2008/2012 (fruitful theorem); Mancosu 2008; Kuhn (exemplar); Hempel (DN-law); Popper (corroborated theory); Sosa/Williamson (apt belief / E=K). *At witness layer, the same verdict bits carry the label `established_result` — see C.5.1.* |

**Lakatos exception (cell 7B only)**: the general Lakatos exclusion applies elsewhere in this rubric (see `inquiry_urs_goal_layer_cells.md:101` anti-sophism discipline). For goal-cell 7B (`research_programme`), Lakatos's *Methodology of Scientific Research Programmes* is the dominant classical lineage and is the authors-confirmed citable. The exception applies ONLY to this cell.

**Goal-layer cell-name cross-cell findings**:
- Inv=0 sub-cells with novelty/defeat (1A, 2A, 3A, 4A, 6A, 7A): 2 have classical names (`pseudo_problem`, `idle_speculation`); 4 are unnamed (zombie_theorem the authors-coined; closed_refutation, orphan_result, minor_open_question are descriptive the authors-locked labels). The literature systematically under-records these failed-and-forgotten cells (survivorship bias).
- Inv=1 sub-cells with novelty/defeat (1B, 2B, 3B, 4B, 5B, 6B, 7B): 6 have strong classical anchors; 1 (1B `private_theory`) is the authors-coined.
- Time-indexing OUT OF SCOPE: cell assignment is a snapshot verdict; the mutability over time (e.g., a goal-cell-6B novel discovery migrating to goal-cell-9 fundamental result once the new mechanism is internalized by the field) is itself a meaningful signal but is NOT tracked in the rubric.

### C.6 `witnesses` array

Each entry is one witness. A goal may have multiple witnesses (different evidence types serving the same goal).

```json
{
  "witnesses": [
    {
      "id": "executed_paper_witness",
      "source": "external_repos/AI-Scientist-ICLR2025-Workshop-Experiment/compositional-regularization/annotated_paper.pdf",
      "description": "The executed paper's experimental section as the witness for the main hypothesis.",
      "tetrad_evaluation": { /* same shape as goal-level */ },
      "witness_loop": { /* same shape */ },
      "outcome": { /* same shape */ },
      "steps": null
    }
  ]
}
```

#### C.6.1 `steps` array (FP-only at present)

For FP problems, the witness has step-level depth. Each step is itself a mini-evaluation entry:

```json
{
  "steps": [
    {
      "id": "M1",
      "source": "FirstProof YAML problem_3 step M1",
      "description": "Metropolis-Hastings construction",
      "tetrad_evaluation": { /* per-step Pl/Coh/Comp/Inv */ },
      "outcome": { "cell": 8, "cell_name": "local_only_win", "interpretation": "..." }
    }
  ]
}
```

For non-FP substrates: `"steps": null`.

---

## D. Required vs optional fields

### D.1 Required at every level (goal, witness, step)

- `id` (witness-id and step-id are local; only goal.id follows §B generator)
- `source` (with at minimum `location`)
- `tetrad_evaluation` (all 4 gates present, even if some are `fired: false`)
- `outcome` (cell + cell_name + interpretation)

### D.2 Required at goal level only

- `goal.substrate`, `goal.type`, `goal.class`, `goal.parent_artifact`, `goal.captured_at`, `goal.evaluator`
- `schema_version` at top level

### D.3 Optional everywhere

- `witness_loop` (defaults to `{iterations: 1, settled: true}` if omitted)
- `description` (used when source extraction is not a clean prose quote)

---

## E. Validation rules

A goal entry is **valid** iff:

1. `goal.id` matches the regex `^(fp|flt|slt|asv1|asv2)_(thm|prob|hyp|subhyp|arg)_[a-z0-9_]+(_[0-9]+)?$` and is ≤ 80 chars.
2. The filename matches `<goal.id>.json`.
3. `goal.class` is consistent with `goal.type` (per §B.2 type table).
4. `tetrad_evaluation` contains all four gates as keys.
5. For each gate: `fired: true` ⟹ `verdict ∈ {"pass", "fail", "escalate"}` and `verdict: null` ⟹ `fired: false`.
6. `outcome.cell` is consistent with the verdict-vector per the 9-cell taxonomy.
7. `outcome.cell_name` matches the the authors-locked label for the cell.
8. `witness_loop.iterations` ∈ {1, 2, 3}.
9. Every `citations[].source` resolves to a real file path or PDF location (validatable against the actual repo).

A validation script (to be written) will check (1)-(8) syntactically and (9) by inspection.

---

## F. Query patterns (what falls out for free)

Run via `jq` over the directory tree.

| Question | Query sketch |
|---|---|
| All sophism (cell-2) verdicts across all goals | `jq -s '[.[] \| .. \| .outcome? \| select(.cell == 2)]' empirical_analysis/**/*.json` |
| Per-substrate cell distribution | `jq -s 'group_by(.goal.substrate) \| map({sub: .[0].goal.substrate, cells: [.[] \| .outcome.cell]})' empirical_analysis/**/*.json` |
| Direction-orientation pattern (clean goal, broken witness) | `jq -s '[.[] \| select(.outcome.cell >= 7 and (.witnesses[]?.outcome.cell // 9) <= 6)]' empirical_analysis/**/*.json` |
| Goal-witness alignment fail (Comp at goal layer pass, but Comp at witness layer fail) | `jq -s '[.[] \| select(.tetrad_evaluation.completeness.verdict == "pass" and .witnesses[]?.tetrad_evaluation.completeness.verdict == "fail")]' empirical_analysis/**/*.json` |
| Coh-Inv gap per substrate | aggregation script over per-gate verdicts |
| Escalation rate (fraction needing human review) | `jq -s '[.[] \| .. \| .verdict? \| select(. == "escalate")] \| length'` |

---

## G. yaml_view.py (companion converter)

Lightweight converter for human inspection. Two operations:

```bash
# JSON to YAML view (single file or directory)
python yaml_view.py to-yaml empirical_analysis/asv2/asv2_hyp_compreg_main.json

# YAML edits back to JSON canonical
python yaml_view.py to-json edited.yaml
```

The canonical files are JSON. YAML is a derived view; do not edit JSON files via the YAML view round-trip without validation.

---

## H. Open items

- [ ] `yaml_view.py` implementation (small Python script using `pyyaml` + `json`).
- [ ] Validation script (regex + jq + file-resolution checks).
- [ ] Per-substrate goal-extraction protocol (separate doc per substrate).
- [ ] Worked example: first goal entry to be `asv2_hyp_compreg_main.json`, generated using the verified case-study material.
- [ ] LLM-judge prompt template that instructs the judge to produce schema-valid output for one goal at a time.
