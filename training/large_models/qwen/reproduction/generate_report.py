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


def toolsandbox_rows():
    scores = []
    counts = []
    for root in STATEFUL_ROOTS:
        path = remote_find(f"{root}/toolsandbox32", "result_summary.json")
        data = remote_json(path)
        scores.append(data["category_aggregated_results"]["ALL_CATEGORIES"]["similarity"])
        counts.append(len(data["per_scenario_results"]))
    if counts[0] != counts[1]:
        raise RuntimeError(f"ToolSandbox count mismatch: {counts}")
    return [(f"ToolSandbox similarity (n={counts[0]})", *scores)]


def simulation_rows(roots: tuple[str, str], domains: tuple[tuple[str, str], ...]):
    rows = []
    totals = [[0.0, 0], [0.0, 0]]
    for label, directory in domains:
        values = []
        counts = []
        for index, root in enumerate(roots):
            path = remote_find(f"{root}/{directory}", "results.json")
            simulations = remote_json(path)["simulations"]
            rewards = [float(row.get("reward_info", {}).get("reward", 0.0)) for row in simulations]
            values.append(100 * sum(rewards) / len(rewards))
            counts.append(len(rewards))
            totals[index][0] += sum(rewards)
            totals[index][1] += len(rewards)
        if counts[0] != counts[1]:
            raise RuntimeError(f"{label} count mismatch: {counts}")
        rows.append((f"{label} (n={counts[0]})", *values))
    rows.append(
        (
            f"Weighted overall (n={totals[0][1]})",
            100 * totals[0][0] / totals[0][1],
            100 * totals[1][0] / totals[1][1],
        )
    )
    rows.append(("Domain macro", mean(row[1] for row in rows[:-1]), mean(row[2] for row in rows[:-1])))
    return rows


def json_rows(rows, *, lower_is_better: bool = False):
    result = []
    for name, base, tuned in rows:
        delta = None if base is None or tuned is None else tuned - base
        result.append(
            {
                "benchmark": name,
                "official_base": base,
                "tuned": tuned,
                "delta": delta,
                "higher_is_better": not lower_is_better,
            }
        )
    return result


def main() -> None:
    general_vl = vl_rows()
    mammoth_exact = mammoth_rows("exact_accuracy")
    mammoth_containment = mammoth_rows("target_containment")
    mammoth_similarity = mammoth_rows("mean_similarity")
    mammoth_cer = mammoth_rows("mean_cer", scale=1.0)
    mammoth_line_recall = mammoth_rows("mean_line_recall")
    cultural_title = title_rows()
    target = target_rows()
    opencompass = {
        title: opencompass_rows(*paths) for title, paths in OC_PATHS.items()
    }
    bfcl = bfcl_rows()
    toolsandbox = toolsandbox_rows()
    tau2 = simulation_rows(
        STATEFUL_ROOTS,
        (("Tau2 airline", "tau2/airline"), ("Tau2 retail", "tau2/retail"), ("Tau2 telecom", "tau2/telecom")),
    )
    tau3 = simulation_rows(
        TAU3_ROOTS,
        (
            ("Tau3 airline", "airline"),
            ("Tau3 retail", "retail"),
            ("Tau3 telecom", "telecom"),
            ("Tau3 banking knowledge", "banking_knowledge"),
        ),
    )
    summary = [
        general_vl[0],
        mammoth_exact[0],
        mammoth_exact[1],
        next(row for row in mammoth_exact if row[0] == "heritage_simple"),
        next(row for row in target if row[0] == "H400 direct exact"),
        next(row for row in target if row[0] == "H400 hard choice"),
        opencompass["Core"][0],
        opencompass["Extra"][0],
        opencompass["Korean"][0],
        bfcl[0],
        tau2[-2],
        tau3[-2],
    ]
    sections = [
        ("general_multimodal", "General multimodal", general_vl, False, "%"),
        ("mammoth_exact", "Mammoth exact accuracy", mammoth_exact, False, "%"),
        ("mammoth_containment", "Mammoth target containment", mammoth_containment, False, "%"),
        ("mammoth_similarity", "Mammoth normalized similarity", mammoth_similarity, False, "%"),
        ("mammoth_cer", "Mammoth OCR CER", mammoth_cer, True, ""),
        ("mammoth_line_recall", "Mammoth OCR line recall", mammoth_line_recall, False, "%"),
        ("cultural_title", "Cultural heritage title-clean", cultural_title, False, "%"),
        ("heritage_targets", "H400/HS100 target gates", target, False, "%"),
        ("bfcl", "BFCL V4", bfcl, False, "%"),
        ("toolsandbox", "ToolSandbox", toolsandbox, False, ""),
        ("tau2", "Tau2", tau2, False, "%"),
        ("tau3", "Tau3", tau3, False, "%"),
    ]
    sections[8:8] = [
        (f"opencompass_{name.lower()}", f"OpenCompass {name}", rows, False, "%")
        for name, rows in opencompass.items()
    ]

    ranked = []
    for _, title, rows, lower_is_better, unit in sections:
        for name, base, tuned in rows:
            if base is None or tuned is None:
                continue
            delta = tuned - base
            benefit = -delta if lower_is_better else delta
            ranked.append((benefit, title, name, delta, unit, lower_is_better))
    top_gains = sorted(ranked, reverse=True)[:10]
    top_regressions = sorted(ranked)[:10]

    lines = [
        "# Qwen3.5-27B Official Base vs v28cl + 9B Heritage Recipe",
        "",
        "Comparison generated: 2026-09-02 (Asia/Seoul).",
        "",
        "## Contract",
        "",
        f"- Official base: `{BASE_MODEL}` (untouched official `Qwen/Qwen3.5-27B` weights).",
        f"- Tuned: `{TUNED_MODEL}`.",
        "- All deltas are tuned minus official base. Percentage metrics use absolute percentage points.",
        "- OpenCompass uses the same API, thinking, stop-token, parser, and dataset configuration for both models.",
        "- Tau3 uses four trials per task and identical BM25/tool simulation settings.",
        "- The tuned lineage follows the successful 9B heritage recipe: v28cl parent, specialist/task-vector transfer, H400/H300 acquisition, then H400/HS100 scale-up.",
        "",
        "## Executive summary",
        "",
        *comparison_table(summary),
        "",
    ]

    for _, title, rows, lower_is_better, unit in sections:
        section(
            lines,
            title,
            rows,
            digits=4 if title in ("Mammoth OCR CER", "ToolSandbox") else 2,
            unit=unit,
            lower_is_better=lower_is_better,
        )

    lines.extend(
        (
            "## Largest improvements",
            "",
            *(
                f"- {title} / {name}: {delta:+.2f}{' pp' if unit == '%' else ''}"
                for _, title, name, delta, unit, _ in top_gains
            ),
            "",
            "## Largest regressions",
            "",
            *(
                f"- {title} / {name}: {delta:+.2f}{' pp' if unit == '%' else ''}"
                for _, title, name, delta, unit, _ in top_regressions
            ),
            "",
            "## Reading the result",
            "",
            "- H400 direct exact measures open-ended canonical-name retrieval; H400 hard measures closed-set choice. A large gap between them indicates recognition/discrimination is stronger than exact name generation.",
            "- HS100 train, unseen, and Simple distinguish memorization, held-out view generalization, and transfer to a separate simple-identification population. They are not interchangeable with Mammoth Heritage Simple.",
            "- Mammoth exact is strict. Containment and normalized similarity show whether an answer is usable but differs in annotation, spacing, aliases, or added explanation.",
            "- OCR CER is the only lower-is-better metric in this report; all other deltas are better when positive.",
            "- OpenCompass, General-VL, BFCL, ToolSandbox, Tau2, and Tau3 are retention gates. Improvements in heritage should be interpreted together with these broad-capability deltas.",
            "",
            "## Source locations",
            "",
            "- Official OpenCompass: `/data/workspace/eval_models/test/outputs/*q35-27b-official-20260901r2full`",
            "- Tuned OpenCompass: `/data/workspace/eval_models/test/outputs/*q35-27b-v28cl-hs25-20260902r1`",
            "- Official Tau3: `/data/workspace/eval_models/tau3_axes/q35-27b-official-20260901r2full`",
            "- Tuned Tau3: `/data/workspace/eval_models/tau3_axes/q35-27b-v28cl-hs25-20260902r1-full`",
            "",
        )
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    JSON_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT.write_text(
        json.dumps(
            {
                "generated_at": "2026-09-02 Asia/Seoul",
                "official_base": {"label": BASE_LABEL, "model": BASE_MODEL},
                "tuned": {"label": TUNED_LABEL, "model": TUNED_MODEL},
                "sections": {
                    key: {
                        "title": title,
                        "unit": unit,
                        "rows": json_rows(rows, lower_is_better=lower_is_better),
                    }
                    for key, title, rows, lower_is_better, unit in sections
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    CSV_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ("section", "benchmark", "official_base", "tuned", "delta", "unit", "higher_is_better")
        )
        for _, title, rows, lower_is_better, unit in sections:
            for name, base, tuned in rows:
                delta = None if base is None or tuned is None else tuned - base
                writer.writerow((title, name, base, tuned, delta, unit, not lower_is_better))
    print(OUTPUT)
    print(JSON_OUTPUT)
    print(CSV_OUTPUT)
