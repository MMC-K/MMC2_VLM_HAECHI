# 27B·32B 모델 평가

`2026-11-16`에는 두 계열의 학습 전·후 저장 응답과 실행 메타데이터, 입력·정답·이미지를 보존했습니다. V2.0 분석서는 이 중 국가유산 명칭 식별과 한글 OCR 각 100문항을 다룹니다. 추가 지식 질문 100문항과 LLM 채점은 별도의 보충 기록입니다.

## 저장 결과 확인

```bash
python scripts/verify_release.py
python evaluation/2026-11-16/score_results.py
```

재채점은 GPU·모델 다운로드 없이 실행됩니다. `score_results.py`는 기존 저장 응답에서 `*_scores.json`, `summary.json`, CSV를 다시 만듭니다. 원본을 보존하려면 별도 checkout에서 실행하세요. `verify_release.py`는 원본 파일을 수정하지 않고 해시·문항 정렬·오류 여부·지표를 확인합니다.

EM은 NFKC 정규화 후 영문 소문자·숫자·한글만 남긴 문자열의 일치율입니다. 엄격 일치율은 NFC 정규화와 양끝 공백 제거 후 비교합니다. CER은 전체 표본의 문자 편집 거리 합을 정답 문자 수 합으로 나눈 값입니다. `similarity`·`contains`는 과거 보충 지표로 원본에 남아 있으나 V2.0 분석서의 두 과제 핵심 지표와 구분합니다.

## 학습 후 모델 재추론

최상위 README의 모델 설치·다운로드를 먼저 완료합니다. 출력 이름을 분리하면 기존 결과를 보존할 수 있습니다.

```bash
.venv-qwen/bin/python evaluation/2026-11-16/run_benchmark.py \
  --model qwen --stage haechi --output-tag rerun1
.venv-hyperclova/bin/python evaluation/2026-11-16/run_benchmark.py \
  --model hyperclova --stage haechi --output-tag rerun1
```

`--limit 3`으로 소규모 동작 점검이 가능합니다. 같은 출력 이름의 저장 응답이 존재하면 완료된 문항은 건너뜁니다. 기본 입력은 보충 지식 과제를 포함한 300문항입니다. V2.0의 두 과제만 추론하려면 `inputs.jsonl`에서 `task != "h400_knowledge_image"`인 행을 별도 JSONL로 만든 뒤 `--inputs`로 전달합니다. 이 부분집합에는 기존 300문항 전용 집계 대신 별도 집계가 필요합니다.

원본 입력 JSONL의 이미지 필드는 당시의 절대 경로입니다. 공개본 runner는 해당 파일이 없으면 같은 파일명의 동봉 `images/`로 해석하며, 입력 파일과 원본 해시는 변경하지 않습니다.

## 학습 전 모델 재추론

기반 모델은 HAECHI 모델과 별도로 준비합니다. 아래 다운로드는 GPU를 사용하지 않습니다.

```bash
.venv-qwen/bin/hf download Qwen/Qwen3.5-27B --local-dir base_models/Qwen3.5-27B
.venv-hyperclova/bin/hf download naver-hyperclovax/HyperCLOVAX-SEED-Think-32B \
  --local-dir base_models/HyperCLOVAX-SEED-Think-32B

.venv-qwen/bin/python evaluation/2026-11-16/run_benchmark.py \
  --model qwen --stage base --output-tag rerun1
.venv-hyperclova/bin/python evaluation/2026-11-16/run_benchmark.py \
  --model hyperclova --stage base --output-tag rerun1
```

다른 모델 루트는 `HAECHI_BASE_MODELS=/absolute/path`로 지정합니다. 위 `hf download` 명령은 현재 기본 리비전을 받으므로 과거 실험과 동일 리비전을 원하면 `*_run.json` 및 `base_weight_checksums.json`의 메타데이터와 대조해야 합니다. 각 쌍은 HAECHI 쪽 프로세서를 공통 사용합니다.

## 속도·메모리 기록과 커널

물리 GPU 3번, CPU thread 8개를 사용합니다. 첫 문항을 warm-up한 뒤 문항별 생성 시간과 peak allocated/reserved 메모리를 저장했습니다.

원본 Qwen 시간 측정에는 `flash-linear-attention==0.6.0`, `causal-conv1d==1.7.0`이 사용되었습니다. 이 추가 커널은 설치가 필요하며 vendored 소스·컴파일 바이너리는 이 저장소에 포함하지 않습니다. 모델 환경과 CUDA 호환성을 확인하고 별도로 설치하세요. 설치하지 않은 fallback 실행의 속도는 원본 최적화 경로의 속도와 직접 비교하지 않습니다. 정확한 기존 패키지 버전은 `requirements-*-eval.lock.txt`와 `*_run.json`에 보존했습니다.

`verify_patch_projection.py`는 visual patch projection의 BF16 수치 동등성을 확인한 원본 코드입니다. 모델 파일이 필요한 GPU 점검이며 공개 정리 중 재실행하지 않았습니다.

## 추가 지식 응답과 LLM 채점

`2026-11-17-llm-judge`는 추가 국가유산 지식 질문에 대해 저장된 응답을 재채점한 기록입니다. `gemini-3.5-flash-lite`의 모델명·판정 기준·실제 API 응답을 보존했으며, 최초 유효 판정을 사용했습니다. 사람에 의한 정답 검증으로 해석하지 않습니다.

`run_judge.py` 재실행은 외부 API 호출을 발생시킵니다. 이번 공개 작업에서는 API를 호출하지 않았습니다. `private_mapping.json`은 모델 블라인드 ID 대응표이며 인증 정보가 아닙니다. 동봉 해시·manifest는 당시 실행을 가리키며 현재 새 실행과 구분합니다.
