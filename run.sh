#!/usr/bin/env bash
set -euo pipefail

# 스크립트 위치를 기준으로 모델별 가상환경을 선택합니다.
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if [[ $# -eq 0 || "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  echo '사용법: ./run.sh {qwen|hyperclova} [추론 옵션]'
  echo '이미지: ./run.sh hyperclova --image ./photo.jpg --prompt "사진을 설명해 주세요."'
  echo '샘플:   ./run.sh qwen --sample --prompt "사진 속 국가유산의 공식 명칭만 답하세요." --max-new-tokens 32'
  exit 0
fi

model="$1"
shift
case "$model" in
  qwen|hyperclova) ;;
  *) echo '모델은 qwen 또는 hyperclova를 지정하세요.' >&2; exit 2 ;;
esac

python_bin="$project_dir/.venv-$model/bin/python"
if [[ ! -x "$python_bin" ]]; then
  echo "가상환경이 없습니다. 먼저 실행하세요: bash \"$project_dir/setup.sh\" $model" >&2
  exit 1
fi

# 물리 GPU 3번만 사용합니다. 프로세스 내부에서는 cuda:0입니다.
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_VISIBLE_DEVICES=3

# 나머지 옵션을 그대로 전달하며, 선택한 모델의 환경에서 추론합니다.
exec "$python_bin" "$project_dir/haechi.py" run "$@" --model "$model"
