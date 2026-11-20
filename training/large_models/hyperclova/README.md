---
language:
  - ko
  - en
license: other
license_name: hyperclovax
license_link: LICENSE
library_name: transformers
pipeline_tag: image-text-to-text
base_model:
  - naver-hyperclovax/HyperCLOVAX-SEED-Think-32B
base_model_relation: finetune
tags:
  - hyperclovax
  - multimodal
  - vision-language
  - korean
  - cultural-heritage
  - ocr
  - tool-use
  - long-horizon
  - image-text-to-text
---

# HyperCLOVA X KETI-HAECHI-32B

<table>
  <tr>
    <td align="center" width="40%">
      <img src="samples/images/haechi.png" alt="HAECHI mascot" width="100%">
    </td>
    <td align="center" width="60%">
      <img src="samples/images/haechi_personalization.png" alt="HAECHI personalization with Qwen and HyperCLOVA" width="100%">
    </td>
  </tr>
</table>

<p align="center"><strong>Powered by HyperCLOVA X</strong></p>

HyperCLOVA X KETI-HAECHI-32B is a multimodal model derived from
[`naver-hyperclovax/HyperCLOVAX-SEED-Think-32B`](https://huggingface.co/naver-hyperclovax/HyperCLOVAX-SEED-Think-32B).
It was developed for two primary purposes: improving Korean cultural-heritage
understanding and Korean OCR, and improving tool calling and multi-step,
stateful agent execution. Alongside these goals, the model retains broad
multimodal, language, and coding capabilities from the base model.

## Core capability profile

- **Korean cultural heritage and OCR:** identifies the official names of
  heritage objects, answers questions grounded in heritage images, and reads
  Korean text from signs, scenes, rendered text, and public documents.
- **Tool calling and long-horizon task execution:** selects and calls tools,
  carries information across multiple turns, tracks changing state, and works
  toward an end-to-end goal over several steps.
- **General multimodal understanding:** interprets images and text together,
  follows Korean and English instructions, and performs visual reasoning beyond
  the specialized heritage domain.

## Performance overview

<img src="samples/images/key_performance_overview.png" alt="Bar chart comparing the official HyperCLOVA X SEED 32B Think base model with HyperCLOVA X KETI-HAECHI-32B on representative cultural-heritage, Korean OCR, long-horizon agent, tool-calling, and general multimodal benchmarks" width="1000">

The chart highlights representative metrics from each major capability area.
Detailed benchmark tables appear in the Evaluation section.

## Quickstart

The checkpoint contains custom HyperCLOVA X model and processor code, so
`trust_remote_code=True` is required. The example below follows the direct
Transformers runtime used to verify the packaged BF16 checkpoint on two 80 GB
GPUs. `torchvision` is required when `AutoProcessor` initializes the bundled
video processor, including for image-only inference. The versions below are the
combination verified in a clean environment.

```bash
pip install "torch==2.9.1" "torchvision==0.24.1" "transformers>=4.57,<5" accelerate pillow safetensors huggingface_hub
```

```python
import sys

import torch
from huggingface_hub import hf_hub_download
from PIL import Image
from transformers import AutoProcessor
from transformers.dynamic_module_utils import get_class_from_dynamic_module

model_id = "KETI-AIR/HyperCLOVA-X-KETI-HAECHI-32B"
image_path = hf_hub_download(
    repo_id=model_id,
    filename="samples/qualitative/01_gyeongbokgung_gyeonghoeru.jpg",
)

processor = AutoProcessor.from_pretrained(
    model_id,
    trust_remote_code=True,
    use_fast=False,
)

# The bundled visual code selects FlashAttention2 on Ampere-class GPUs.
# This verified fallback uses Transformers SDPA when flash-attn is unavailable.
model_class = get_class_from_dynamic_module(
    "modeling_vlm.HCXVisionForCausalLM",
    model_id,
)
sys.modules[model_class.__module__].is_ampere_or_newer = lambda: False

model = model_class.from_pretrained(
    model_id,
    dtype=torch.bfloat16,
    device_map="balanced",
    max_memory={0: "76GiB", 1: "76GiB"},
    low_cpu_mem_usage=True,
).eval()

image = Image.open(image_path).convert("RGB")
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {"url": image_path},
            },
            {
                "type": "text",
                "text": "사진 속 국가유산의 정확한 공식 명칭만 답하세요. 설명은 쓰지 마세요.",
            },
        ],
    }
]

prompt = processor.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True,
    thinking=False,
)
inputs = processor(
    text=[prompt],
    images=[image],
    min_pixels=65_536,
    max_pixels=1_048_576,
    return_tensors="pt",
).to(model.device)

with torch.inference_mode():
    output_ids = model.inference(
        **inputs,
        max_length=32,
        min_length=0,
        temperature=0.0,
        do_sample=False,
        use_cache=True,
    )

answer = processor.batch_decode(output_ids, skip_special_tokens=True)[0].strip()
print(answer)

# Example output from this checkpoint:
# 경복궁 경회루
```

For the packaged directory in this release, use `model_id = "./model"` and
open the sample image directly from
`samples/qualitative/01_gyeongbokgung_gyeonghoeru.jpg`. Adjust `device_map` and
`max_memory` for the deployment hardware. The upstream model also supports the
[OmniServe](https://github.com/NAVER-Cloud-HyperCLOVA-X/OmniServe)
OpenAI-compatible runtime.

The example disables thinking mode for concise extraction. Set
`thinking=True` and provide a larger generation budget for tasks that benefit
from the model's reasoning mode.

## Evaluation

All reported deltas are calculated as **HyperCLOVA X KETI-HAECHI-32B minus
the untouched official HyperCLOVA X SEED 32B Think weights**. Percentage
deltas are absolute percentage points. The evaluator-compatible base copied
only the chat template; model weights were unchanged. Both models used matched
API, template, decoding, stop-token, parser, and dataset settings.

### Qualitative comparison with the base model

The examples below were re-run from the packaged BF16 checkpoint and the
untouched official base weights using `HCXVisionForCausalLM.inference()` with
the original evaluation prompts. Both models used thinking disabled, greedy
decoding, a 256-token output limit, and the same image preprocessing settings.
For OCR examples, the table shows the recognized text span; surrounding
explanatory prose is omitted.

#### Korean cultural-heritage recognition

| Target (reference) | HyperCLOVA X SEED 32B Think base | HyperCLOVA X KETI-HAECHI-32B |
|---|---|---|
| <img src="samples/qualitative/02_geumdong_yeonga_buddha.jpg" alt="금동연가7년명여래입상" width="160"><br>금동연가7년명여래입상 | ❌ `금동미륵보살반가사유상 (국보 제78호)` | ✅ `금동연가7년명여래입상` |
| <img src="samples/qualitative/03_white_porcelain_grape_monkey_jar.jpg" alt="백자 철화포도원숭이문 항아리" width="160"><br>백자 철화포도원숭이문 항아리 | ❌ `백자철화포도문항아리` | ✅ `백자 철화포도원숭이문 항아리` |
| <img src="samples/qualitative/04_muryeong_crown_ornament.jpg" alt="무령왕 금제 관식" width="160"><br>무령왕 금제 관식 | ❌ `금제 관식` | ✅ `무령왕 금제 관식` |

#### Korean OCR

##### Font

| Target (reference) | HyperCLOVA X SEED 32B Think base | HyperCLOVA X KETI-HAECHI-32B |
|---|---|---|
| <img src="samples/qualitative/05_ocr_font_waen.png" alt="왠 글꼴 OCR 샘플" width="200"><br>`왠` | ❌ `왜` | ✅ `왠` |
| <img src="samples/qualitative/06_ocr_font_jeojeollo.png" alt="저절로 글꼴 OCR 샘플" width="200"><br>`저절로` | ❌ `절로` | ✅ `저절로` |
| <img src="samples/qualitative/07_ocr_font_ipda.png" alt="입다 글꼴 OCR 샘플" width="200"><br>`입다` | ❌ `입니다` | ✅ `입다` |
| <img src="samples/qualitative/08_ocr_font_chap.png" alt="찹 글꼴 OCR 샘플" width="200"><br>`찹` | ❌ `참` | ✅ `찹` |

##### Outdoor

| Target (reference) | HyperCLOVA X SEED 32B Think base | HyperCLOVA X KETI-HAECHI-32B |
|---|---|---|
| <img src="samples/qualitative/11_ocr_outdoor_coin_karaoke.png" alt="동전 노래연습장 실외 간판 OCR 샘플" width="200"><br>`동전 노래연습장` | ❌ `동전 노래방` | ✅ `동전 노래연습장` |
| <img src="samples/qualitative/12_ocr_outdoor_ddungs.png" alt="뚱스 실외 간판 OCR 샘플" width="200"><br>`뚱스` | ❌ `뚠스` | ✅ `뚱스` |

##### Public exec

| Target (reference) | HyperCLOVA X SEED 32B Think base | HyperCLOVA X KETI-HAECHI-32B |
|---|---|---|
| <img src="samples/qualitative/13_ocr_public_disaster.png" alt="재난안전관리과 공공문서 OCR 샘플" width="200"><br>`재난안전관리과` | ❌ `폐쇄병동전과` | ✅ `재난안전관리과` |
| <img src="samples/qualitative/15_ocr_public_gimhae_market.png" alt="김해시장 전산정보과장 공공문서 OCR 샘플" width="200"><br>`김해시장(전산정보과장)` | ❌ `개인 정보에 해당합니다.` | ✅ `김해시장(전산정보과장)` |

### Quantitative benchmarks

#### Korean cultural-heritage performance

| Benchmark | Official base | HyperCLOVA X KETI-HAECHI-32B | Delta |
|---|---:|---:|---:|
| H400 direct exact | 5.05% | **74.16%** | +69.11 pp |
| H400 hard choice | 59.79% | **89.76%** | +29.97 pp |
| H400 knowledge image | 4.89% | **35.13%** | +30.24 pp |
| H400 knowledge text | 9.07% | **39.59%** | +30.53 pp |

H400 is an internal evaluation set built around 400 Korean cultural-heritage
items. It evaluates canonical-name recognition, fine-grained discrimination
among visually similar heritage items, and heritage knowledge grounded in
either images or text. H400 direct exact measures open-ended canonical-name
retrieval, while H400 hard measures closed-set discrimination. The
knowledge-image and knowledge-text values are mean string-similarity scores in
this report.

#### Korean (Hangul) OCR performance

| Benchmark | Official base | HyperCLOVA X KETI-HAECHI-32B | Delta |
|---|---:|---:|---:|
| `ocr_font` exact | 18.36% | **20.96%** | +2.60 pp |
| `ocr_outdoor` exact | 33.59% | **38.87%** | +5.27 pp |
| `ocr_public_exec` exact | **2.47%** | 1.69% | -0.78 pp |

These Mammoth OCR results use strict exact match. Font and outdoor OCR improve,
while public-document exact match declines slightly despite selected successful
examples above.

#### Tool calling and long-horizon task performance

##### Tau2

| Benchmark | Official base | HyperCLOVA X KETI-HAECHI-32B | Delta |
|---|---:|---:|---:|
| Tau2 airline (n=32) | **46.88%** | 34.38% | -12.50 pp |
| Tau2 retail (n=32) | 37.50% | **53.12%** | +15.62 pp |
| Tau2 telecom (n=32) | 37.50% | **40.62%** | +3.12 pp |
| Tau2 weighted overall (n=96) | 40.62% | **42.71%** | +2.08 pp |

Tau2 measures end-to-end success across multi-step airline, retail, and telecom
workflows. The weighted overall score improves through retail and telecom gains,
although airline performance declines.

##### BFCL V4

| Benchmark | Official base | HyperCLOVA X KETI-HAECHI-32B | Delta |
|---|---:|---:|---:|
| Overall accuracy | 7.85% | **15.00%** | +7.15 pp |
| Non-Live AST accuracy | 21.42% | **64.17%** | +42.75 pp |
| Non-Live Simple AST | 23.17% | **48.67%** | +25.50 pp |
| Non-Live Multiple AST | 45.50% | **90.50%** | +45.00 pp |
| Non-Live Parallel AST | 13.50% | **60.50%** | +47.00 pp |
| Non-Live Parallel Multiple AST | 3.50% | **57.00%** | +53.50 pp |
| Multi-turn accuracy | 2.63% | **13.63%** | +11.00 pp |
| Multi-turn base | 4.00% | **19.50%** | +15.50 pp |
| Multi-turn missing function | 2.50% | **9.50%** | +7.00 pp |
| Multi-turn missing parameter | 1.50% | **10.50%** | +9.00 pp |
| Multi-turn long context | 2.50% | **15.00%** | +12.50 pp |

BFCL V4 measures structured function-call generation and multi-turn recovery
from missing functions or parameters. The tuned checkpoint improves across all
reported BFCL V4 categories.

#### General multimodal and language retention

| Benchmark | Official base | HyperCLOVA X KETI-HAECHI-32B | Delta |
|---|---:|---:|---:|
| General-VL macro (7) | **66.19%** | 65.29% | -0.90 pp |
| MMBench DEV EN v1.1 | 83.36% | **83.59%** | +0.23 pp |
| MMStar | 63.00% | **63.13%** | +0.13 pp |
| MMStar-KO | 59.27% | **60.00%** | +0.73 pp |
| KRETA | **84.32%** | 78.08% | -6.25 pp |
| MMMU-Pro 10c | 38.15% | **38.96%** | +0.81 pp |
| HallusionBench aAcc | **66.46%** | 64.77% | -1.68 pp |
| MathVista MINI | **68.80%** | 68.50% | -0.30 pp |
| OpenCompass Core | **54.98%** | 54.20% | -0.78 pp |
| OpenCompass Extra | **68.67%** | 68.07% | -0.60 pp |
| OpenCompass Korean | **53.74%** | 53.01% | -0.73 pp |

See the [detailed score report](reports/DETAILED_SCORE_REPORT.md) for the full
results, the [benchmark guide](reports/BENCHMARK_GUIDE.md) for definitions and
caveats, and the [paired output report](reports/PAIRED_OUTPUT_EXAMPLES.md) for
additional raw Base/Tuned examples.

## Intended use

The model is intended for research and prototyping involving:

- Korean cultural-heritage image identification and visual question answering;
- Korean scene, sign, font, and public-document OCR;
- image-grounded heritage knowledge retrieval;
- multi-step, stateful tool-use workflows with explicit monitoring and
  recovery;
- general image understanding and text generation; and
- analysis of domain specialization and capability retention in multimodal
  models.

## Responsible use

Verify cultural-property names and factual claims against authoritative
catalogs or domain experts. Preserve human review for public descriptions,
education, archival metadata, and research outputs. Do not treat model output
as evidence of authenticity or provenance. Avoid submitting sensitive or
personal documents for OCR unless the deployment provides appropriate privacy
controls. All use must comply with the Acceptable Use Policy incorporated into
the HyperCLOVA X model license.

## Limitations

- OCR outputs may omit text, normalize spelling incorrectly, or add unsupported
  text. Public-document exact match is lower than the official base in this
  evaluation.
- The model can hallucinate names, dates, designations, provenance, and
  historical claims. Similar-looking artifacts and uncommon viewpoints are
  especially challenging.
- General-VL macro, KRETA, HallusionBench, and the Tau2 airline domain regress
  relative to the official base.
- Direct Transformers loading relies on bundled custom code and is sensitive to
  the Transformers version, attention backend, and available GPU memory.
- General multilingual, video, robustness, demographic-bias, privacy, and
  safety behavior were not comprehensively evaluated for this release.
- As with the base model, generated content may be inaccurate, biased, unsafe,
  or unsuitable for the user's context.

## Core contributors

- **San Kim** ([kimsan0622@keti.re.kr](mailto:kimsan0622@keti.re.kr)) — Led
  long-context agent task performance and development/management of the main
  training loop.
- **Byunggill Joe** ([byunggill@keti.re.kr](mailto:byunggill@keti.re.kr)) —
  Secured GPU compute resources through the support program and led Korean
  cultural-heritage recognition/OCR performance.

## Acknowledgements

HyperCLOVA X KETI-HAECHI-32B was developed using compute resources provided
through the `첨단 GPU 활용 지원 사업` of the National IT Industry Promotion
Agency (NIPA; 정보통신산업진흥원).

## License and attribution

This derivative checkpoint is distributed under the
[HyperCLOVA X SEED 32B Think Model License Agreement](LICENSE), not the Apache
License 2.0. Redistribution and use are subject to that agreement and its
Acceptable Use Policy, including naming, attribution, notice, and display
requirements. See [NOTICE](NOTICE) for the required attribution and modification
notice. Third-party data and sample images may be subject to additional terms.

**Powered by HyperCLOVA X**

## Citation

```bibtex
@misc{hyperclova_x_keti_haechi_32b,
  title        = {HyperCLOVA X KETI-HAECHI-32B},
  author       = {Kim, San and Joe, Byunggill},
  year         = {2026},
  howpublished = {Hugging Face model repository},
  url          = {https://huggingface.co/KETI-AIR/HyperCLOVA-X-KETI-HAECHI-32B}
}
```

## 한국어 요약

이 모델은 `naver-hyperclovax/HyperCLOVAX-SEED-Think-32B`를 기반으로 두
가지 목적을 위해 개발한 멀티모달 모델입니다. 첫 번째 목적은 한국 문화유산의
정확한 명칭 식별, 이미지 기반 문화유산 질의응답, 한글 OCR 능력을 향상하는
것입니다. 두 번째 목적은 적절한 도구를 호출하고 여러 단계에 걸쳐 정보를
기억하며 변화하는 상태를 추적하는 장기작업 수행 능력을 향상하는 것입니다.

공식 베이스 모델과 동일한 조건의 내부 평가에서 H400 직접 식별 정확도는
5.05%에서 74.16%로, H400 유사 문화재 선택 정확도는 59.79%에서 89.76%로
향상되었습니다. 한글 OCR은 글꼴과 실외 간판에서 향상되었지만 공공문서 exact
match는 2.47%에서 1.69%로 하락했습니다. 장기작업 평가인 Tau2 가중 점수는
40.62%에서 42.71%로, BFCL V4 전체 정확도는 7.85%에서 15.00%로
향상되었습니다. 실제 배포에서는 단계별 상태 확인, 실패 복구, 결과 검증을 함께
적용하는 것을 권장합니다.
