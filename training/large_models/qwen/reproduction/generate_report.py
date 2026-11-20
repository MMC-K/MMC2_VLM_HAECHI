#!/usr/bin/env python3
"""Generate the complete official-vs-tuned Qwen3.5-27B benchmark report."""

from __future__ import annotations

import csv
import io
import json
import os
import subprocess
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "reports/qwen35_27b_official_vs_v28cl_9b_recipe_full_20260902.md"
JSON_OUTPUT = ROOT / "results/qwen35_27b_official_vs_v28cl_9b_recipe_full_20260902.json"
CSV_OUTPUT = ROOT / "results/qwen35_27b_official_vs_v28cl_9b_recipe_full_20260902.csv"
KUBECONFIG = os.environ.get(
    "KUBECONFIG", str(ROOT.parent / "keti-airc-h200-128-kubeconfig.yaml")
)
NAMESPACE = "p-keti-airc-h200-128"
POD = "upload-pod-san"
CONTAINER = "uploader"

BASE_LABEL = "Official Qwen3.5-27B"
TUNED_LABEL = "27B v28cl + 9B heritage recipe"
BASE_MODEL = "/data/workspace/post-training/outputs/qwen35-27b-official"
TUNED_MODEL = "/data/workspace/post-training/outputs/qwen35-27b-v28cl-h400-hs100-scale2500-step2500-hf"

OC_PATHS = {
    "Core": (
        "/data/workspace/eval_models/test/outputs/oc_all_q35-27b-official-20260901r2full/20260901_113253/summary/summary_20260901_113253.csv",
        "/data/workspace/eval_models/test/outputs/oc_all_q35-27b-v28cl-hs25-20260902r1/20260902_082336/summary/summary_20260902_082336.csv",
    ),
    "Extra": (
        "/data/workspace/eval_models/test/outputs/oc_extra_registered_q35-27b-official-20260901r2full/20260901_113255/summary/summary_20260901_113255.csv",
        "/data/workspace/eval_models/test/outputs/oc_extra_registered_q35-27b-v28cl-hs25-20260902r1/20260902_082339/summary/summary_20260902_082339.csv",
    ),
    "Korean": (
        "/data/workspace/eval_models/test/outputs/oc_korean_hf_q35-27b-official-20260901r2full/20260901_113257/summary/summary_20260901_113257.csv",
        "/data/workspace/eval_models/test/outputs/oc_korean_hf_q35-27b-v28cl-hs25-20260902r1/20260902_082346/summary/summary_20260902_082346.csv",
    ),
}

VL_RUNS = {
    "base": (
        "/data/workspace/eval_models/test/outputs/vlmeval-q35-27b-official-20260827/"
        "qwen35-27b-official/T20260827-141946",
        "qwen35-27b-official",
    ),
    "tuned": (
        "/data/workspace/eval_models/test/outputs/vlmeval-q35-27b-v28cl-hs25-20260902r1/"
        "qwen35-27b-v28cl-h400-hs100-scale2500/T20260902-082323",
        "qwen35-27b-v28cl-h400-hs100-scale2500",
    ),
}

MAMMOTH_ROOTS = (
    "/data/workspace/eval_models/mammoth_six_eval/q35-27b-official-20260827",
    "/data/workspace/eval_models/mammoth_six_eval/q35-27b-v28cl-hs25-20260902r1",
)
MAMMOTH_SOURCES = (
    "heritage_multi_attr",
    "heritage_reverse_mt",
    "heritage_simple",
    "ocr_font",
    "ocr_outdoor",
    "ocr_public_exec",
)

TITLE_ROOTS = (
    "/data/workspace/eval_models/cultural_heritage_focus_eval/qwen35_27b_official_20260827/base/summary.json",
    "/data/workspace/eval_models/cultural_heritage_focus_eval/q35-27b-v28cl-hs25-20260902r1/summary.json",
)
TARGET_ROOTS = (
    "/data/workspace/eval_models/heritage_h400_hs100_model_compare/qwen35-27b-official-20260901/target_summary.json",
    "/data/workspace/eval_models/heritage_h400_hs100_model_compare/qwen35-27b-v28cl-hs25-20260902r1/target_summary.json",
)
BFCL_ROOTS = (
    "/data/workspace/eval_models/bfcl/runs/q35-27b-official-20260827/score",
    "/data/workspace/eval_models/bfcl/runs/q35-27b-v28cl-hs25-20260902r1/score",
)
STATEFUL_ROOTS = (
    "/data/workspace/eval_models/stateful_tool_axes/q35-27b-official-20260827",
    "/data/workspace/eval_models/stateful_tool_axes/q35-27b-v28cl-hs25-20260902r1",
)
TAU3_ROOTS = (
    "/data/workspace/eval_models/tau3_axes/q35-27b-official-20260901r2full",
    "/data/workspace/eval_models/tau3_axes/q35-27b-v28cl-hs25-20260902r1-full",
)


def kubectl(*args: str) -> str:
    command = [
        "kubectl",
        "--kubeconfig",
        KUBECONFIG,
        "-n",
        NAMESPACE,
        "exec",
        POD,
        "-c",
        CONTAINER,
        "--",
        *args,
    ]
    return subprocess.run(command, check=True, text=True, capture_output=True).stdout


def remote_text(path: str) -> str:
    return kubectl("cat", path)


def remote_json(path: str) -> dict:
    return json.loads(remote_text(path))


def remote_find(root: str, name: str) -> str:
    paths = sorted(
        line
        for line in kubectl("find", root, "-type", "f", "-name", name, "-print").splitlines()
        if line
    )
    if len(paths) != 1:
        raise RuntimeError(f"Expected one {name} below {root}, found {paths}")
    return paths[0]


def number(value: str):
    value = value.strip().removesuffix("%")
    try:
        return float(value)
    except ValueError:
        return None


def fmt(value: float | None, digits: int = 2) -> str:
    return "-" if value is None else f"{value:.{digits}f}"


def comparison_table(
    rows: list[tuple[str, float | None, float | None]],
    *,
    digits: int = 2,
    unit: str = "%",
    delta_unit: str | None = None,
    lower_is_better: bool = False,
) -> list[str]:
    lines = [
        "| Benchmark | Official Base | Tuned | Delta | Direction |",
        "|---|---:|---:|---:|:---:|",
    ]
    direction = "lower" if lower_is_better else "higher"
    if delta_unit is None:
        delta_unit = " pp" if unit == "%" else unit
    for name, base, tuned in rows:
        change = None if base is None or tuned is None else tuned - base
        lines.append(
            f"| {name} | {fmt(base, digits)}{unit} | {fmt(tuned, digits)}{unit} | "
            f"{('-' if change is None else f'{change:+.{digits}f}')}{delta_unit} | {direction} |"
        )
    return lines


def section(
    lines: list[str],
    title: str,
    rows: list[tuple[str, float | None, float | None]],
    **kwargs,
) -> None:
    lines.extend((f"## {title}", "", *comparison_table(rows, **kwargs), ""))


def csv_rows(path: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(remote_text(path))))


def opencompass_rows(base_path: str, tuned_path: str):
    def parse(path: str):
        scores = []
        for row in csv.reader(io.StringIO(remote_text(path))):
            if not row or row[0] == "dataset" or not row[0].strip():
                continue
            score = number(row[-1])
            if score is not None:
                scores.append((row[0].strip(), score))
        return scores

    base = parse(base_path)
    tuned = dict(parse(tuned_path))
    return [(name, score, tuned.get(name)) for name, score in base]


def vl_rows():
    result = []
    for dataset in (
        "MMBench_DEV_EN_V11",
        "MMStar",
        "MMStar_KO",
        "KRETA",
        "MMMU_Pro_10c",
    ):
        values = []
        for key in ("base", "tuned"):
            root, model = VL_RUNS[key]
            row = csv_rows(f"{root}/{model}_{dataset}_acc.csv")[0]
            values.append(100 * float(row["Overall"]))
        result.append((dataset, *values))
    values = []
    for key in ("base", "tuned"):
        root, model = VL_RUNS[key]
        row = csv_rows(f"{root}/{model}_HallusionBench_score.csv")[0]
        values.append(float(row["aAcc"]))
    result.append(("HallusionBench aAcc", *values))
    result.insert(
        0,
        (
            "General-VL macro (6)",
            mean(row[1] for row in result),
            mean(row[2] for row in result),
        ),
    )
    return result


def mammoth_rows(metric: str, scale: float = 100.0):
    rows = []
    for source in MAMMOTH_SOURCES:
        values = []
        for root in MAMMOTH_ROOTS:
            data = remote_json(f"{root}/{source}/summary.json")["sources"][source]
            values.append(scale * float(data[metric]))
        rows.append((source, *values))
    return [
        ("Heritage macro (3)", mean(row[1] for row in rows[:3]), mean(row[2] for row in rows[:3])),
        ("OCR macro (3)", mean(row[1] for row in rows[3:]), mean(row[2] for row in rows[3:])),
        *rows,
    ]


def title_rows():
    base = remote_json(TITLE_ROOTS[0])["groups"]
    tuned = remote_json(TITLE_ROOTS[1])["groups"]
    rows = []
    for group in ("overall", "identity", "view_caption", "national_treasure", "other"):
        if group not in base or group not in tuned:
            continue
        for metric, label in (
            ("exact_accuracy", "exact"),
            ("containment_accuracy", "containment"),
            ("mean_similarity", "similarity"),
            ("identity_any_exact", "identity-any exact"),
        ):
            if metric in base[group] and metric in tuned[group]:
                rows.append(
                    (f"{group} / {label}", 100 * base[group][metric], 100 * tuned[group][metric])
                )
    return rows


def target_rows():
    base = remote_json(TARGET_ROOTS[0])
    tuned = remote_json(TARGET_ROOTS[1])
    specs = (
        ("h400_direct", "H400 direct exact", "exact_accuracy"),
        ("h400_hard", "H400 hard choice", "choice_accuracy"),
        ("h400_knowledge_image", "H400 knowledge image", "mean_similarity"),
        ("h400_knowledge_text", "H400 knowledge text", "mean_similarity"),
        ("hs100_train", "HS100 train exact", "exact_accuracy"),
        ("hs100_unseen", "HS100 unseen exact", "exact_accuracy"),
        ("hs100_simple", "HS100 Simple exact", "exact_accuracy"),
    )
    return [
        (label, 100 * base[key][metric], 100 * tuned[key][metric])
        for key, label, metric in specs
    ]


def bfcl_rows():
    base = csv_rows(f"{BFCL_ROOTS[0]}/data_overall.csv")[0]
    tuned = csv_rows(f"{BFCL_ROOTS[1]}/data_overall.csv")[0]
    wanted = (
        "Overall Acc",
        "Non-Live AST Acc",
        "Non-Live Simple AST",
        "Non-Live Multiple AST",
        "Non-Live Parallel AST",
        "Non-Live Parallel Multiple AST",
        "Multi Turn Acc",
        "Multi Turn Base",
        "Multi Turn Miss Func",
        "Multi Turn Miss Param",
        "Multi Turn Long Context",
    )
    return [(name, number(base.get(name, "")), number(tuned.get(name, ""))) for name in wanted]
