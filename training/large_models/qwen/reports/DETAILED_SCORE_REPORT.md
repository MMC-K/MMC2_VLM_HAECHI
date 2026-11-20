# Qwen3.5-27B Official Base vs v28cl + 9B Heritage Recipe

Comparison generated: 2026-09-02 (Asia/Seoul).

## Contract

- Official base: `/data/workspace/post-training/outputs/qwen35-27b-official` (untouched official `Qwen/Qwen3.5-27B` weights).
- Tuned: `/data/workspace/post-training/outputs/qwen35-27b-v28cl-h400-hs100-scale2500-step2500-hf`.
- All deltas are tuned minus official base. Percentage metrics use absolute percentage points.
- OpenCompass uses the same API, thinking, stop-token, parser, and dataset configuration for both models.
- Tau3 uses four trials per task and identical BM25/tool simulation settings.
- The tuned lineage follows the successful 9B heritage recipe: v28cl parent, specialist/task-vector transfer, H400/H300 acquisition, then H400/HS100 scale-up.

## Executive summary

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| General-VL macro (6) | 45.44% | 77.60% | +32.16 pp | higher |
| Heritage macro (3) | 38.06% | 40.21% | +2.15 pp | higher |
| OCR macro (3) | 19.99% | 22.09% | +2.11 pp | higher |
| heritage_simple | 0.00% | 1.95% | +1.95 pp | higher |
| H400 direct exact | 0.92% | 38.07% | +37.16 pp | higher |
| H400 hard choice | 26.45% | 80.43% | +53.98 pp | higher |
| core_average | 63.49% | 64.80% | +1.31 pp | higher |
| extra_registered_average | 57.26% | 57.61% | +0.35 pp | higher |
| korean_hf_average | 17.18% | 16.77% | -0.41 pp | higher |
| Overall Acc | 32.77% | 32.11% | -0.66 pp | higher |
| Weighted overall (n=96) | 69.79% | 71.88% | +2.08 pp | higher |
| Weighted overall (n=1500) | 41.67% | 40.00% | -1.67 pp | higher |

## General multimodal

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| General-VL macro (6) | 45.44% | 77.60% | +32.16 pp | higher |
| MMBench_DEV_EN_V11 | 30.42% | 90.63% | +60.22 pp | higher |
| MMStar | 39.40% | 77.33% | +37.93 pp | higher |
| MMStar_KO | 45.20% | 72.33% | +27.13 pp | higher |
| KRETA | 48.54% | 86.15% | +37.60 pp | higher |
| MMMU_Pro_10c | 44.28% | 61.85% | +17.57 pp | higher |
| HallusionBench aAcc | 64.77% | 77.29% | +12.51 pp | higher |

## Mammoth exact accuracy

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| Heritage macro (3) | 38.06% | 40.21% | +2.15 pp | higher |
| OCR macro (3) | 19.99% | 22.09% | +2.11 pp | higher |
| heritage_multi_attr | 22.01% | 28.26% | +6.25 pp | higher |
| heritage_reverse_mt | 92.19% | 90.43% | -1.76 pp | higher |
| heritage_simple | 0.00% | 1.95% | +1.95 pp | higher |
| ocr_font | 19.66% | 19.66% | +0.00 pp | higher |
| ocr_outdoor | 36.13% | 41.41% | +5.27 pp | higher |
| ocr_public_exec | 4.17% | 5.21% | +1.04 pp | higher |

## Mammoth target containment

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| Heritage macro (3) | 44.51% | 43.53% | -0.98 pp | higher |
| OCR macro (3) | 32.47% | 32.68% | +0.22 pp | higher |
| heritage_multi_attr | 35.42% | 35.55% | +0.13 pp | higher |
| heritage_reverse_mt | 97.07% | 92.58% | -4.49 pp | higher |
| heritage_simple | 1.04% | 2.47% | +1.43 pp | higher |
| ocr_font | 20.96% | 20.70% | -0.26 pp | higher |
| ocr_outdoor | 70.70% | 70.70% | +0.00 pp | higher |
| ocr_public_exec | 5.73% | 6.64% | +0.91 pp | higher |

## Mammoth normalized similarity

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| Heritage macro (3) | 45.68% | 50.25% | +4.57 pp | higher |
| OCR macro (3) | 35.00% | 38.59% | +3.59 pp | higher |
| heritage_multi_attr | 39.14% | 44.36% | +5.22 pp | higher |
| heritage_reverse_mt | 92.20% | 90.43% | -1.77 pp | higher |
| heritage_simple | 5.70% | 15.95% | +10.25 pp | higher |
| ocr_font | 23.66% | 24.12% | +0.46 pp | higher |
| ocr_outdoor | 59.73% | 64.96% | +5.22 pp | higher |
| ocr_public_exec | 21.61% | 26.71% | +5.09 pp | higher |

## Mammoth OCR CER

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| Heritage macro (3) | 2.4569 | 0.6781 | -1.7788 | lower |
| OCR macro (3) | 1.5337 | 1.1192 | -0.4146 | lower |
| heritage_multi_attr | 0.7850 | 0.6776 | -0.1074 | lower |
| heritage_reverse_mt | 0.1016 | 0.0957 | -0.0059 | lower |
| heritage_simple | 6.4840 | 1.2608 | -5.2231 | lower |
| ocr_font | 1.4261 | 1.0366 | -0.3895 | lower |
| ocr_outdoor | 1.4172 | 0.9583 | -0.4589 | lower |
| ocr_public_exec | 1.7579 | 1.3625 | -0.3954 | lower |

## Mammoth OCR line recall

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| Heritage macro (3) | 44.51% | 43.53% | -0.98 pp | higher |
| OCR macro (3) | 32.47% | 32.68% | +0.22 pp | higher |
| heritage_multi_attr | 35.42% | 35.55% | +0.13 pp | higher |
| heritage_reverse_mt | 97.07% | 92.58% | -4.49 pp | higher |
| heritage_simple | 1.04% | 2.47% | +1.43 pp | higher |
| ocr_font | 20.96% | 20.70% | -0.26 pp | higher |
| ocr_outdoor | 70.70% | 70.70% | +0.00 pp | higher |
| ocr_public_exec | 5.73% | 6.64% | +0.91 pp | higher |

## Cultural heritage title-clean

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| overall / exact | 0.17% | 2.64% | +2.47 pp | higher |
| overall / containment | 1.11% | 3.05% | +1.94 pp | higher |
| overall / similarity | 7.25% | 11.11% | +3.86 pp | higher |
| overall / identity-any exact | 0.31% | 4.19% | +3.89 pp | higher |
| identity / exact | 0.46% | 6.89% | +6.43 pp | higher |
| identity / containment | 0.70% | 7.28% | +6.58 pp | higher |
| identity / similarity | 13.16% | 19.93% | +6.77 pp | higher |
| identity / identity-any exact | 0.62% | 7.81% | +7.19 pp | higher |
| view_caption / exact | 0.00% | 0.26% | +0.26 pp | higher |
| view_caption / containment | 1.34% | 0.69% | -0.65 pp | higher |
| view_caption / similarity | 3.96% | 6.19% | +2.24 pp | higher |
| view_caption / identity-any exact | 0.00% | 0.40% | +0.40 pp | higher |
| national_treasure / exact | 0.00% | 9.92% | +9.92 pp | higher |
| national_treasure / containment | 0.62% | 10.12% | +9.50 pp | higher |
| national_treasure / similarity | 11.47% | 22.91% | +11.44 pp | higher |
| national_treasure / identity-any exact | 0.00% | 12.10% | +12.10 pp | higher |
| other / exact | 0.19% | 1.51% | +1.31 pp | higher |
| other / containment | 1.19% | 1.96% | +0.77 pp | higher |
| other / similarity | 6.60% | 9.28% | +2.68 pp | higher |
| other / identity-any exact | 0.37% | 2.49% | +2.11 pp | higher |

## H400/HS100 target gates

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| H400 direct exact | 0.92% | 38.07% | +37.16 pp | higher |
| H400 hard choice | 26.45% | 80.43% | +53.98 pp | higher |
| H400 knowledge image | 11.45% | 25.30% | +13.85 pp | higher |
| H400 knowledge text | 5.97% | 6.28% | +0.31 pp | higher |
| HS100 train exact | 0.00% | 12.00% | +12.00 pp | higher |
| HS100 unseen exact | 0.50% | 7.43% | +6.93 pp | higher |
| HS100 Simple exact | 0.00% | 0.98% | +0.98 pp | higher |

## OpenCompass Core

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| core_average | 63.49% | 64.80% | +1.31 pp | higher |
| IFEval | 85.58% | 85.21% | -0.37 pp | higher |
| aime2024 | 30.00% | 26.67% | -3.33 pp | higher |
| aime2025 | 60.00% | 73.33% | +13.33 pp | higher |
| math_prm800k_500 | 86.80% | 89.00% | +2.20 pp | higher |
| bbh | 47.56% | 46.84% | -0.72 pp | higher |
| GPQA_diamond | 82.83% | 84.85% | +2.02 pp | higher |
| mmlu_pro | 85.55% | 85.57% | +0.02 pp | higher |
| openai_humaneval | 96.95% | 96.34% | -0.61 pp | higher |
| lcb_code_generation | 74.50% | 76.00% | +1.50 pp | higher |
| leval | 14.88% | 15.00% | +0.12 pp | higher |
| longbench | 6.81% | 6.89% | +0.08 pp | higher |
| LongBenchv2 | 54.47% | 57.46% | +2.99 pp | higher |
| keti_long_ctx_gutenberg | 99.38% | 99.25% | -0.13 pp | higher |

## OpenCompass Extra

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| extra_registered_average | 57.26% | 57.61% | +0.35 pp | higher |
| extra_registered_mc_average | 88.46% | 89.37% | +0.91 pp | higher |
| extra_registered_math_average | 53.57% | 54.12% | +0.55 pp | higher |
| ARC-c | 73.56% | 80.34% | +6.78 pp | higher |
| ARC-e | 83.07% | 85.01% | +1.94 pp | higher |
| BoolQ | 90.55% | 90.24% | -0.31 pp | higher |
| COPA | 100.00% | 100.00% | +0.00 pp | higher |
| commonsense_qa | 88.45% | 87.96% | -0.49 pp | higher |
| hellaswag | 94.28% | 94.12% | -0.16 pp | higher |
| openbookqa | 89.80% | 90.00% | +0.20 pp | higher |
| piqa | 95.43% | 95.81% | +0.38 pp | higher |
| siqa | 76.51% | 76.77% | +0.26 pp | higher |
| winogrande | 92.90% | 93.45% | +0.55 pp | higher |
| mmlu | 92.00% | 92.13% | +0.13 pp | higher |
| mmlu-stem | 94.90% | 94.71% | -0.19 pp | higher |
| mmlu-humanities | 91.56% | 91.64% | +0.08 pp | higher |
| mmlu-social-science | 91.96% | 92.64% | +0.68 pp | higher |
| mmlu-other | 88.27% | 88.41% | +0.14 pp | higher |
| gsm8k | 9.86% | 10.69% | +0.83 pp | higher |
| math | 97.28% | 97.56% | +0.28 pp | higher |
| mbpp | 42.40% | 43.00% | +0.60 pp | higher |
| lambada | 0.00% | 0.00% | +0.00 pp | higher |
| drop | 91.89% | 92.00% | +0.11 pp | higher |
| nq | 32.52% | 32.66% | +0.14 pp | higher |

## OpenCompass Korean

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| korean_hf_average | 17.18% | 16.77% | -0.41 pp | higher |
| kmmlu | 1.97% | 1.33% | -0.64 pp | higher |
| csatqa | 19.23% | 18.70% | -0.53 pp | higher |
| haerae | 19.21% | 19.21% | +0.00 pp | higher |
| k2_eval | 17.36% | 16.67% | -0.69 pp | higher |
| kobest | 46.49% | 46.61% | +0.12 pp | higher |
| kobest_boolq | 53.43% | 53.43% | +0.00 pp | higher |
| kobest_copa | 49.60% | 50.00% | +0.40 pp | higher |
| kobest_hellaswag | 22.20% | 22.40% | +0.20 pp | higher |
| kobest_sentineg | 50.00% | 50.00% | +0.00 pp | higher |
| kobest_wic | 57.21% | 57.21% | +0.00 pp | higher |
| kobalt | 9.71% | 9.71% | +0.00 pp | higher |
| kr_clinical_qa | 6.31% | 5.18% | -1.13 pp | higher |

## BFCL V4

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| Overall Acc | 32.77% | 32.11% | -0.66 pp | higher |
| Non-Live AST Acc | 89.60% | 89.44% | -0.16 pp | higher |
| Non-Live Simple AST | 79.42% | 79.25% | -0.17 pp | higher |
| Non-Live Multiple AST | 95.50% | 95.50% | +0.00 pp | higher |
| Non-Live Parallel AST | 91.50% | 91.00% | -0.50 pp | higher |
| Non-Live Parallel Multiple AST | 92.00% | 92.00% | +0.00 pp | higher |
| Multi Turn Acc | 66.25% | 64.50% | -1.75 pp | higher |
| Multi Turn Base | 76.50% | 76.00% | -0.50 pp | higher |
| Multi Turn Miss Func | 66.00% | 64.00% | -2.00 pp | higher |
| Multi Turn Miss Param | 53.00% | 52.00% | -1.00 pp | higher |
| Multi Turn Long Context | 69.50% | 66.00% | -3.50 pp | higher |

## ToolSandbox

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| ToolSandbox similarity (n=32) | 0.6077 | 0.6043 | -0.0034 | higher |

## Tau2

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| Tau2 airline (n=32) | 65.62% | 71.88% | +6.25 pp | higher |
| Tau2 retail (n=32) | 56.25% | 65.62% | +9.38 pp | higher |
| Tau2 telecom (n=32) | 87.50% | 78.12% | -9.38 pp | higher |
| Weighted overall (n=96) | 69.79% | 71.88% | +2.08 pp | higher |
| Domain macro | 69.79% | 71.88% | +2.08 pp | higher |

## Tau3

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| Tau3 airline (n=200) | 67.00% | 64.50% | -2.50 pp | higher |
| Tau3 retail (n=456) | 50.66% | 44.08% | -6.58 pp | higher |
| Tau3 telecom (n=456) | 50.66% | 51.54% | +0.88 pp | higher |
| Tau3 banking knowledge (n=388) | 7.47% | 9.02% | +1.55 pp | higher |
| Weighted overall (n=1500) | 41.67% | 40.00% | -1.67 pp | higher |
| Domain macro | 43.95% | 42.28% | -1.66 pp | higher |

## Largest improvements

- General multimodal / MMBench_DEV_EN_V11: +60.22 pp
- H400/HS100 target gates / H400 hard choice: +53.98 pp
- General multimodal / MMStar: +37.93 pp
- General multimodal / KRETA: +37.60 pp
- H400/HS100 target gates / H400 direct exact: +37.16 pp
- General multimodal / General-VL macro (6): +32.16 pp
- General multimodal / MMStar_KO: +27.13 pp
- General multimodal / MMMU_Pro_10c: +17.57 pp
- H400/HS100 target gates / H400 knowledge image: +13.85 pp
- OpenCompass Core / aime2025: +13.33 pp

## Largest regressions

- Tau2 / Tau2 telecom (n=32): -9.38 pp
- Tau3 / Tau3 retail (n=456): -6.58 pp
- Mammoth OCR line recall / heritage_reverse_mt: -4.49 pp
- Mammoth target containment / heritage_reverse_mt: -4.49 pp
- BFCL V4 / Multi Turn Long Context: -3.50 pp
- OpenCompass Core / aime2024: -3.33 pp
- Tau3 / Tau3 airline (n=200): -2.50 pp
- BFCL V4 / Multi Turn Miss Func: -2.00 pp
- Mammoth normalized similarity / heritage_reverse_mt: -1.77 pp
- Mammoth exact accuracy / heritage_reverse_mt: -1.76 pp

## Reading the result

- H400 direct exact measures open-ended canonical-name retrieval; H400 hard measures closed-set choice. A large gap between them indicates recognition/discrimination is stronger than exact name generation.
- HS100 train, unseen, and Simple distinguish memorization, held-out view generalization, and transfer to a separate simple-identification population. They are not interchangeable with Mammoth Heritage Simple.
- Mammoth exact is strict. Containment and normalized similarity show whether an answer is usable but differs in annotation, spacing, aliases, or added explanation.
- OCR CER is the only lower-is-better metric in this report; all other deltas are better when positive.
- OpenCompass, General-VL, BFCL, ToolSandbox, Tau2, and Tau3 are retention gates. Improvements in heritage should be interpreted together with these broad-capability deltas.

## Source locations

- Official OpenCompass: `/data/workspace/eval_models/test/outputs/*q35-27b-official-20260901r2full`
- Tuned OpenCompass: `/data/workspace/eval_models/test/outputs/*q35-27b-v28cl-hs25-20260902r1`
- Official Tau3: `/data/workspace/eval_models/tau3_axes/q35-27b-official-20260901r2full`
- Tuned Tau3: `/data/workspace/eval_models/tau3_axes/q35-27b-v28cl-hs25-20260902r1-full`
