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


