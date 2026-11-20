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


def choose_pair(base_rows: list[dict[str, Any]], tuned_rows: list[dict[str, Any]]) -> dict[str, Any]:
    base = keyed(base_rows)
    tuned = keyed(tuned_rows)
    common = sorted(base.keys() & tuned.keys())
    if not common:
        raise RuntimeError("No paired sample IDs")
    ranked = sorted(
        common,
        key=lambda key: (
            correctness(tuned[key]) - correctness(base[key]),
            correctness(tuned[key]),
            base[key].get("similarity", 0.0) != tuned[key].get("similarity", 0.0),
        ),
        reverse=True,
    )
    key = ranked[0]
    return {"pair_key": key, "base": compact(base[key]), "tuned": compact(tuned[key])}


def collect_cultural(roots: list[str]) -> dict[str, Any]:
    pairs = []
    for root in roots:
        rows = []
        for path in sorted(glob.glob(f"{root}/shard_*/predictions.jsonl")):
            rows.extend(read_jsonl(path))
        pairs.append(rows)
    result = {}
    for label, predicate in {
        "identity": lambda row: row.get("task_type") == "heritage_identity" or row.get("question_category") == "identity",
        "view_caption": lambda row: row.get("task_type") == "heritage_view_caption" or row.get("question_category") == "view_caption",
        "national_treasure": lambda row: bool(row.get("is_national_treasure")) or row.get("heritage_grade") == "국보",
    }.items():
        left = [row for row in pairs[0] if predicate(row)]
        right = [row for row in pairs[1] if predicate(row)]
        if left and right:
            result[label] = choose_pair(left, right)
    return result


def flatten_prompt(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(flatten_prompt(item) for item in value)
    if isinstance(value, dict):
        return str(value.get("prompt", value.get("content", value)))
    return str(value)


def oc_records(path: str) -> dict[str, dict[str, Any]]:
    data = json.load(open(path, encoding="utf-8"))
    return {str(key): value for key, value in data.items()}


def compact_oc(row: dict[str, Any]) -> dict[str, Any]:
    result = {
        "prompt": flatten_prompt(row.get("origin_prompt", row.get("prompt", "")))[:3000],
        "prediction": str(row.get("prediction", ""))[:5000],
    }
    for key in ("gold", "reference", "answer", "label"):
        if key in row:
            result[key] = row[key]
    return result


def collect_opencompass(roots: dict[str, list[str]]) -> dict[str, Any]:
    output = {}
    for suite, patterns in OC_PATTERNS.items():
        base_files = glob.glob(f"{roots[suite][0]}/predictions/*/*.json")
        tuned_files = glob.glob(f"{roots[suite][1]}/predictions/*/*.json")
        tuned_by_name = {Path(path).name: path for path in tuned_files}
        for pattern in patterns:
            candidates = sorted(
                path for path in base_files
                if pattern.lower() in Path(path).name.lower() and Path(path).name in tuned_by_name
            )
            if not candidates:
                continue
            base_path = candidates[0]
            tuned_path = tuned_by_name[Path(base_path).name]
            base = oc_records(base_path)
            tuned = oc_records(tuned_path)
            common = sorted(base.keys() & tuned.keys())
            if not common:
                continue
            key = next(
                (key for key in common if base[key].get("prediction") != tuned[key].get("prediction")),
                common[0],
            )
            output[f"{suite}/{pattern}"] = {
                "source_file": Path(base_path).name,
                "sample_key": key,
                "base": compact_oc(base[key]),
                "tuned": compact_oc(tuned[key]),
            }
    return output


def xlsx_rows(path: str) -> list[dict[str, str]]:
    namespace = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    with zipfile.ZipFile(path) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall(f"{namespace}si"):
                shared.append("".join(node.text or "" for node in item.iter(f"{namespace}t")))
        sheet = ElementTree.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    table: list[list[str]] = []
    for row in sheet.iter(f"{namespace}row"):
        values: dict[int, str] = {}
        for cell in row.findall(f"{namespace}c"):
            reference = cell.attrib.get("r", "A1")
            letters = re.match(r"[A-Z]+", reference).group(0)
            column = 0
            for letter in letters:
                column = column * 26 + ord(letter) - ord("A") + 1
            column -= 1
            kind = cell.attrib.get("t")
            if kind == "inlineStr":
                value = "".join(node.text or "" for node in cell.iter(f"{namespace}t"))
            else:
                node = cell.find(f"{namespace}v")
                value = "" if node is None else (node.text or "")
                if kind == "s" and value:
                    value = shared[int(value)]
            values[column] = value
        if values:
            table.append([values.get(index, "") for index in range(max(values) + 1)])
    if not table:
        return []
    headers = table[0]
    return [
        {headers[index]: value for index, value in enumerate(row) if index < len(headers)}
        for row in table[1:]
    ]


def compact_vl(row: dict[str, str]) -> dict[str, str]:
    aliases = (
        "index", "category", "l2-category", "question", "hint", "A", "B", "C", "D",
        "answer", "prediction", "score", "judge", "res",
    )
    return {key: str(row[key])[:5000] for key in aliases if key in row and str(row[key]).strip()}


def collect_vl(roots: list[list[str]]) -> dict[str, Any]:
    output = {}
    for dataset in VL_DATASETS:
        paths = [f"{root}/{prefix}_{dataset}.xlsx" for root, prefix in roots]
        if not all(Path(path).is_file() for path in paths):
            continue
        rows = [xlsx_rows(path) for path in paths]
        if not rows[0] or not rows[1]:
            continue
        key_name = "index" if "index" in rows[0][0] else None
        if key_name:
            left = {str(row.get(key_name)): row for row in rows[0]}
            right = {str(row.get(key_name)): row for row in rows[1]}
            common = sorted(left.keys() & right.keys())
            key = next(
                (item for item in common if left[item].get("prediction") != right[item].get("prediction")),
                common[0],
            )
            base_row, tuned_row = left[key], right[key]
        else:
            index = next(
                (i for i, (left, right) in enumerate(zip(*rows)) if left.get("prediction") != right.get("prediction")),
                0,
            )
            key = str(index)
            base_row, tuned_row = rows[0][index], rows[1][index]
        output[dataset] = {
            "sample_key": key,
            "base": compact_vl(base_row),
            "tuned": compact_vl(tuned_row),
        }
    return output


def final_assistant(simulation: dict[str, Any]) -> dict[str, Any]:
    messages = simulation.get("messages", [])
    user = next((item.get("content", "") for item in messages if item.get("role") == "user"), "")
    assistants = [item for item in messages if item.get("role") == "assistant"]
    last = assistants[-1] if assistants else {}
    return {
        "task_id": simulation.get("task_id"),
        "reward": simulation.get("reward_info", {}).get("reward"),
        "user": str(user)[:2500],
        "final_assistant": str(last.get("content", ""))[:3500],
        "tool_calls": last.get("tool_calls"),
        "termination_reason": simulation.get("termination_reason"),
    }


def collect_simulation_pair(roots: list[str], suite: str, domain: str) -> dict[str, Any]:
    pattern = f"{roots[0]}/{suite}/{domain}/**/results.json" if suite == "tau2" else f"{roots[0]}/{domain}/**/results.json"
    tuned_pattern = f"{roots[1]}/{suite}/{domain}/**/results.json" if suite == "tau2" else f"{roots[1]}/{domain}/**/results.json"
    left_path = glob.glob(pattern, recursive=True)[0]
    right_path = glob.glob(tuned_pattern, recursive=True)[0]
    left = json.load(open(left_path, encoding="utf-8"))["simulations"]
    right = json.load(open(right_path, encoding="utf-8"))["simulations"]
    left_map = {str(row.get("task_id")): row for row in left}
    right_map = {str(row.get("task_id")): row for row in right}
    common = sorted(left_map.keys() & right_map.keys())
    key = max(
        common,
        key=lambda item: float(right_map[item].get("reward_info", {}).get("reward", 0))
        - float(left_map[item].get("reward_info", {}).get("reward", 0)),
    )
    return {"base": final_assistant(left_map[key]), "tuned": final_assistant(right_map[key])}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=sorted(MODELS), required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    spec = MODELS[args.model]

    data: dict[str, Any] = {"model": args.model, "labels": spec["labels"]}
    data["mammoth"] = {}
    for source in MAMMOTH:
        data["mammoth"][source] = choose_pair(
            read_jsonl(f"{spec['mammoth'][0]}/{source}/predictions.jsonl"),
            read_jsonl(f"{spec['mammoth'][1]}/{source}/predictions.jsonl"),
        )
    data["cultural_focus"] = collect_cultural(spec["cultural"])
    data["target"] = {}
    for label, relative in TARGET.items():
        data["target"][label] = choose_pair(
            read_jsonl(f"{spec['target'][0]}/{relative}"),
            read_jsonl(f"{spec['target'][1]}/{relative}"),
        )
    data["general_vl"] = collect_vl(spec["vl"])
    data["opencompass"] = collect_opencompass(spec["opencompass"])
    data["tau2"] = {
        domain: collect_simulation_pair(spec["tau2"], "tau2", domain)
        for domain in ("airline", "retail", "telecom")
    }
    data["tau3"] = {
        domain: collect_simulation_pair(spec["tau3"], "tau3", domain)
        for domain in ("airline", "retail", "telecom", "banking_knowledge")
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(args.output)
