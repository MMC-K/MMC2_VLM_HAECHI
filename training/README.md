# 27B·32B 학습 코드와 실험 레시피

이 폴더는 기존 학습 구현과 모델 배포 패키지에 보존된 학습 설정을 함께 제공합니다. 공통 SFT 구현과 배포 모델의 단계별 학습 레시피는 서로 다른 경로입니다.

## 공통 SFT 구현

- `generic_sft/VLM_SFT_Custom_Data_Qwen3_5/3_vlm_sft_distributed.py`: Qwen3.5 모델, messages+images 데이터, 응답 구간 loss masking, FSDP 학습.
- `generic_sft/VLM_SFT_Custom_Data_HyperClovaX/3_vlm_sft_distributed.py`: HyperCLOVA 모델의 데이터 처리와 분산 SFT. 원본 기본 모델명은 8B이므로 **32B 실험에는 아래처럼 모델을 명시**합니다.
- 각 `Dockerfile`은 원본 학습 의존성을 보존합니다. 추론용 `.venv-qwen`·`.venv-hyperclova`와 학습 환경은 별개입니다.
- 동봉 `trainer.py`는 원본 학습 보조 코드입니다. 원본 동작을 확인할 수 있도록 보존했습니다.

입력은 Hugging Face `load_from_disk`로 읽을 수 있는 로컬 데이터셋이며, Qwen의 non-packed 입력에는 `messages`·`images` 열이 필요합니다. 원천 학습 데이터와 대규모 학습 가중치는 포함하지 않습니다.

## Qwen 27B 공통 SFT 실행 예

해당 `Dockerfile`로 환경을 준비한 뒤 GPU·데이터 경로를 조정합니다. 다음 명령은 공통 SFT 시작 예이며 배포 HAECHI의 다단계 레시피 재현 명령이 아닙니다.

```bash
cd training/generic_sft/VLM_SFT_Custom_Data_Qwen3_5
# 로컬 컨테이너 이미지 빌드
# docker build -t haechi-qwen-sft .

torchrun --standalone --nproc_per_node=8 3_vlm_sft_distributed.py \
  --model_name Qwen/Qwen3.5-27B \
  --data_path /data/vlm_sft_dataset \
  --output_path /data/checkpoints/qwen27b-sft \
  --logging_dir /data/log/qwen27b-sft \
  --attn_implementation sdpa
```

## HyperCLOVA 32B 공통 SFT 실행 예

```bash
cd training/generic_sft/VLM_SFT_Custom_Data_HyperClovaX
# docker build -t haechi-hyperclova-sft .
torchrun --standalone --nproc_per_node=8 3_vlm_sft_distributed.py \
  --model_name naver-hyperclovax/HyperCLOVAX-SEED-Think-32B \
  --data_path /data/vlm_sft_dataset \
  --output_path /data/checkpoints/hyperclova32b-sft
```

GPU 수,FSDP 설정, 컨테이너·라이브러리 호환성 및 데이터 형식은 실행 환경에 맞춰 확인해야 합니다. 이번 공개 정리에서 대규모 학습을 다시 수행하지 않았습니다.

## 배포 모델의 실제 학습 기록

| 모델 | 보존 자료 |
| --- | --- |
| Qwen 27B | `large_models/qwen/configs/01...06` 단계별 설정, `reproduction/run_end_to_end.sh`, 평가 gate, 리포트·패키징 도구 |
| HyperCLOVA 32B | `large_models/hyperclova/reports/TRAINING_CONFIG.yaml`, BF16 변환·응답 사례 추출·패키징 도구 |

Qwen 레시피는 HSM specialist → task-vector merge → H400 Stage A → H300 identity acquisition → H400/HS100 scale-up → HF 변환 순서입니다. HyperCLOVA 설정에는 16노드 × 노드당 8 GPU, 최종 2,500 step, vision encoder 고정과 visual merger 학습 등의 조건이 기록되어 있습니다. 정확한 비율과 하이퍼파라미터는 해당 YAML을 기준으로 확인합니다.

원본 YAML과 연계 스크립트의 `/data/workspace`, 레지스트리, namespace, PVC 및 데이터 경로는 당시 클러스터의 값입니다. 원본 레시피가 참조하는 `sft_training_code/qwen35_multimodal_sft.py`, `sft_training_code/hyperclovax_multimodal_sft.py`, 일부 병합 도구와 외부 데이터는 제공된 로컬 패키지에서 찾을 수 없어 이 저장소에 포함하지 못했습니다. 따라서 원본 클러스터 레시피는 보존된 실행 기록으로 읽고, 동일 실행의 완전한 재현에는 해당 의존성을 별도로 확보해야 합니다.

## 점수 기록의 구분

`large_models/*/reports`는 2026-09 배포 패키지의 기존 벤치마크 기록입니다. 최상위 README와 첨부 V2.0 분석서는 `evaluation/2026-11-16`의 고정 표본 결과를 사용합니다. 데이터·시점·지표가 다른 두 결과를 한 표본의 결과로 합산하지 않습니다.
