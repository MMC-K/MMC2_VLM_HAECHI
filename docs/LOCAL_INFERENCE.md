# KETI HAECHI 로컬 실행 프로젝트

이 제출본은 실행 코드와 문서만 포함합니다. **모델 가중치와 가상환경은 포함하지 않으므로**, 받는 사람이 아래 순서대로 환경을 설치하고 Hugging Face에서 모델을 다운로드해야 합니다. 사용 예시는 이미지 추론으로 구성했습니다. 모델은 한 번에 하나씩 실행하며, 모든 추론은 **물리 GPU 3번**으로 고정됩니다.

| CLI 이름 | Hugging Face 저장소 | 실행 방식 |
| --- | --- | --- |
| `qwen` | [KETI-NLP/Qwen3.5-KETI-HAECHI-27B](https://huggingface.co/KETI-NLP/Qwen3.5-KETI-HAECHI-27B) | AutoModelForMultimodalLM / generate |
| `hyperclova` | [KETI-NLP/HyperCLOVA-X-KETI-HAECHI-32B](https://huggingface.co/KETI-NLP/HyperCLOVA-X-KETI-HAECHI-32B) | 저장소의 HCXVisionForCausalLM / inference |

## 처음 실행하는 순서

압축을 풀고 프로젝트 폴더로 이동한 뒤 다음 명령을 순서대로 실행하세요. 아래 경로는 압축을 푼 위치에 맞게 조정합니다. 두 모델 중 필요한 모델만 설치·다운로드해도 됩니다.

```bash
cd haechi_runner

# 1) 모델별 가상환경과 패키지 설치
bash setup.sh qwen
bash setup.sh hyperclova

# 2) 검증에 사용한 리비전의 모델 전체 다운로드
.venv-qwen/bin/python haechi.py download --model qwen \
  --revision 259830921a2f45322018c496b123ce075511286e
.venv-hyperclova/bin/python haechi.py download --model hyperclova \
  --revision 776bf4ac7207f47f171a00b81ac4f161880f156d

# 3) 다운로드한 저장소의 예제 이미지로 추론 (한 모델씩 순서대로 실행)
bash run.sh qwen --sample \
  --prompt '사진 속 국가유산의 정확한 공식 명칭만 답하세요. 설명은 쓰지 마세요.' \
  --max-new-tokens 32
bash run.sh hyperclova --sample \
  --prompt '사진 속 국가유산의 정확한 공식 명칭만 답하세요. 설명은 쓰지 마세요.' \
  --max-new-tokens 32
```

검증 환경에서 확인한 응답은 Qwen의 `경주 첨성대`, HyperCLOVA의 `경복궁 경회루`입니다. `--sample` 이미지는 모델 다운로드 시 함께 받아지므로 별도의 사진을 준비할 필요가 없습니다. 최초 실행에는 인터넷이 필요하며, 설치와 다운로드를 마친 뒤에는 로컬 파일로 추론합니다. 압축 해제 시 실행 권한이 없어도 위처럼 `bash run.sh`로 실행할 수 있습니다.

`run.sh`는 자신의 위치에서 `.venv-<모델명>/bin/python`을 찾아 `haechi.py run`을 실행합니다. 가상환경을 직접 활성화할 필요가 없습니다. 이미지와 사용자 지정 `--model-dir`의 상대 경로는 명령을 실행한 현재 폴더 기준입니다. 한 번 호출하면 질문 하나에 답한 뒤 종료합니다.

## 1. 준비 및 설치

Linux, Python 3.10 이상(검증 버전 3.12), Git, Python venv 모듈, NVIDIA 드라이버가 필요합니다. GPU 3번이 존재하고 사용 가능한지 `nvidia-smi -i 3`으로 확인하세요. 설치 스크립트는 CUDA 지원 PyTorch를 포함한 패키지를 설치합니다. 모델 카드에 안내된 torch 2.9.1 / torchvision 0.24.1 조합을 사용합니다. Qwen은 카드에서 지정한 Transformers 커밋, HyperCLOVA는 Transformers 4.57 이상 5 미만이므로 **별도 가상환경**을 만듭니다. 기존 프로젝트 환경을 활성화할 필요가 없습니다.

```bash
cd haechi_runner
bash setup.sh qwen
bash setup.sh hyperclova
```

두 모델 가중치는 합계 약 **121GB**입니다. 가상환경과 설치 캐시까지 고려해 여유 디스크 **180GB 이상을 권장**합니다. 다운로드 시간은 네트워크 속도에 따라 달라집니다.

접근 거부 또는 인증 오류가 발생하면 모델 페이지에서 접근 조건을 확인하고 해당 환경으로 로그인한 뒤 다운로드를 다시 실행하세요.

```bash
.venv-qwen/bin/hf auth login
.venv-hyperclova/bin/hf auth login
```

`HF_TOKEN` 환경변수도 사용할 수 있습니다. 토큰이나 인증 정보는 제출 파일에 포함하지 마세요.

BF16 가중치만 단순 계산하면 27B는 약 54GB, 32B는 약 64GB이며 실제 다운로드 크기와 추론 메모리는 부가 구성요소에 따라 더 커집니다. GPU 3번은 확인 시 A100 80GB였지만 단일 GPU 적합성은 실제 입력 길이와 메모리 사용량에 따라 달라집니다. 특히 HyperCLOVA 모델 카드의 검증 환경은 80GB GPU 2장입니다. 이 프로젝트는 요청에 따라 GPU 3번 한 장만 사용하며 다른 GPU로 분산하지 않습니다. 실제 검증에서 HyperCLOVA의 텍스트·샘플 이미지 추론은 이 GPU 한 장에서 성공했습니다.

## 2. 모델 다운로드

```bash
.venv-qwen/bin/python haechi.py download --model qwen
.venv-hyperclova/bin/python haechi.py download --model hyperclova
```

기본 저장 위치는 프로젝트 아래 `models/qwen`, `models/hyperclova`이며 다운로드 명령이 폴더를 생성합니다. 가중치, 프로세서, 사용자 정의 코드, 예제 이미지를 포함한 저장소 전체를 다운로드합니다. 중단 후 같은 명령을 실행하면 Hugging Face가 이미 받은 파일을 재사용합니다. 다운로드에는 GPU가 필요하지 않습니다.

다른 저장 경로 또는 고정 리비전을 사용하려면:

```bash
.venv-qwen/bin/python haechi.py download --model qwen \
  --model-dir /data/models/haechi-qwen --revision main
```

위 일반 다운로드 명령은 최신 `main`을 사용합니다. 검증한 모델을 그대로 받으려면 문서 처음의 커밋 SHA가 지정된 명령을 사용하세요. 사용자 경로에 다운로드했다면 실행 시에도 동일한 `--model-dir`을 전달합니다. 실행 코드는 로컬 파일만 사용하므로 먼저 다운로드해야 합니다.

## 3. 이미지 추론 및 모델 카드 예제

직접 준비한 로컬 이미지 (`photo.jpg`를 실제 이미지 경로로 바꾸세요):

```bash
bash run.sh qwen --image ./photo.jpg --prompt '이미지 속 한글을 읽어 주세요.'
bash run.sh hyperclova --image ./photo.jpg --prompt '이미지 속 한글을 읽어 주세요.'
```

Python CLI로 직접 실행할 수도 있습니다:

```bash
.venv-qwen/bin/python haechi.py run --model qwen \
  --image /absolute/path/photo.jpg --prompt '이미지 속 한글을 읽어 주세요.'

.venv-hyperclova/bin/python haechi.py run --model hyperclova \
  --image /absolute/path/photo.jpg --prompt '이미지 속 한글을 읽어 주세요.'
```

모델 저장소에 포함된 예제 이미지로 실행:

```bash
.venv-qwen/bin/python haechi.py run --model qwen --sample \
  --prompt '사진 속 국가유산의 정확한 공식 명칭만 답하세요. 설명은 쓰지 마세요.' \
  --max-new-tokens 32

.venv-hyperclova/bin/python haechi.py run --model hyperclova --sample \
  --prompt '사진 속 국가유산의 정확한 공식 명칭만 답하세요. 설명은 쓰지 마세요.' \
  --max-new-tokens 32
```

`--sample`은 Qwen에는 첨성대, HyperCLOVA에는 경회루 샘플을 선택합니다. 실제 GPU 3번에서 각각 `경주 첨성대`, `경복궁 경회루` 응답을 확인했습니다.

## 4. 옵션과 코드 흐름

```bash
.venv-qwen/bin/python haechi.py run --help
.venv-qwen/bin/python haechi.py run --model qwen \
  --sample --thinking --max-new-tokens 1024 \
  --prompt '사진 속 국가유산을 식별하고, 그렇게 판단한 시각적 근거를 설명해 주세요.'
```

- `--max-new-tokens`: 기본 생성 예산 256. HyperCLOVA에서는 해당 모델 카드와 같이 사용자 정의 `inference(max_length=...)` 인자로 전달합니다.
- `--thinking`: 추론 모드 활성화. 기본은 비활성화입니다. 충분한 생성 예산을 지정하세요.
- `--image`: 로컬 이미지 경로. `--sample`과 동시에 사용할 수 없습니다.
- `--model-dir`: 모델 파일이 저장된 로컬 디렉터리.

`haechi.py`는 torch를 불러오기 전에 `CUDA_DEVICE_ORDER=PCI_BUS_ID`, `CUDA_VISIBLE_DEVICES=3`을 설정합니다. 프로세스 내부의 `cuda:0`은 물리 GPU 3번을 뜻합니다. `device_map={'': 0}`으로 모델 전체를 그 GPU에 올립니다.

Qwen은 `AutoProcessor.apply_chat_template()`에 `enable_thinking`을 전달하고, `generate()` 출력에서 입력 토큰을 제외한 답변을 디코딩합니다. HyperCLOVA는 저장소의 사용자 정의 코드를 실행하는 `trust_remote_code=True`가 필요합니다. 모델 카드에 나온 동적 클래스 로딩과 SDPA 폴백을 사용해 별도 flash-attn 설치 없이 실행하도록 구성했습니다. 이미지가 있으면 RGB로 변환하고 카드에 명시된 픽셀 범위를 적용합니다. HyperCLOVA 이미지 응답은 사용자 정의 `inference()` 결과를 그대로 디코딩합니다. 텍스트만 입력하면 내부 `language_model.generate()`를 사용하고 입력 토큰을 제외합니다. 원본 설정에 남은 외부 코드 경로는 메모리상의 `text_config._name_or_path`를 로컬 디렉터리로 바꿔 해결합니다. 모델 파일 자체는 수정하지 않습니다. 사용자 정의 코드 로딩에 필요한 `importlib_metadata`도 의존성에 포함했습니다.

## 5. 오류 확인

- CUDA OOM: GPU 3번의 다른 작업을 확인하고 입력 이미지 크기, 프롬프트 길이, 생성 예산을 줄이세요. 두 모델을 동시에 실행하지 마세요. 여전히 부족하면 별도 양자화 또는 CPU 오프로딩 구성이 필요합니다(현재 미구현).
- Qwen 클래스 import 오류: `.venv-qwen` 환경과 `requirements-qwen.txt` 설치 여부를 확인하세요.
- HyperCLOVA 호환 오류: `.venv-hyperclova` 및 Transformers 4.x를 사용하세요.
- torchvision 관련 오류: torch와 torchvision의 버전 및 CUDA 빌드가 맞는지 확인하세요.
- 접근 거부: 모델 페이지의 접근 조건, 로그인 상태와 토큰 권한을 확인하세요.
- Qwen의 `causal_conv1d`, `flash-linear-attention` 미설치 안내: 기본 PyTorch 폴백으로 동작합니다. 정확성 오류는 아니지만 추론이 느릴 수 있습니다. 현재 환경은 별도 최적화 커널 없이 실제 추론을 검증했습니다.
- 예제 이미지 없음: 다운로드를 완료했는지 확인하거나 `--image`로 직접 이미지를 지정하세요.

## 참고 및 라이선스

2026-11-13에 두 저장소의 **Quickstart 본문**과 HyperCLOVA 사용자 정의 코드를 확인해 구현했습니다. 모델 카드 본문 일부 예제의 `KETI-AIR` 표기 대신 사용자가 지정한 실제 저장소 `KETI-NLP`를 사용합니다. 웹페이지의 자동 생성 배포 예제보다 모델 작성자의 직접 실행 예제를 기준으로 삼았습니다.

- [Qwen 모델 카드 / Quickstart](https://huggingface.co/KETI-NLP/Qwen3.5-KETI-HAECHI-27B#quickstart): Transformers 커밋, 멀티모달 입력, thinking 설정, 출력 디코딩 참고.
- [HyperCLOVA 모델 카드 / Quickstart](https://huggingface.co/KETI-NLP/HyperCLOVA-X-KETI-HAECHI-32B#quickstart): 버전 범위, 사용자 정의 클래스, SDPA 폴백 및 inference 사용법 참고.
- Qwen 모델 카드 라이선스 표기는 Apache-2.0, HyperCLOVA는 HyperCLOVA X 라이선스입니다. 모델 사용 및 배포 시 각 저장소의 실제 라이선스를 확인하세요.

## 실제 실행 검증 (2026-11-13)

개발 서버에서 환경 설치와 가중치 다운로드를 완료한 뒤 확인한 기록입니다. 제출본에는 해당 서버의 모델과 가상환경을 포함하지 않습니다. A100 80GB **물리 GPU 3번 한 장**, BF16, thinking 비활성화, 생성 예산 32로 각 명령을 순서대로 실행했습니다. 아래 이미지 추론 모두 종료 코드 0입니다.

| 모델 | 입력 | 실제 응답 |
| --- | --- | --- |
| Qwen | 저장소 첨성대 이미지 / 공식 명칭 요청 | 경주 첨성대 |
| HyperCLOVA | 저장소 경회루 이미지 / 공식 명칭 요청 | 경복궁 경회루 |

두 환경의 `pip check`, 다운로드 CLI 재실행도 통과했습니다. 모든 safetensors 가중치는 Hub에 명시된 SHA-256과 대조했습니다. 검증한 모델 리비전과 결과는 [verification.json](verification.json)에 기록했습니다.

검증 과정에서 HyperCLOVA의 로컬 사용자 정의 코드 경로, 텍스트 전용 생성 경로, 누락된 `importlib_metadata` 의존성을 수정했습니다. 사용한 전체 패키지 버전은 `requirements-qwen.lock.txt`, `requirements-hyperclova.lock.txt`에 저장했습니다. 동일 환경을 새로 만들 때 해당 lock 파일을 `pip install -r`로 설치할 수 있습니다.

초기 대용량 전송에서 일부 연결이 지연되어 구간 재시도로 보완하고 체크섬을 검증했습니다. 받는 사람의 환경에서도 전송 속도에 따라 다운로드가 오래 걸릴 수 있습니다. `verification.json`의 로그 파일명은 개발 서버의 기록을 가리키며, 원본 로그 파일은 제출본에 포함하지 않습니다.

위 표는 이미지 추론 2건의 동작 확인 결과입니다. 전체 검증 기록은 `verification.json`에 보관했습니다. 장문 입력, 대규모 이미지, thinking 모드의 품질·속도·메모리 한도는 별도 측정하지 않았습니다.

## 모델 없이 제출용 ZIP 만들기

프로젝트의 **상위 폴더**에서 다음 명령을 실행하면 코드·문서·의존성 목록·검증 기록만 포함한 새 ZIP을 만듭니다. 출력 ZIP 파일이 이미 있다면 다른 이름을 지정하세요. `zip`은 기존 ZIP에 파일을 추가할 수 있으므로, 예전 전체 압축파일을 그대로 재사용하지 마세요.

```bash
zip -9 haechi_runner_submission.zip \
  haechi_runner/README.md \
  haechi_runner/haechi.py \
  haechi_runner/run.sh \
  haechi_runner/setup.sh \
  haechi_runner/requirements-qwen.txt \
  haechi_runner/requirements-hyperclova.txt \
  haechi_runner/requirements-qwen.lock.txt \
  haechi_runner/requirements-hyperclova.lock.txt \
  haechi_runner/verification.json \
  haechi_runner/.gitignore
```

제출 구성은 위 10개 파일입니다. `models/`, `.venv-*/`, `wheelhouse/`, 캐시, 로그, 인증 정보는 포함하지 않습니다. `.gitignore`만으로 ZIP에서 자동 제외되는 것은 아니므로 위처럼 포함할 파일을 직접 지정하세요. 받는 사람은 압축 해제 후 문서 처음의 **설치 → 다운로드 → 이미지 추론** 순서로 진행하면 됩니다.
