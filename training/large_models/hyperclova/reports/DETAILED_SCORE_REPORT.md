# HyperCLOVAX-SEED-Think-32B Official Base vs H400/HS100 Step-2500

Comparison generated: 2026-09-02 (Asia/Seoul).

## Contract

- Official base: `/data/workspace/post-training/outputs/hyperclovax-seed-think-32b-official-evalcompat`. Model weights are the untouched official weights; only the evaluator-compatible chat template was copied.
- Tuned: `/data/workspace/post-training/outputs/hyperclovax-seed-think-32b-h400-hs100-scale2500-step2500-hf`.
- All deltas are tuned minus official base. Percentage metrics use absolute percentage points.
- The invalid first VL run is excluded. This report uses the corrected r2 VL/Mammoth/stateful runs, r4fixed OpenCompass, and clean r2 Tau3 runs.
- OpenCompass uses `thinking=False`, stop IDs `[128001, 0]`, and matched datasets/parsers for both models.

## Executive summary

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| General-VL macro (7) | 66.19% | 65.29% | -0.90 pp | higher |
| heritage_simple | 0.39% | 9.77% | +9.38 pp | higher |
| H400 direct exact | 5.05% | 74.16% | +69.11 pp | higher |
| H400 hard choice | 59.79% | 89.76% | +29.97 pp | higher |
| core_average | 54.98% | 54.20% | -0.78 pp | higher |
| extra_registered_average | 68.67% | 68.07% | -0.60 pp | higher |
| korean_hf_average | 53.74% | 53.01% | -0.73 pp | higher |
| Overall Acc | 7.85% | 15.00% | +7.15 pp | higher |
| Weighted overall (n=96) | 40.62% | 42.71% | +2.08 pp | higher |
| Weighted overall (n=1500) | 31.80% | 27.93% | -3.87 pp | higher |

## General multimodal

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| General-VL macro (7) | 66.19% | 65.29% | -0.90 pp | higher |
| MMBench_DEV_EN_V11 | 83.36% | 83.59% | +0.23 pp | higher |
| MMStar | 63.00% | 63.13% | +0.13 pp | higher |
| MMStar_KO | 59.27% | 60.00% | +0.73 pp | higher |
| KRETA | 84.32% | 78.08% | -6.25 pp | higher |
| MMMU_Pro_10c | 38.15% | 38.96% | +0.81 pp | higher |
| HallusionBench aAcc | 66.46% | 64.77% | -1.68 pp | higher |
| MathVista MINI | 68.80% | 68.50% | -0.30 pp | higher |

## Mammoth exact accuracy

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| heritage_multi_attr | 23.83% | 29.82% | +5.99 pp | higher |
| heritage_reverse_mt | 88.87% | 89.26% | +0.39 pp | higher |
| heritage_simple | 0.39% | 9.77% | +9.38 pp | higher |
| ocr_font | 18.36% | 20.96% | +2.60 pp | higher |
| ocr_outdoor | 33.59% | 38.87% | +5.27 pp | higher |
| ocr_public_exec | 2.47% | 1.69% | -0.78 pp | higher |

## Mammoth target containment

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| heritage_multi_attr | 35.55% | 42.58% | +7.03 pp | higher |
| heritage_reverse_mt | 91.21% | 91.21% | +0.00 pp | higher |
| heritage_simple | 1.04% | 10.55% | +9.51 pp | higher |
| ocr_font | 28.65% | 25.00% | -3.65 pp | higher |
| ocr_outdoor | 70.12% | 72.46% | +2.34 pp | higher |
| ocr_public_exec | 5.60% | 4.56% | -1.04 pp | higher |

## Mammoth normalized similarity

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| heritage_multi_attr | 40.62% | 47.99% | +7.37 pp | higher |
| heritage_reverse_mt | 88.87% | 89.26% | +0.39 pp | higher |
| heritage_simple | 5.60% | 20.47% | +14.86 pp | higher |
| ocr_font | 21.98% | 25.12% | +3.14 pp | higher |
| ocr_outdoor | 47.10% | 61.97% | +14.87 pp | higher |
| ocr_public_exec | 7.65% | 8.38% | +0.73 pp | higher |

## Mammoth OCR CER

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| heritage_multi_attr | 0.8531 | 0.7527 | -0.1004 | lower |
| heritage_reverse_mt | 0.1113 | 0.1074 | -0.0039 | lower |
| heritage_simple | 29.4449 | 1.1959 | -28.2489 | lower |
| ocr_font | 39.3483 | 1.6765 | -37.6718 | lower |
| ocr_outdoor | 4.3497 | 1.1733 | -3.1764 | lower |
| ocr_public_exec | 13.0505 | 2.0653 | -10.9852 | lower |

## Mammoth OCR line recall

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| heritage_multi_attr | 35.55% | 42.58% | +7.03 pp | higher |
| heritage_reverse_mt | 91.21% | 91.21% | +0.00 pp | higher |
| heritage_simple | 1.04% | 10.55% | +9.51 pp | higher |
| ocr_font | 28.65% | 25.00% | -3.65 pp | higher |
| ocr_outdoor | 70.12% | 72.46% | +2.34 pp | higher |
| ocr_public_exec | 5.60% | 4.56% | -1.04 pp | higher |

## Cultural heritage title-clean

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| overall / exact | 0.19% | 7.27% | +7.08 pp | higher |
| overall / containment | 1.33% | 7.74% | +6.41 pp | higher |
| overall / similarity | 5.06% | 15.97% | +10.90 pp | higher |
| overall / identity-any exact | 0.36% | 10.99% | +10.63 pp | higher |
| identity / exact | 0.54% | 20.29% | +19.75 pp | higher |
| identity / containment | 1.24% | 20.45% | +19.21 pp | higher |
| identity / similarity | 9.12% | 34.87% | +25.74 pp | higher |
| identity / identity-any exact | 0.72% | 22.10% | +21.38 pp | higher |
| view_caption / exact | 0.00% | 0.00% | +0.00 pp | higher |
| view_caption / containment | 1.38% | 0.65% | -0.73 pp | higher |
| view_caption / similarity | 2.80% | 5.42% | +2.62 pp | higher |
| view_caption / identity-any exact | 0.00% | 0.00% | +0.00 pp | higher |
| national_treasure / exact | 0.83% | 26.03% | +25.21 pp | higher |
| national_treasure / containment | 2.27% | 26.86% | +24.59 pp | higher |
| national_treasure / similarity | 9.61% | 38.33% | +28.72 pp | higher |
| national_treasure / identity-any exact | 1.15% | 30.84% | +29.68 pp | higher |
| other / exact | 0.10% | 4.36% | +4.26 pp | higher |
| other / containment | 1.19% | 4.78% | +3.59 pp | higher |
| other / similarity | 4.36% | 12.50% | +8.14 pp | higher |
| other / identity-any exact | 0.19% | 6.71% | +6.53 pp | higher |

## H400/HS100 target gates

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| H400 direct exact | 5.05% | 74.16% | +69.11 pp | higher |
| H400 hard choice | 59.79% | 89.76% | +29.97 pp | higher |
| H400 knowledge image | 4.89% | 35.13% | +30.24 pp | higher |
| H400 knowledge text | 9.07% | 39.59% | +30.53 pp | higher |
| HS100 train exact | 0.00% | 100.00% | +100.00 pp | higher |
| HS100 unseen exact | 0.99% | 74.26% | +73.27 pp | higher |
| HS100 Simple exact | 0.00% | 64.71% | +64.71 pp | higher |

## OpenCompass Core

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| core_average | 54.98% | 54.20% | -0.78 pp | higher |
| IFEval | 83.36% | 82.44% | -0.92 pp | higher |
| aime2024 | 16.67% | 23.33% | +6.66 pp | higher |
| aime2025 | 13.33% | 16.67% | +3.34 pp | higher |
| math_prm800k_500 | 80.60% | 82.00% | +1.40 pp | higher |
| bbh | 71.34% | 56.48% | -14.86 pp | higher |
| GPQA_diamond | 47.47% | 42.93% | -4.54 pp | higher |
| mmlu_pro | 66.50% | 64.77% | -1.73 pp | higher |
| openai_humaneval | 80.49% | 81.71% | +1.22 pp | higher |
| lcb_code_generation | 37.50% | 33.00% | -4.50 pp | higher |
| leval | 51.26% | 50.60% | -0.66 pp | higher |
| longbench | 53.63% | 54.22% | +0.59 pp | higher |
| LongBenchv2 | 34.59% | 33.40% | -1.19 pp | higher |
| keti_long_ctx_gutenberg | 78.00% | 83.00% | +5.00 pp | higher |

## OpenCompass Extra

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| extra_registered_average | 68.67% | 68.07% | -0.60 pp | higher |
| extra_registered_mc_average | 83.88% | 80.87% | -3.01 pp | higher |
| extra_registered_math_average | 72.42% | 69.95% | -2.47 pp | higher |
| ARC-c | 88.81% | 80.68% | -8.13 pp | higher |
| ARC-e | 94.00% | 84.30% | -9.70 pp | higher |
| BoolQ | 88.96% | 89.63% | +0.67 pp | higher |
| COPA | 98.00% | 99.00% | +1.00 pp | higher |
| commonsense_qa | 84.77% | 84.60% | -0.17 pp | higher |
| hellaswag | 90.23% | 90.68% | +0.45 pp | higher |
| openbookqa | 90.60% | 71.40% | -19.20 pp | higher |
| piqa | 85.96% | 84.60% | -1.36 pp | higher |
| siqa | 47.75% | 50.77% | +3.02 pp | higher |
| winogrande | 69.69% | 73.01% | +3.32 pp | higher |
| mmlu | 83.13% | 82.67% | -0.46 pp | higher |
| mmlu-stem | 85.57% | 84.11% | -1.46 pp | higher |
| mmlu-humanities | 81.86% | 81.60% | -0.26 pp | higher |
| mmlu-social-science | 84.33% | 84.84% | +0.51 pp | higher |
| mmlu-other | 79.71% | 79.65% | -0.06 pp | higher |
| gsm8k | 79.98% | 80.89% | +0.91 pp | higher |
| math | 64.86% | 59.00% | -5.86 pp | higher |
| mbpp | 69.60% | 66.80% | -2.80 pp | higher |
| lambada | 57.40% | 61.85% | +4.45 pp | higher |
| drop | 87.83% | 85.50% | -2.33 pp | higher |
| nq | 26.45% | 28.86% | +2.41 pp | higher |

## OpenCompass Korean

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| korean_hf_average | 53.74% | 53.01% | -0.73 pp | higher |
| kmmlu | 7.75% | 7.39% | -0.36 pp | higher |
| csatqa | 76.18% | 76.07% | -0.11 pp | higher |
| haerae | 72.42% | 70.35% | -2.07 pp | higher |
| k2_eval | 87.96% | 87.73% | -0.23 pp | higher |
| kobest | 89.99% | 90.01% | +0.02 pp | higher |
| kobest_boolq | 94.29% | 93.71% | -0.58 pp | higher |
| kobest_copa | 97.20% | 97.20% | +0.00 pp | higher |
| kobest_hellaswag | 74.20% | 74.40% | +0.20 pp | higher |
| kobest_sentineg | 99.50% | 99.50% | +0.00 pp | higher |
| kobest_wic | 84.75% | 85.25% | +0.50 pp | higher |
| kobalt | 36.71% | 34.43% | -2.28 pp | higher |
| kr_clinical_qa | 5.18% | 5.12% | -0.06 pp | higher |

## BFCL V4

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| Overall Acc | 7.85% | 15.00% | +7.15 pp | higher |
| Non-Live AST Acc | 21.42% | 64.17% | +42.75 pp | higher |
| Non-Live Simple AST | 23.17% | 48.67% | +25.50 pp | higher |
| Non-Live Multiple AST | 45.50% | 90.50% | +45.00 pp | higher |
| Non-Live Parallel AST | 13.50% | 60.50% | +47.00 pp | higher |
| Non-Live Parallel Multiple AST | 3.50% | 57.00% | +53.50 pp | higher |
| Multi Turn Acc | 2.63% | 13.63% | +11.00 pp | higher |
| Multi Turn Base | 4.00% | 19.50% | +15.50 pp | higher |
| Multi Turn Miss Func | 2.50% | 9.50% | +7.00 pp | higher |
| Multi Turn Miss Param | 1.50% | 10.50% | +9.00 pp | higher |
| Multi Turn Long Context | 2.50% | 15.00% | +12.50 pp | higher |

## ToolSandbox

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| ToolSandbox similarity (n=32) | 0.6943 | 0.7410 | +0.0467 | higher |

## Tau2

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| Tau2 airline (n=32) | 46.88% | 34.38% | -12.50 pp | higher |
| Tau2 retail (n=32) | 37.50% | 53.12% | +15.62 pp | higher |
| Tau2 telecom (n=32) | 37.50% | 40.62% | +3.12 pp | higher |
| Weighted overall (n=96) | 40.62% | 42.71% | +2.08 pp | higher |
| Domain macro | 40.62% | 42.71% | +2.08 pp | higher |

## Tau3

| Benchmark | Official Base | Tuned | Delta | Direction |
|---|---:|---:|---:|:---:|
| Tau3 airline (n=200) | 42.50% | 31.00% | -11.50 pp | higher |
| Tau3 retail (n=456) | 44.08% | 47.59% | +3.51 pp | higher |
| Tau3 telecom (n=456) | 39.04% | 29.17% | -9.87 pp | higher |
| Tau3 banking knowledge (n=388) | 3.35% | 1.80% | -1.55 pp | higher |
| Weighted overall (n=1500) | 31.80% | 27.93% | -3.87 pp | higher |
| Domain macro | 32.24% | 27.39% | -4.85 pp | higher |

## Interpretation

- Heritage acquisition succeeded strongly on HCX: H400 direct, H400 hard, HS100 unseen, and HS100 Simple all show large gains rather than only closed-set choice gains.
- OpenCompass Core, Extra, and Korean move by less than one point in aggregate, but BBH and several tool domains regress materially; the aggregate alone hides these local changes.
- General VL is mostly preserved, with KRETA and HallusionBench as the main regressions. Mammoth OCR public-executive also regresses slightly.
- BFCL and ToolSandbox improve, Tau2 rises slightly, while Tau3 declines. These suites exercise different schemas and interaction dynamics and should not be collapsed into one tool score.
- HCX and Qwen 27B are not a controlled architecture comparison: their vision-freeze policy and model-specific chat/template behavior differ.

## Source locations

- Official OpenCompass: `/data/workspace/eval_models/test/outputs/*hcx32b-official-base-20260901r2fixed`
- Tuned OpenCompass: `/data/workspace/eval_models/test/outputs/*hcx32b-h400-hs100-s2500-20260901r4fixed`
- Official Tau3: `/data/workspace/eval_models/tau3_axes/hcx32b-official-base-20260901r2`
- Tuned Tau3: `/data/workspace/eval_models/tau3_axes/hcx32b-h400-hs100-s2500-20260901r2`
