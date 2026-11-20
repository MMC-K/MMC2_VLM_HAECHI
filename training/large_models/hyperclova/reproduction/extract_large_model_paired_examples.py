#!/usr/bin/env python3
"""Extract compact paired Base/Tuned examples from remote evaluation artifacts."""

from __future__ import annotations

import argparse
import glob
import json
import re
import zipfile
from xml.etree import ElementTree
from pathlib import Path
from typing import Any, Iterable


MODELS = {
    "qwen27b": {
        "labels": ["Official Qwen3.5-27B", "Qwen3.5-27B tuned"],
        "mammoth": [
            "/data/workspace/eval_models/mammoth_six_eval/q35-27b-official-20260827",
            "/data/workspace/eval_models/mammoth_six_eval/q35-27b-h400-hs100-s2500-20260831",
        ],
        "cultural": [
            "/data/workspace/eval_models/cultural_heritage_focus_eval/qwen35_27b_official_20260827/base",
            "/data/workspace/eval_models/cultural_heritage_focus_eval/q35-27b-h400-hs100-s2500-20260831",
        ],
        "target": [
            "/data/workspace/eval_models/heritage_h400_hs100_model_compare/qwen35-27b-official-20260901",
            "/data/workspace/eval_models/heritage_h400_hs100_model_compare/qwen35-27b-tuned-20260901",
        ],
        "vl": [
            [
                "/data/workspace/eval_models/test/outputs/vlmeval-q35-27b-official-20260827/qwen35-27b-official/T20260827-141946",
                "qwen35-27b-official",
            ],
            [
                "/data/workspace/eval_models/test/outputs/vlmeval-q35-27b-h400-hs100-s2500-20260831/qwen35-27b-h400-hs100-scale2500/T20260831-150649",
                "qwen35-27b-h400-hs100-scale2500",
            ],
        ],
        "opencompass": {
            "core": [
                "/data/workspace/eval_models/test/outputs/oc_all_q35-27b-official-20260901r2full/20260901_113253",
                "/data/workspace/eval_models/test/outputs/oc_all_q35-27b-h400-hs100-s2500-20260831/20260831_150703",
            ],
            "extra": [
                "/data/workspace/eval_models/test/outputs/oc_extra_registered_q35-27b-official-20260901r2full/20260901_113255",
                "/data/workspace/eval_models/test/outputs/oc_extra_registered_q35-27b-h400-hs100-s2500-20260831/20260831_150701",
            ],
            "korean": [
                "/data/workspace/eval_models/test/outputs/oc_korean_hf_q35-27b-official-20260901r2full/20260901_113257",
                "/data/workspace/eval_models/test/outputs/oc_korean_hf_q35-27b-h400-hs100-s2500-20260831/20260831_150704",
            ],
        },
        "tau2": [
            "/data/workspace/eval_models/stateful_tool_axes/q35-27b-official-20260827",
            "/data/workspace/eval_models/stateful_tool_axes/q35-27b-h400-hs100-s2500-20260831",
        ],
        "tau3": [
            "/data/workspace/eval_models/tau3_axes/q35-27b-official-20260901r2full",
            "/data/workspace/eval_models/tau3_axes/q35-27b-h400-hs100-s2500-20260831",
        ],
    },
    "hcx32b": {
        "labels": ["Official HyperCLOVAX-SEED-Think-32B", "HCX 32B tuned"],
        "mammoth": [
            "/data/workspace/eval_models/mammoth_six_eval/hcx32b-official-base-20260901",
            "/data/workspace/eval_models/mammoth_six_eval/hcx32b-h400-hs100-s2500-20260901r3full",
        ],
        "cultural": [
            "/data/workspace/eval_models/cultural_heritage_focus_eval/hcx32b-official-base-20260901",
            "/data/workspace/eval_models/cultural_heritage_focus_eval/hcx32b-h400-hs100-s2500-20260901r3full",
        ],
        "target": [
            "/data/workspace/eval_models/heritage_h400_hs100_model_compare/hcx32b-official-20260901r2compat",
            "/data/workspace/eval_models/heritage_h400_hs100_model_compare/hcx32b-tuned-20260901",
        ],
        "vl": [
            [
                "/data/workspace/eval_models/test/outputs/vlmeval-hcx32b-official-base-20260901/hyperclovax-seed-think-32b-official-evalcompat/T20260901-083848",
                "hyperclovax-seed-think-32b-official-evalcompat",
            ],
            [
                "/data/workspace/eval_models/test/outputs/vlmeval-hcx32b-h400-hs100-s2500-20260901r2/hyperclovax-seed-think-32b-h400-hs100-scale2500/T20260901-054200",
                "hyperclovax-seed-think-32b-h400-hs100-scale2500",
            ],
        ],
        "opencompass": {
            "core": [
                "/data/workspace/eval_models/test/outputs/oc_all_hcx32b-official-base-20260901r2fixed/20260901_092808",
                "/data/workspace/eval_models/test/outputs/oc_all_hcx32b-h400-hs100-s2500-20260901r4fixed/20260901_065152",
            ],
            "extra": [
                "/data/workspace/eval_models/test/outputs/oc_extra_registered_hcx32b-official-base-20260901r2fixed/20260901_092809",
                "/data/workspace/eval_models/test/outputs/oc_extra_registered_hcx32b-h400-hs100-s2500-20260901r4fixed/20260901_065152",
            ],
            "korean": [
                "/data/workspace/eval_models/test/outputs/oc_korean_hf_hcx32b-official-base-20260901r2fixed/20260901_092804",
                "/data/workspace/eval_models/test/outputs/oc_korean_hf_hcx32b-h400-hs100-s2500-20260901r4fixed/20260901_065149",
            ],
        },
        "tau2": [
            "/data/workspace/eval_models/stateful_tool_axes/hcx32b-official-base-20260901",
            "/data/workspace/eval_models/stateful_tool_axes/hcx32b-h400-hs100-s2500-20260901r2",
        ],
        "tau3": [
            "/data/workspace/eval_models/tau3_axes/hcx32b-official-base-20260901r2",
            "/data/workspace/eval_models/tau3_axes/hcx32b-h400-hs100-s2500-20260901r2",
        ],
    },
}

MAMMOTH = [
    "heritage_multi_attr",
    "heritage_reverse_mt",
    "heritage_simple",
    "ocr_font",
    "ocr_outdoor",
    "ocr_public_exec",
]
TARGET = {
    "h400_direct": "h400/heritage_h400_direct/predictions.jsonl",
    "h400_hard": "h400/heritage_h400_hard_negative/predictions.jsonl",
    "h400_knowledge_image": "h400/heritage_h400_knowledge_image/predictions.jsonl",
    "h400_knowledge_text": "h400/heritage_h400_knowledge_text/predictions.jsonl",
    "hs100_train": "hs100/train_recall/predictions.jsonl",
    "hs100_unseen": "hs100/heldout_refine/predictions.jsonl",
    "hs100_simple": "hs100/benchmark_simple/predictions.jsonl",
}
OC_PATTERNS = {
    "core": ["aime2024", "bbh-date_understanding", "gpqa", "mmlu_pro", "humaneval", "ifeval"],
    "extra": ["arc_c", "boolq", "commonsense", "gsm8k", "math", "mbpp", "drop", "nq"],
    "korean": ["kmmlu", "csatqa", "hae", "kobest", "kobalt", "clinical"],
}
VL_DATASETS = [
    "MMBench_DEV_EN_V11",
    "MMStar",
    "MMStar_KO",
    "KRETA",
    "MMMU_Pro_10c",
    "HallusionBench",
    "MathVista_MINI",
]


def read_jsonl(path: str) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def keyed(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("sample_id", row.get("id", row.get("row_index")))): row for row in rows}


def correctness(row: dict[str, Any]) -> float:
    for key in ("exact", "normalized_exact", "choice_correct"):
        if key in row:
            return float(bool(row[key]))
    return float(row.get("similarity", 0.0))


def sanitize_source(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: sanitize_source(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_source(item) for item in value]
    if isinstance(value, str):
        if value.startswith("data:image/"):
            return "<embedded image omitted; packaged sample image is provided separately>"
        if len(value) > 10_000:
            return value[:2_000] + f"... <{len(value) - 2_000} characters omitted>"
    return value


def compact(row: dict[str, Any]) -> dict[str, Any]:
    wanted = (
        "sample_id", "task_type", "question_category", "question", "gold_response",
        "gold_target", "prediction", "predicted_target", "exact", "normalized_exact",
        "contains", "similarity", "choice_correct", "finish_reason", "source_file",
        "line_offset", "row_index",
    )
    result = {key: row[key] for key in wanted if key in row}
    source_file = row.get("source_file")
    offset = row.get("line_offset")
    if source_file and offset is not None and Path(source_file).is_file():
        try:
            with open(source_file, "rb") as stream:
                stream.seek(int(offset))
                source = json.loads(stream.readline().decode("utf-8"))
            result["source_record"] = sanitize_source(source)
        except Exception as exc:  # source offsets are provenance aids, not required data
            result["source_record_error"] = repr(exc)
    return result
