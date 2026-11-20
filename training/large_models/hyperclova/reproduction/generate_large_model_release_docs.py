#!/usr/bin/env python3
"""Generate release-ready benchmark guides and paired-output reports."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
RELEASE_ROOT = ROOT / "releases"

SPECS = {
    "qwen27b": {
        "slug": "qwen35-27b-h400-hs100-s2500-20260902",
        "title": "Qwen3.5-27B H400/HS100 Step-2500",
        "official": "Qwen/Qwen3.5-27B",
        "base": "Official Qwen3.5-27B",
        "tuned": "Qwen3.5-27B tuned",
        "examples": ROOT / "results/qwen27b_release_paired_examples_20260902.json",
        "score_report": ROOT / "reports/qwen35_27b_official_vs_h400_hs100_scale2500_full_20260902.md",
        "model_path": "/data/workspace/post-training/outputs/qwen35-27b-official-h400-hs100-scale2500-step2500-hf",
        "weight_note": "Native BF16 HF export (single safetensors file).",
        "vision_policy": "Vision encoder frozen except the final two blocks, trained at 5e-8; visual merger trainable at 7.5e-7.",
        "headline": [
            "General-VL macro +4.09 pp, OpenCompass Core +0.62 pp, Extra +0.26 pp, Korean -0.05 pp.",
            "H400 hard choice +50.76 pp, but H400 direct exact only +1.07 pp and HS100 train remains 0%.",
            "The run learned closed-set discrimination but did not acquire broad image-to-canonical-name recall.",
            "BFCL +0.33 pp, ToolSandbox +0.0098, Tau2 unchanged, Tau3 +1.67 pp weighted.",
        ],
        "diagnosis": [
            "The 27B run starts from the untouched official model. It does not inherit the H300 identity-acquisition parent used by the successful Qwen 9B branch.",
            "A paired H400 audit finds 13/654 exact for tuned 27B versus 312/654 for selected 9B. Formatting succeeds on all 654 rows, so this is not a parser or stop-token failure.",
            "Predictions collapse toward a small set of plausible names; the top ten labels occupy 21.41% of outputs. More direct identity acquisition and held-out-direct milestone selection are required.",
        ],
    },
    "hcx32b": {
        "slug": "hyperclovax-seed-think-32b-h400-hs100-s2500-bf16-20260902",
        "title": "HyperCLOVAX-SEED-Think-32B H400/HS100 Step-2500",
        "official": "naver-hyperclovax/HyperCLOVAX-SEED-Think-32B",
        "base": "Official HyperCLOVAX-SEED-Think-32B",
        "tuned": "HCX 32B tuned",
        "examples": ROOT / "results/hcx32b_release_paired_examples_20260902.json",
        "score_report": ROOT / "reports/hcx32b_official_vs_h400_hs100_scale2500_full_20260902.md",
        "model_path": "/data/workspace/post-training/outputs/hyperclovax-seed-think-32b-h400-hs100-scale2500-step2500-hf-bf16-release-20260902",
        "weight_note": "Deployment BF16 conversion of the verified FP32 HF export; all 1,043 tensor keys are preserved.",
        "vision_policy": "Vision encoder fully frozen; visual merger trainable at 7.5e-7.",
        "headline": [
            "H400 direct +69.11 pp, H400 hard +29.97 pp, HS100 unseen +73.27 pp, HS100 Simple +64.71 pp.",
            "Mammoth Heritage Simple +9.38 pp and Cultural Focus identity +19.75 pp.",
            "General-VL macro -0.90 pp, with KRETA -6.25 pp and HallusionBench -1.68 pp as the main regressions.",
            "BFCL +7.15 pp and ToolSandbox +0.0467, but Tau3 weighted -3.87 pp.",
        ],
        "diagnosis": [
            "Unlike Qwen 27B, HCX successfully acquired both free-form identities and closed-set discrimination from the same target mixture.",
            "The strongest gains are concentrated in H400/HS100 in-scope identities. HS100 Train is a recall diagnostic, while HS100 Unseen is the more meaningful cross-view transfer measure.",
            "The model is not a uniform upgrade: KRETA, HallusionBench, BBH, GPQA, LCB and several Tau3 domains regress. Preservation replay or model merging should be evaluated before general deployment.",
        ],
    },
}

MAMMOTH_DESC = {
    "heritage_multi_attr": ("Mammoth Heritage Multi", "이미지에서 문화재의 분류·시대·소재·지역 같은 속성을 짧은 키워드로 답한다."),
    "heritage_reverse_mt": ("Mammoth Heritage Reverse", "문화재 명칭을 보고 네 장의 후보 이미지 중 맞는 이미지를 고르는 역방향 선택 문제다."),
    "heritage_simple": ("Mammoth Heritage Simple", "단일 이미지에서 문화재의 정확한 공식 명칭을 자유 생성한다."),
    "ocr_font": ("Mammoth OCR Font", "합성 또는 다양한 한글 폰트로 표시된 강조 문자열을 전사한다."),
    "ocr_outdoor": ("Mammoth OCR Outdoor", "간판·매장·실외 장면의 지정 영역에 있는 한국어를 전사한다."),
    "ocr_public_exec": ("Mammoth OCR Public", "공문서·행정문서의 날짜·기관·필드 등 강조 영역을 전사한다."),
}
TARGET_DESC = {
    "h400_direct": ("H400 Direct", "H400 범위의 held-out 실제 이미지에서 공식 명칭을 설명 없이 자유 생성한다."),
    "h400_hard": ("H400 Hard", "같은 계열의 혼동하기 쉬운 후보 중 정답을 선택하여 세밀한 시각 구분력을 본다."),
    "h400_knowledge_image": ("H400 Knowledge Image", "문화재 이미지와 함께 시대·인물·용도·역사적 사실을 묻는다."),
    "h400_knowledge_text": ("H400 Knowledge Text", "이미지 없이 문화재 관련 사실 지식을 묻는다."),
    "hs100_train": ("HS100 Train", "집중 학습한 100개 identity의 학습 view 회상률을 본다. 일반화 지표가 아니다."),
    "hs100_unseen": ("HS100 Unseen", "같은 100개 identity의 학습에 쓰지 않은 실제 view로 cross-view 일반화를 본다."),
    "hs100_simple": ("HS100 Simple", "HS100과 원래 Mammoth Simple가 교차하는 102개 행에서 exact-name 성능을 본다."),
}
VL_DESC = {
    "MMBench_DEV_EN_V11": "영어 이미지 객관식 QA. 지각, 관계, 논리, 지식 결합을 정확도로 측정한다.",
    "MMStar": "데이터 누출을 줄인 1,500개 멀티모달 객관식으로 여섯 핵심 능력을 측정한다.",
    "MMStar_KO": "MMStar의 한국어 프로토콜로 한국어 시각 추론과 출력 안정성을 측정한다.",
    "KRETA": "한국어 중심의 문서·도표·일상 이미지 이해 및 추론 능력을 측정한다.",
    "MMMU_Pro_10c": "대학 전공 수준의 이미지·도표 문제를 10개 선택지로 풀어 전문 지식과 추론을 측정한다.",
    "HallusionBench": "이미지에 근거하지 않은 환각을 억제하고 질문을 정확히 판별하는지 aAcc로 측정한다.",
    "MathVista_MINI": "도표·기하·과학 그림을 포함한 시각 수학 추론 정확도를 측정한다.",
}
OC_DESC = {
    "aime2024": "AIME 2024 경시 수학. 최종 정수 답을 `\\boxed{}`에서 파싱해 exact로 판정한다.",
    "bbh-date_understanding": "BBH 날짜 이해. 다단계 규칙 추론 후 선택지를 맞힌다.",
    "gpqa": "GPQA Diamond 대학원급 과학 객관식. 전문 지식과 깊은 추론을 본다.",
    "mmlu_pro": "MMLU-Pro 10지선다. 광범위한 학문 지식과 고난도 추론을 본다.",
    "humaneval": "함수 docstring을 만족하는 코드를 생성하고 hidden unit test pass@1로 판정한다.",
    "ifeval": "지정된 형식·길이·키워드·금지 조건을 엄격히 따르는지 instruction-level로 판정한다.",
    "arc_c": "ARC-Challenge 과학 상식 객관식.",
    "boolq": "짧은 문맥을 읽고 yes/no 질문에 답하는 독해 벤치마크.",
    "commonsense": "CommonsenseQA 일상 상식 객관식.",
    "gsm8k": "초등 수학 서술형. 최종 수치 exact를 측정한다.",
    "math": "MATH 고등 수학 문제. 정규화된 최종 수식/답 exact를 측정한다.",
    "mbpp": "짧은 Python 프로그래밍 문제를 unit test pass@1로 판정한다.",
    "drop": "문단에서 수치·산술·불연속 span 추론을 수행하고 F1/EM으로 평가한다.",
    "nq": "Natural Questions 단답 지식 QA. 정규화된 답 일치로 평가한다.",
    "kmmlu": "한국어 전문·상식 다분야 객관식.",
    "csatqa": "한국 수능형 언어·사회·과학 객관식 추론.",
    "hae": "HAE-RAE 한국 문화·역사·언어 지식 평가.",
    "kobest": "KoBEST의 BoolQ/COPA/HellaSwag/SentiNeg 등 한국어 이해 묶음.",
    "kobalt": "한국어 장문·지시·추론 능력 묶음.",
    "clinical": "한국어 임상·의학 QA.",
}


def clip(value: Any, limit: int = 1800) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    head = int(limit * 0.65)
    tail = limit - head
    return f"{text[:head]}\n... <{len(text) - limit} chars omitted> ...\n{text[-tail:]}"


def code_block(value: Any) -> list[str]:
    return ["```text", clip(value) or "(empty)", "```", ""]


def source_question(row: dict[str, Any]) -> str:
    if row.get("question"):
        return str(row["question"])
    source = row.get("source_record", {})
    messages = source.get("messages", []) if isinstance(source, dict) else []
    for message in messages:
        if message.get("role") != "user":
            continue
        content = message.get("content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            texts = [item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text"]
            if texts:
                return "\n".join(texts)
    return "(prompt text not repeated in prediction artifact)"


def record_metrics(row: dict[str, Any]) -> str:
    parts = []
    for key in ("exact", "normalized_exact", "contains", "choice_correct", "similarity", "finish_reason"):
        if key in row:
            value = row[key]
            if isinstance(value, float):
                value = f"{value:.4f}"
            parts.append(f"{key}={value}")
    return ", ".join(parts) or "per-benchmark evaluator result"


def render_pair(lines: list[str], title: str, description: str, pair: dict[str, Any]) -> None:
    base, tuned = pair["base"], pair["tuned"]
    lines.extend((f"### {title}", "", description, "", f"- Sample key: `{pair.get('pair_key', pair.get('sample_key', '-'))}`", "- Prompt:"))
    lines.extend(code_block(source_question(base)))
    gold = base.get("gold_target", base.get("gold_response", "(see benchmark reference)"))
    lines.extend(("- Reference:", *code_block(gold), "- Official Base output:", *code_block(base.get("prediction", ""))))
    lines.append(f"- Base scoring: `{record_metrics(base)}`")
    lines.extend(("", "- Tuned output:", *code_block(tuned.get("prediction", ""))))
    lines.append(f"- Tuned scoring: `{record_metrics(tuned)}`")
    lines.extend(("", "판독: 이 예시는 동일 sample ID의 실제 평가 레코드이며, 선택된 예시는 가능한 경우 Base 실패/Tuned 성공을 우선한다.", ""))


def render_vl(lines: list[str], name: str, pair: dict[str, Any]) -> None:
    base, tuned = pair["base"], pair["tuned"]
    lines.extend((f"### {name}", "", VL_DESC.get(name, "멀티모달 질의응답 벤치마크."), "", f"- Sample key: `{pair['sample_key']}`", "- Question:"))
    prompt = base.get("question", "")
    options = "\n".join(f"{key}. {base[key]}" for key in ("A", "B", "C", "D") if key in base)
    lines.extend(code_block(f"{prompt}\n{options}".strip()))
    lines.extend((f"- Reference: `{base.get('answer', '(judge-based)')}`", "", "- Official Base output:", *code_block(base.get("prediction", "")), "- Tuned output:", *code_block(tuned.get("prediction", ""))))


def render_oc(lines: list[str], name: str, pair: dict[str, Any]) -> None:
    short = name.split("/", 1)[1]
    lines.extend((f"### OpenCompass {name}", "", OC_DESC.get(short, "OpenCompass 등록 데이터셋의 대표 문제."), "", f"- Prediction shard: `{pair['source_file']}`, sample `{pair['sample_key']}`", "- Prompt:"))
    lines.extend(code_block(pair["base"].get("prompt", "")))
    reference = next((pair["base"][key] for key in ("gold", "reference", "answer", "label") if key in pair["base"]), None)
    if reference is not None:
        lines.extend(("- Reference:", *code_block(reference)))
    else:
        lines.extend(("- Reference: evaluator dataset object에 보존되며 prediction shard에는 반복 저장되지 않음.", ""))
    lines.extend(("- Official Base output:", *code_block(pair["base"].get("prediction", "")), "- Tuned output:", *code_block(pair["tuned"].get("prediction", ""))))


def render_sim(lines: list[str], suite: str, domain: str, pair: dict[str, Any]) -> None:
    lines.extend((f"### {suite} {domain}", "", "상태가 있는 도구 환경에서 정책 준수, 올바른 API 호출, DB 상태 변화와 최종 응답을 end-to-end reward로 평가한다.", "", "- User request:"))
    lines.extend(code_block(pair["base"].get("user", "")))
    for label, row in (("Official Base", pair["base"]), ("Tuned", pair["tuned"])):
        lines.extend((f"- {label} final output:", *code_block(row.get("final_assistant", ""))))
        lines.append(f"- {label} final tool calls: `{clip(row.get('tool_calls'), 1000)}`")
        lines.append(f"- {label} reward: `{row.get('reward')}`, termination: `{row.get('termination_reason')}`")
        lines.append("")


def benchmark_guide() -> str:
    return """# Benchmark Guide

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
"""


def readme(spec: dict[str, Any]) -> str:
    bullets = "\n".join(f"- {item}" for item in spec["headline"])
    diagnosis = "\n".join(f"- {item}" for item in spec["diagnosis"])
    return f"""# {spec['title']}

This package contains a Hugging Face multimodal checkpoint, its official-base comparison, benchmark definitions, actual paired Base/Tuned outputs, selected sample images, raw compact example JSON and reproducibility metadata.

## Identity

- Official comparison base: `{spec['official']}`
- Tuned HF source: `{spec['model_path']}`
- Weight representation: {spec['weight_note']}
- Selection checkpoint: step 2,500

## Training contract

- Hardware: 16 H200 nodes, 8 GPUs/node, 128 ranks.
- Sequence: 4,096 packed tokens; text-only cap 3,584; image pixels 65,536 to 1,048,576.
- Per-device batch 1, gradient accumulation 2, 2,500 optimizer steps.
- Source supervised-token mix: Fable 10%, VisualWeb 10%, H400/HS100 target 80%.
- Target lanes: H400 direct .32, multiview .10, hard .08, image knowledge .05, text knowledge .05; HS100 direct .25, multiview .10, hard .05.
- Decoder LR 5e-7, visual merger LR 7.5e-7, constant schedule after 100-step warmup.
- Heritage augmentation probability .60; light affine, brightness/contrast/saturation/sharpness, rare blur/JPEG; no flip.
- {spec['vision_policy']}
- BF16 training, TF32, non-reentrant gradient checkpointing and FSDP full-shard across groups of 16 ranks.

## Result synopsis

{bullets}

## Analysis

{diagnosis}

## Package layout

```text
model/                              Hugging Face config, tokenizer, processor and safetensors
reports/DETAILED_SCORE_REPORT.md    Every authoritative Base/Tuned score and delta
reports/BENCHMARK_GUIDE.md          What each suite and metric measures
reports/PAIRED_OUTPUT_EXAMPLES.md   Actual prompts and Base/Tuned outputs
reports/TRAINING_CONFIG.yaml        Exact Kubernetes training manifest
samples/images/                     Representative benchmark images
samples/paired_examples.json        Machine-readable paired examples
reproduction/                       Report/extraction/packaging scripts
PACKAGE_MANIFEST.json               Model validation and package provenance
SHA256SUMS                          SHA-256 for every packaged file
```

## Loading

Use the model's bundled processor/tokenizer and enable remote model code for HCX. The exact class depends on the installed Transformers revision, so `AutoModelForImageTextToText` is the preferred entry point.

```python
import torch
from transformers import AutoModelForImageTextToText, AutoProcessor

path = "./model"
processor = AutoProcessor.from_pretrained(path, trust_remote_code=True)
model = AutoModelForImageTextToText.from_pretrained(
    path,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True,
)
```

Read `reports/DETAILED_SCORE_REPORT.md` before promotion. Target-gate improvements do not imply a uniform general-purpose upgrade.
"""


def build_examples(spec: dict[str, Any], data: dict[str, Any]) -> str:
    lines = [
        f"# {spec['title']}: Paired Output Examples",
        "",
        "Every example below comes from the actual evaluation artifacts and uses the same sample key for official Base and Tuned. Examples are selected to be diagnostic, preferring Base-fail/Tuned-pass when available; they are not random estimates of overall accuracy.",
        "",
        "## Packaged Image Index",
        "",
        "The package includes actual benchmark images under `samples/images/`. The four contact sheets provide a quick visual index; individual files support closer inspection. The automatically selected paired records below can be different rows from these curated image examples.",
        "",
        "![Mammoth and OCR examples](../samples/images/01_mammoth_and_ocr.jpg)",
        "",
        "![Reverse-image candidates](../samples/images/02_reverse_candidates.jpg)",
        "",
        "![Cultural Focus examples](../samples/images/03_cultural_focus.jpg)",
        "",
        "![H400 and HS100 examples](../samples/images/04_h400_hs100.jpg)",
        "",
        "## Mammoth Heritage and OCR",
        "",
    ]
    for key, pair in data["mammoth"].items():
        title, description = MAMMOTH_DESC[key]
        render_pair(lines, title, description, pair)
    lines.extend(("## Cultural Focus", ""))
    cultural_desc = {
        "identity": "Held-out view에서 exact official title을 자유 생성한다.",
        "view_caption": "문화재 view 설명과 촬영년도까지 포함한 canonical caption 일치를 본다.",
        "national_treasure": "Cultural Focus identity 중 국보 subset의 exact-name 성능을 본다.",
    }
    for key, pair in data["cultural_focus"].items():
        render_pair(lines, f"Cultural Focus {key}", cultural_desc[key], pair)
    lines.extend(("## H400 and HS100", ""))
    for key, pair in data["target"].items():
        title, description = TARGET_DESC[key]
        render_pair(lines, title, description, pair)
    lines.extend(("## General Vision-Language", ""))
    for key, pair in data["general_vl"].items():
        render_vl(lines, key, pair)
    lines.extend(("## OpenCompass Language", ""))
    for key, pair in data["opencompass"].items():
        render_oc(lines, key, pair)
    lines.extend(("## Stateful Tool Use", ""))
    for suite in ("tau2", "tau3"):
        for domain, pair in data[suite].items():
            render_sim(lines, suite.upper(), domain, pair)
    lines.extend((
        "## BFCL and ToolSandbox example retention note",
        "",
        "BFCL's retained run folder contains category score CSVs and logs, not the raw per-query generation files. Its log records empty outputs in some missing-parameter/missing-function multi-turn cases; the main report includes the resulting category scores. ToolSandbox retained scenario-level milestone/minefield mappings but not a compact human-readable conversation transcript in `result_summary.json`. Tau2/Tau3 above provide the auditable stateful conversation examples.",
        "",
    ))
    return "\n".join(lines)


def main() -> None:
    guide = benchmark_guide()
    for key, spec in SPECS.items():
        target = RELEASE_ROOT / spec["slug"]
        reports = target / "reports"
        samples = target / "samples"
        reproduction = target / "reproduction"
        reports.mkdir(parents=True, exist_ok=True)
        samples.mkdir(parents=True, exist_ok=True)
        reproduction.mkdir(parents=True, exist_ok=True)

        data = json.loads(spec["examples"].read_text(encoding="utf-8"))
        (target / "README.md").write_text(readme(spec), encoding="utf-8")
        shutil.copy2(spec["score_report"], reports / "DETAILED_SCORE_REPORT.md")
        (reports / "BENCHMARK_GUIDE.md").write_text(guide, encoding="utf-8")
        (reports / "PAIRED_OUTPUT_EXAMPLES.md").write_text(
            build_examples(spec, data), encoding="utf-8"
        )
        shutil.copy2(spec["examples"], samples / "paired_examples.json")

        training_yaml = (
            ROOT.parent / "kubectl_yml/sft_qwen35_27b_official_h400_hs100_scaleup_2500steps_16nodes.yaml"
            if key == "qwen27b"
            else ROOT.parent / "kubectl_yml/sft_hyperclovax_seed_think_32b_h400_hs100_scaleup_2500steps_16nodes.yaml"
        )
        shutil.copy2(training_yaml, reports / "TRAINING_CONFIG.yaml")
        for script in (
            ROOT / "scripts/extract_large_model_paired_examples.py",
            ROOT / "scripts/package_hf_release_v2.py",
            ROOT / "scripts/convert_hf_safetensors_to_bf16.py",
            Path(__file__),
        ):
            shutil.copy2(script, reproduction / script.name)
        print(target)


if __name__ == "__main__":
    main()
