# Benchmark Guide

## Reading the numbers

All percentage deltas in the model report are **Tuned minus that model's own official Base**, in absolute percentage points. Qwen and HCX raw scores must not be mixed into a single architecture ranking because their official checkpoints, chat templates, vision policies and pretraining histories differ.

| Metric | Meaning | Direction | Important caveat |
|---|---|:---:|---|
| Exact / normalized exact | After evaluator normalization, prediction and canonical answer are identical | Higher | Correct content with extra prose can fail |
| Containment | Canonical target occurs inside normalized output | Higher | More permissive than exact; hallucinated extra claims may still pass |
| Format | Required answer wrapper/choice/short-answer form was parsed | Higher | Format success is not semantic correctness |
| Similarity | Evaluator's normalized string/semantic similarity in [0,1] | Higher | Near-name answers can score partially without being canonical |
| CER | Character edit distance divided by reference length | Lower | Can exceed 1 when insertion is heavy |
| Line recall | Fraction of reference OCR lines recovered | Higher | Does not penalize all extra text |
| Accuracy / aAcc | Correct rows divided by evaluated rows; Hallusion aAcc balances its paired structure | Higher | Compare only matched protocols |
| pass@1 | First generated program passes hidden tests | Higher | Sensitive to code extraction and runtime |
| ToolSandbox similarity | Milestone completion minus minefield penalties, aggregated by scenario | Higher | Continuous, not plain accuracy |
| Tau reward | End-to-end task reward from actions, state checks and communication | Higher | Domain/trial weighting must match |

## Benchmark families

### General vision-language

- **MMBench DEV EN v1.1**: English visual perception, relation, logic and knowledge multiple choice.
- **MMStar / MMStar-KO**: leakage-reduced multimodal core skills in English and Korean.
- **KRETA**: Korean-centric document, chart, scene and reasoning evaluation.
- **MMMU-Pro 10c**: college-level multidisciplinary visual problems with ten choices.
- **HallusionBench**: visual faithfulness and hallucination resistance; report `aAcc`.
- **MathVista MINI**: visual mathematical reasoning. It is available in the HCX comparison; the Qwen run retained predictions but not an authoritative scored row.

### Mammoth OCR and heritage

- **Heritage Multi** asks attributes, **Reverse** selects the matching image, and **Simple** freely names a heritage object.
- **OCR Font**, **Outdoor** and **Public** cover rendered fonts, signs/scenes and administrative documents.
- Exact, containment, similarity, CER and line recall should be read together. Exact alone confounds recognition and output policy.

### Cultural Focus and H400/HS100

- **Cultural Focus identity** is exact official-title recognition; **view caption** is strict caption/year matching. `overall` aggregates both and is therefore much harder than identity alone.
- **H400 Direct** is open-vocabulary held-out naming; **H400 Hard** is same-family multiple choice; **Knowledge Image/Text** test factual knowledge.
- **HS100 Train** measures memorization/fit, **Unseen** measures new-view transfer, and **Simple** is only the 102-row intersection with the original Simple style. These are not aliases for full Mammoth Heritage Simple (768 rows).

### OpenCompass language

- **Core**: IFEval, AIME 2024/2025, PRM800K math, BBH, GPQA, MMLU-Pro, HumanEval, LiveCodeBench and long-context suites.
- **Extra**: ARC, BoolQ, COPA, CommonsenseQA, HellaSwag, OpenBookQA, PIQA, SIQA, WinoGrande, MMLU, GSM8K, MATH, MBPP, LAMBADA, DROP and Natural Questions.
- **Korean**: KMMLU, CSATQA, HAE-RAE, K2-Eval, KoBEST, KOBALT and Korean clinical QA.
- The first row in each score table is the configured aggregate, not another dataset.

### Tool use and agents

- **BFCL V4** parses function calls into ASTs and tests simple, multiple, parallel and multi-turn calls, including missing-function/parameter and long-context cases.
- **ToolSandbox** runs phone-like stateful scenarios with distractor tools, milestone goals and minefields.
- **Tau2** evaluates airline, retail and telecom interactions. **Tau3** adds revised environments and banking knowledge with repeated trials.
- BFCL's run directory retained score CSVs and diagnostic logs but not the raw generation corpus; paired output examples are therefore provided for Tau2/Tau3, while BFCL is documented with its category scores and observed empty-response diagnostics in the main report.
