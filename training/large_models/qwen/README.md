---
language:
  - ko
  - en
license: apache-2.0
library_name: transformers
pipeline_tag: image-text-to-text
base_model:
  - Qwen/Qwen3.5-27B
base_model_relation: finetune
tags:
  - qwen3.5
  - multimodal
  - vision-language
  - korean
  - cultural-heritage
  - ocr
  - tool-use
  - long-horizon
  - image-text-to-text
---

# Qwen3.5-KETI-HAECHI-27B

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

Qwen3.5-KETI-HAECHI-27B is a multimodal model derived from
[`Qwen/Qwen3.5-27B`](https://huggingface.co/Qwen/Qwen3.5-27B). It was developed
for two primary purposes: improving Korean cultural-heritage understanding and
Korean OCR, and improving tool calling and multi-step, stateful agent execution.
Alongside these goals, the model preserves broad multimodal, language, and
coding capabilities from the base model.

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

<img src="samples/images/key_performance_overview.png" alt="Bar chart comparing the official Qwen3.5-27B base model with Qwen3.5-KETI-HAECHI-27B on representative cultural-heritage, Korean OCR, long-horizon agent, tool-calling, and general multimodal benchmarks" width="1000">

The chart highlights representative metrics from each major capability area.
Detailed benchmark tables appear in the Evaluation section.

## Quickstart

Qwen3.5 support and `AutoModelForMultimodalLM` may be unavailable in older
Transformers releases. The commands below reproduce the clean environment used
to verify this repository. `torchvision` is required when `AutoProcessor`
initializes the bundled video processor, including for image-only inference.

```bash
pip install "torch==2.9.1" "torchvision==0.24.1" accelerate pillow safetensors
pip install "transformers @ git+https://github.com/huggingface/transformers.git@c93057d4835cd31752bb56f59989dd27696eb45b"
```

When the model files are stored at the root of a Hugging Face repository:

```python
import torch
from transformers import AutoModelForMultimodalLM, AutoProcessor

model_id = "KETI-AIR/Qwen3.5-KETI-HAECHI-27B"
image_url = (
    f"https://huggingface.co/{model_id}/resolve/main/"
    "samples/qualitative/06_cheomseongdae.jpg"
)

processor = AutoProcessor.from_pretrained(model_id)
model = AutoModelForMultimodalLM.from_pretrained(
    model_id,
    dtype=torch.bfloat16,
    device_map="auto",
).eval()

messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "image",
                "url": image_url,
            },
            {
                "type": "text",
                "text": "사진 속 국가유산의 정확한 공식 명칭만 답하세요. 설명은 쓰지 마세요.",
            },
        ],
    }
]

inputs = processor.apply_chat_template(
    messages,
    add_generation_prompt=True,
    tokenize=True,
    return_dict=True,
    return_tensors="pt",
    enable_thinking=False,
).to(model.device)

with torch.inference_mode():
    output_ids = model.generate(
        **inputs,
        max_new_tokens=32,
        do_sample=False,
    )

generated_ids = output_ids[:, inputs["input_ids"].shape[1]:]
answer = processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
print(answer)

# Example output from this checkpoint:
# 경주 첨성대
```

For the packaged directory in this release, use `model_id = "./model"` and
`image_url = "samples/qualitative/06_cheomseongdae.jpg"`. For a text-only
request, omit the image item and retain only a `{"type": "text", "text":
...}` item in the message content.

Thinking mode is enabled by default in the bundled chat template. The example
disables it for concise answers. Set `enable_thinking=True` for tasks that
benefit from explicit reasoning, and adjust the generation budget accordingly.

## Evaluation

All reported deltas are calculated as **Qwen3.5-KETI-HAECHI-27B minus the
untouched official `Qwen/Qwen3.5-27B` checkpoint**. Percentage deltas are
absolute percentage points. Both models used matched API, chat-template,
thinking, stop-token, parser, and dataset settings.

### Qualitative comparison with the base model

#### Korean cultural-heritage recognition

| Target (reference) | Qwen3.5-27B base | Qwen3.5-KETI-HAECHI-27B |
|---|---|---|
| <img src="samples/qualitative/06_cheomseongdae.jpg" alt="첨성대" width="160"><br>[첨성대](https://commons.wikimedia.org/wiki/File:Cheomseongdae_Observatory_01.jpg) (`경주 첨성대`) | ❌ `경주 대릉원 석물` | ✅ `경주 첨성대` |
| <img src="samples/qualitative/01_geumdong_yeonga_buddha.jpg" alt="금동연가7년명여래입상" width="160"><br>금동연가7년명여래입상 | ❌ `금동약사여래입상` | ✅ `금동연가7년명여래입상` |
| <img src="samples/qualitative/02_white_porcelain_grape_monkey_jar.jpg" alt="백자 철화포도원숭이문 항아리" width="160"><br>백자 철화포도원숭이문 항아리 | ❌ `분청사기철화포도문호` | ✅ `백자 철화포도원숭이문 항아리` |
| <img src="samples/qualitative/03_muryeong_crown_ornament.jpg" alt="무령왕 금제 관식" width="160"><br>무령왕 금제 관식 | ❌ `금동관식` | ✅ `무령왕 금제 관식` |

#### Korean OCR

##### Font

| Target (reference) | Qwen3.5-27B base | Qwen3.5-KETI-HAECHI-27B |
|---|---|---|
| <img src="samples/qualitative/08_ocr_font_biseo.png" alt="비서 글꼴 OCR 샘플" width="200"><br>`비서` | ❌ `日1人→` | ✅ `비서` |
| <img src="samples/qualitative/09_ocr_font_palwol.png" alt="팔월 글꼴 OCR 샘플" width="200"><br>`팔월` | ❌ `파일` | ✅ `팔월` |
| <img src="samples/qualitative/13_ocr_font_tteodeulda.png" alt="떠들다 글꼴 OCR 샘플" width="200"><br>`떠들다` | ❌ `따라들다` | ✅ `떠들다` |
| <img src="samples/qualitative/14_ocr_font_beolgeum.png" alt="벌금 글꼴 OCR 샘플" width="200"><br>`벌금` | ❌ `별금` | ✅ `벌금` |

##### Outdoor

| Target (reference) | Qwen3.5-27B base | Qwen3.5-KETI-HAECHI-27B |
|---|---|---|
| <img src="samples/qualitative/10_ocr_outdoor_aiwon.png" alt="아이원 아동발달상담센터 실외 간판 OCR 샘플" width="200"><br>`아이원 아동발달상담센터` | ❌ `아아원`<br>`아동발달상담센터` | ✅ `아이원 아동발달상담센터` |
| <img src="samples/qualitative/11_ocr_outdoor_pil.png" alt="필 노래타운 실외 간판 OCR 샘플" width="200"><br>`필 노래타운` | ❌ `꿀 노래타운` | ✅ `필 노래타운` |
| <img src="samples/qualitative/15_ocr_outdoor_sunny_ne_hope.png" alt="써니네호프 실외 간판 OCR 샘플" width="200"><br>`써니네호프` | ❌ `서니네호프` | ✅ `써니네호프` |
| <img src="samples/qualitative/16_ocr_outdoor_mot_doen.png" alt="못된 실외 간판 OCR 샘플" width="200"><br>`못된` | ❌ `몬된` | ✅ `못된` |

##### Public exec

| Target (reference) | Qwen3.5-27B base | Qwen3.5-KETI-HAECHI-27B |
|---|---|---|
| <img src="samples/qualitative/12_ocr_public_landtax.png" alt="종합토지세 공공문서 OCR 샘플" width="200"><br>`종합토지세` | ❌ `홍합회포지`<br>`홍합회포지`<br>`홍합회포지` | ✅ `종합토지세` |
| <img src="samples/qualitative/17_ocr_public_yeongnak_cemetery.png" alt="영락공원묘지 공공문서 OCR 샘플" width="200"><br>`영락공원묘지` | ❌ `영락공원토지` | ✅ `영락공원묘지` |
| <img src="samples/qualitative/18_ocr_public_gimhae_market.png" alt="김해시장 전산정보과장 공공문서 OCR 샘플" width="200"><br>`김해시장(전산정보과장)` | ❌ `김해시청(전산정보과장)` | ✅ `김해시장(전산정보과장)` |

### Quantitative benchmarks

#### Korean cultural-heritage performance

| Benchmark | Official base | Qwen3.5-KETI-HAECHI-27B | Delta |
|---|---:|---:|---:|
| H400 direct exact | 0.92% | **38.07%** | +37.16 pp |
| H400 hard choice | 26.45% | **80.43%** | +53.98 pp |
| H400 knowledge image | 11.45% | **25.30%** | +13.85 pp |
| H400 knowledge text | 5.97% | **6.28%** | +0.31 pp |

H400 is an internal evaluation set built around 400 Korean cultural-heritage
items. It evaluates canonical-name recognition, fine-grained discrimination
among visually similar heritage items, and heritage knowledge grounded in
either images or text. H400 direct exact measures open-ended canonical-name
retrieval, whereas H400 hard is closed-set selection. Their large gap indicates
that recognition and discrimination are substantially stronger than exact
free-form naming.

#### Korean (Hangul) OCR performance

| Benchmark | Official base | Qwen3.5-KETI-HAECHI-27B | Delta |
|---|---:|---:|---:|
| `ocr_font` exact | 19.66% | 19.66% | +0.00 pp |
| `ocr_outdoor` exact | 36.13% | **41.41%** | +5.27 pp |
| `ocr_public_exec` exact | 4.17% | **5.21%** | +1.04 pp |

These Mammoth OCR results use strict exact match, where additional prose or
differences in spacing and normalization can cause an otherwise useful answer
to be marked incorrect.

#### Tool calling and long-horizon task performance

##### Tau2

| Benchmark | Official base | Qwen3.5-KETI-HAECHI-27B | Delta |
|---|---:|---:|---:|
| Tau2 airline (n=32) | 65.62% | **71.88%** | +6.25 pp |
| Tau2 retail (n=32) | 56.25% | **65.62%** | +9.38 pp |
| Tau2 telecom (n=32) | **87.50%** | 78.12% | -9.38 pp |
| Tau2 weighted overall (n=96) | 69.79% | **71.88%** | +2.08 pp |

Tau2 measures end-to-end success across multi-step airline, retail, and telecom
workflows. It improves overall, especially in airline and retail, although the
telecom domain declines.

##### BFCL V4

| Benchmark | Official base | Qwen3.5-KETI-HAECHI-27B | Delta |
|---|---:|---:|---:|
| Overall accuracy | **32.77%** | 32.11% | -0.66 pp |
| Non-Live AST accuracy | **89.60%** | 89.44% | -0.16 pp |
| Non-Live Simple AST | **79.42%** | 79.25% | -0.17 pp |
| Non-Live Multiple AST | 95.50% | 95.50% | +0.00 pp |
| Non-Live Parallel AST | **91.50%** | 91.00% | -0.50 pp |
| Non-Live Parallel Multiple AST | 92.00% | 92.00% | +0.00 pp |
| Multi-turn accuracy | **66.25%** | 64.50% | -1.75 pp |
| Multi-turn base | **76.50%** | 76.00% | -0.50 pp |
| Multi-turn missing function | **66.00%** | 64.00% | -2.00 pp |
| Multi-turn missing parameter | **53.00%** | 52.00% | -1.00 pp |
| Multi-turn long context | **69.50%** | 66.00% | -3.50 pp |

BFCL V4 measures structured function-call generation and multi-turn recovery
from missing functions or parameters. The small overall regression indicates
that tool calling and long-horizon performance remain sensitive to the
environment and task protocol.

#### General multimodal and language retention

| Benchmark | Official base | Qwen3.5-KETI-HAECHI-27B | Delta |
|---|---:|---:|---:|
| General-VL macro (6) | 45.44% | **77.60%** | +32.16 pp |
| MMBench DEV EN v1.1 | 30.42% | **90.63%** | +60.22 pp |
| MMStar | 39.40% | **77.33%** | +37.93 pp |
| MMStar-KO | 45.20% | **72.33%** | +27.13 pp |
| KRETA | 48.54% | **86.15%** | +37.60 pp |
| MMMU-Pro 10c | 44.28% | **61.85%** | +17.57 pp |
| HallusionBench aAcc | 64.77% | **77.29%** | +12.51 pp |
| OpenCompass Core | 63.49% | **64.80%** | +1.31 pp |
| OpenCompass Extra | 57.26% | **57.61%** | +0.35 pp |
| OpenCompass Korean | **17.18%** | 16.77% | -0.41 pp |

See the [detailed score report](reports/DETAILED_SCORE_REPORT.md) for all 148
metrics, the [benchmark guide](reports/BENCHMARK_GUIDE.md) for definitions and
caveats, and the [machine-readable results](reports/EVALUATION_RESULTS.json) for
downstream analysis.

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
education, archival metadata, and research outputs. Do not treat model output as
evidence of authenticity or provenance. Avoid submitting sensitive or personal
documents for OCR unless the deployment provides appropriate privacy controls.

## Limitations

- OCR outputs may omit text, normalize spelling incorrectly, or add unsupported
  text.
- The model can hallucinate names, dates, designations, provenance, and
  historical claims. Similar-looking artifacts and uncommon viewpoints are
  especially challenging.
- General multilingual, video, robustness, demographic-bias, privacy, and
  safety behavior were not comprehensively evaluated for this release.
- As with the base model, generated content may be inaccurate, biased, unsafe,
  or unsuitable for the user's context.

## Core contributors

- **San Kim** ([kimsan0622@keti.re.kr](mailto:kimsan0622@keti.re.kr)) — Led
  long-context agent task performance and development/management of the main training
  loop.
- **Byunggill Joe** ([byunggill@keti.re.kr](mailto:byunggill@keti.re.kr)) —
  Secured GPU compute resources through the support program and led Korean
  cultural-heritage recognition/OCR performance.

## Acknowledgements

Qwen3.5-KETI-HAECHI-27B was developed using compute resources provided through
the `첨단 GPU 활용 지원 사업` of the National IT Industry Promotion Agency
(NIPA; 정보통신산업진흥원).

## License and attribution

This derivative checkpoint is released under the [Apache License 2.0](LICENSE),
following the upstream
[`Qwen/Qwen3.5-27B`](https://huggingface.co/Qwen/Qwen3.5-27B) license. Use of
third-party data and generated outputs may be subject to additional terms.
Please acknowledge the Qwen team and cite the upstream model when using this
checkpoint in published work.

## Citation

```bibtex
@misc{qwen35_keti_haechi_27b,
  title        = {Qwen3.5-KETI-HAECHI-27B},
  author       = {Kim, San and Joe, Byunggill},
  year         = {2026},
  howpublished = {Hugging Face model repository},
  url          = {https://huggingface.co/KETI-AIR/Qwen3.5-KETI-HAECHI-27B}
}
```

## 한국어 요약

이 모델은 `Qwen/Qwen3.5-27B`를 기반으로 두 가지 목적을 위해 개발한
멀티모달 모델입니다. 첫 번째 목적은 한국 문화유산의 정확한 명칭 식별, 이미지
기반 문화유산 질의응답, 한글 OCR 능력을 향상하는 것입니다. 두 번째 목적은
적절한 도구를 호출하고 여러 단계에 걸쳐 정보를 기억하며 변화하는 상태를
추적하는 장기작업 수행 능력을 향상하는 것입니다.

공식 베이스 모델과 동일한 조건의 내부 평가에서 H400 직접 식별 정확도는
0.92%에서 38.07%로, H400 유사 문화재 선택 정확도는 26.45%에서 80.43%로
향상되었습니다. 장기작업 평가인 Tau2 가중 점수는 69.79%에서 71.88%로
향상되었습니다. 다만 세부 환경에 따라 성능 차이가 있으므로, 실제 에이전트
작업에서는 단계별 상태 확인과 실패 복구 절차를 함께 적용하는 것을 권장합니다.
