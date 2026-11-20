#!/usr/bin/env bash
set -euo pipefail

KUBECONFIG_PATH=${KUBECONFIG_PATH-/home/san/backup/mlxp/keti-airc-h200-128-kubeconfig.yaml}
NAMESPACE=${NAMESPACE:-p-keti-airc-h200-128}
DEPLOYMENT=${DEPLOYMENT:-vllm-q35-mm-e1b-s100-16n}
REPLICAS=${REPLICAS:-16}
DETACH=${DETACH:-false}
ROOT=${ROOT:-/home/san/backup/mlxp}
RUN_TAG=${RUN_TAG:-20260831}
MODEL_DIR=${MODEL_DIR:-/data/workspace/post-training/outputs/qwen35-27b-official-h400-hs100-scale2500-step2500-hf}
SERVED_MODEL=${SERVED_MODEL:-qwen35-27b-h400-hs100-scale2500}
MODEL_LABEL=${MODEL_LABEL:-qwen35-27b-h400-hs100-scale2500}
REMOTE_EVAL_ROOT=/data/workspace/eval_models
RESULT_SLUG=${RESULT_SLUG:-q35-27b-h400-hs100-s2500-${RUN_TAG}}
JOB_STEM=${JOB_STEM:-q35-27b-hs25}
MODEL_KEY=${MODEL_KEY:-qwen35_27b_hs25}
MODEL_API_BASE=${MODEL_API_BASE:-http://vllm-qwen35-9b-sft-no-reasoning:8000/v1}
CHAT_TEMPLATE_THINKING_KEY=${CHAT_TEMPLATE_THINKING_KEY:-enable_thinking}
CHAT_TEMPLATE_THINKING_VALUE=${CHAT_TEMPLATE_THINKING_VALUE:-True}
OPENCOMPASS_STOP_TOKEN_IDS=${OPENCOMPASS_STOP_TOKEN_IDS:-248044, 248046}
MAMMOTH_STOP_TOKEN_IDS=${MAMMOTH_STOP_TOKEN_IDS:-248044,248046}
MAMMOTH_THINKING_KEY=${MAMMOTH_THINKING_KEY:-enable_thinking}
MAMMOTH_ENABLE_THINKING=${MAMMOTH_ENABLE_THINKING:-false}
HERITAGE_ANSWER_MAP=/data/image_dataset/mammothvl2_korean_ocr_openai_compat/heritage_simple_answer_map_v2.json

MAMMOTH_TEMPLATE=${ROOT}/kubectl_yml/eval_mammoth_e2_replay_step250_indexed_job.yaml
BFCL_TEMPLATE=${ROOT}/kubectl_yml/bfcl_v4_qwen35_9b_mm_e2_step250_job.yaml
STATEFUL_TEMPLATE=${ROOT}/kubectl_yml/stateful_tool_eval_qwen35_9b_mm_e2_step250.yaml
HERITAGE_TEMPLATE=${ROOT}/kubectl_yml/eval_cultural_heritage_focus_top2k_indexed_job.yaml
VL_TEMPLATE=${ROOT}/kubectl_yml/vl_gate_qwen35_27b_official_baseline_job.yaml
OPENCOMPASS_TEMPLATE=${ROOT}/kubectl_yml/opencompass_qwen35_9b_heritage_shared_visualfreeze_full_epoch_eval_all_job.yaml
TAU3_TEMPLATE=${ROOT}/kubectl_yml/tau3_qwen35_9b_mm_e2_step250_full_eval.yaml
HERITAGE_SUMMARIZER=${REMOTE_EVAL_ROOT}/scripts/cultural_heritage_focus_eval.py
FULL_TAU3_JOB=tau3full-${JOB_STEM}-${RUN_TAG}
FULL_TAU3_ROOT=${REMOTE_EVAL_ROOT}/tau3_axes/${RESULT_SLUG}-full
ASYNC_TAU3_LAUNCHED=false

if [[ -n ${KUBECONFIG_PATH} ]]; then
  export KUBECONFIG=${KUBECONFIG_PATH}
else
  unset KUBECONFIG
fi

log() {
  printf '[%s] %s\n' "$(date '+%F %T')" "$*"
}

jobs=(
  mam-${JOB_STEM}-${RUN_TAG}
  vl-${JOB_STEM}-${RUN_TAG}
  bfcl-${JOB_STEM}-${RUN_TAG}
  ts-${JOB_STEM}-${RUN_TAG}
  tau2-${JOB_STEM}-${RUN_TAG}
  her-${JOB_STEM}-${RUN_TAG}
  ocall-${JOB_STEM}-${RUN_TAG}
  ocextra-${JOB_STEM}-${RUN_TAG}
  ocko-${JOB_STEM}-${RUN_TAG}
  tau3-${JOB_STEM}-${RUN_TAG}
)

cleanup() {
  local exit_code=$?
  if (( exit_code == 0 )) && [[ ${ASYNC_TAU3_LAUNCHED} == false ]]; then
    kubectl -n "${NAMESPACE}" scale deployment "${DEPLOYMENT}" --replicas=0 >/dev/null || true
  elif (( exit_code == 0 )); then
    log "Full tau3 is running asynchronously; its monitor will release ${DEPLOYMENT}"
  else
    log "Evaluation failed; leaving ${DEPLOYMENT} running for inspection"
  fi
}
trap cleanup EXIT

wait_for_jobs() {
  local deadline=$((SECONDS + 43200))
  while (( SECONDS < deadline )); do
    local complete=0 failed_count=0 job condition failed
    for job in "${jobs[@]}"; do
      condition=$(kubectl -n "${NAMESPACE}" get job "${job}" -o jsonpath='{.status.conditions[?(@.type=="Complete")].status}')
      failed=$(kubectl -n "${NAMESPACE}" get job "${job}" -o jsonpath='{.status.conditions[?(@.type=="Failed")].status}')
      if [[ ${condition:-} == True ]]; then
        complete=$((complete + 1))
      elif [[ ${failed:-} == True ]]; then
        failed_count=$((failed_count + 1))
        kubectl -n "${NAMESPACE}" logs job/"${job}" --all-containers --prefix --tail=240 || true
      fi
    done
    log "${MODEL_LABEL} gates: ${complete}/${#jobs[@]} complete, ${failed_count} failed"
    if (( failed_count > 0 )); then return 1; fi
    if (( complete == ${#jobs[@]} )); then return 0; fi
    sleep 60
  done
  return 1
}

tmp=/tmp/${JOB_STEM}-${RUN_TAG}
mkdir -p "${tmp}"
mammoth_root=${REMOTE_EVAL_ROOT}/mammoth_six_eval/${RESULT_SLUG}
heritage_root=${REMOTE_EVAL_ROOT}/cultural_heritage_focus_eval/${RESULT_SLUG}

kubectl -n "${NAMESPACE}" exec upload-pod-san -c uploader -- test -f "${MODEL_DIR}/config.json"
log "Deploying ${SERVED_MODEL} on ${REPLICAS} H200 nodes"
kubectl -n "${NAMESPACE}" set env deployment/"${DEPLOYMENT}" \
  MODEL_DIR="${MODEL_DIR}" SERVED_MODEL="${SERVED_MODEL}" >/dev/null
kubectl -n "${NAMESPACE}" scale deployment "${DEPLOYMENT}" --replicas="${REPLICAS}" >/dev/null
kubectl -n "${NAMESPACE}" rollout status deployment/"${DEPLOYMENT}" --timeout=90m
kubectl -n "${NAMESPACE}" exec upload-pod-san -c uploader -- \
  curl --fail --silent --show-error --max-time 30 "${MODEL_API_BASE}/models" >/dev/null
log "Model API preflight passed: ${MODEL_API_BASE}"

sed \
  -e "s|mammoth-e2-replay-s250-eval-20260823|${jobs[0]}|g" \
  -e "s|qwen35-mm-e2-step250|${SERVED_MODEL}|g" \
  -e "s|qwen35-9b-mm-e2-replay-step250|${MODEL_LABEL}|g" \
  -e "s|/data/workspace/eval_models/mammoth_six_eval/e2_replay_step250_20260823|${mammoth_root}|g" \
  "${MAMMOTH_TEMPLATE}" >"${tmp}/mammoth.yaml"

sed \
  -e "s|bfcl-v4-q35-mm-e2-s250-20260823|${jobs[2]}|g" \
  -e "s|/data/workspace/post-training/outputs/qwen35-9b-mm-e2-replay250-step250-hf|${MODEL_DIR}|g" \
  -e "s|/data/workspace/eval_models/bfcl/runs/qwen35-9b-mm-e2-replay-s250-20260823|${REMOTE_EVAL_ROOT}/bfcl/runs/${RESULT_SLUG}|g" \
  -e "s|qwen35-mm-e2-step250|${SERVED_MODEL}|g" \
  "${BFCL_TEMPLATE}" >"${tmp}/bfcl.yaml"

sed \
  -e "s|toolsandbox-q35-e2-s250-20260823|${jobs[3]}|g" \
  -e "s|tau2-q35-e2-s250-20260823|${jobs[4]}|g" \
  -e "s|qwen35-mm-e2-step250|${SERVED_MODEL}|g" \
  -e "s|qwen35-mm-e2-replay-s250-20260823|${RESULT_SLUG}|g" \
  -e "s|qwen35_e2_replay_s250|${MODEL_KEY}|g" \
  "${STATEFUL_TEMPLATE}" >"${tmp}/stateful.yaml"

sed \
  -e "s|heritage-focus-top2k-e6-eval|${jobs[5]}|g" \
  -e "s|q35-chfocus-e6|${SERVED_MODEL}|g" \
  -e "s|/data/workspace/post-training/outputs/qwen35-9b-mm-e6-behavior-recovery-step100-hf|${MODEL_DIR}|g" \
  -e 's|/data/workspace/eval_models/cultural_heritage_focus_eval/top2k_20260825/manifests/shards|/data/workspace/eval_models/cultural_heritage_focus_eval/titleclean_v4_20260825/manifests/shards|g' \
  -e "s|/data/workspace/eval_models/cultural_heritage_focus_eval/top2k_20260825/e6|${heritage_root}|g" \
  "${HERITAGE_TEMPLATE}" >"${tmp}/heritage.yaml"

sed \
  -e "s|vl-gate-q35-27b-official-20260827|${jobs[1]}|g" \
  -e "s|qwen35-27b-official|${SERVED_MODEL}|g" \
  -e "s|q35-27b-official-20260827|${RESULT_SLUG}|g" \
  "${VL_TEMPLATE}" >"${tmp}/vl.yaml"

for target_spec in \
  "all:${jobs[6]}" \
  "extra:${jobs[7]}" \
  "korean:${jobs[8]}"; do
  target=${target_spec%%:*}
  job=${target_spec#*:}
  sed \
    -e "s|oc-q35-mm-hshared-vfvm-all-r2-20260822|${job}|g" \
    -e "s|qwen35-mm-hshared-vfvm-full1ep|${SERVED_MODEL}|g" \
    -e "s|/data/workspace/post-training/outputs/qwen35-9b-fable-vwi-mammoth-heritage-shared-full1ep-lr1e7-visualfreeze-16n-hf|${MODEL_DIR}|g" \
    -e "s|qwen35-9b-mm-hshared-vfvm-full1ep-20260822-r2|${RESULT_SLUG}|g" \
    -e "s|value: all|value: ${target}|g" \
    "${OPENCOMPASS_TEMPLATE}" >"${tmp}/opencompass-${target}.yaml"
done

sed \
  -e "s|tau3-q35-e2-s250-full-20260823|${jobs[9]}|g" \
  -e "s|qwen35-mm-e2-step250|${SERVED_MODEL}|g" \
  -e "s|qwen35_e2_replay_s250|${MODEL_KEY}|g" \
  -e "s|/data/workspace/eval_models/tau3_axes/qwen35-mm-e2-replay-s250-20260823|${REMOTE_EVAL_ROOT}/tau3_axes/${RESULT_SLUG}|g" \
  -e 's|TRIALS=4|TRIALS=1|g' \
  -e 's|base_full_4trials_bm25_v1|base_quick_1trial_bm25_v1|g' \
  -e 's|--max-concurrency 16|--max-concurrency 32|g' \
  -e 's|\[expected_tasks\] \* 4|[expected_tasks] * 1|g' \
  -e 's|"num_trials": 4|"num_trials": 1|g' \
  "${TAU3_TEMPLATE}" >"${tmp}/tau3.yaml"

full_tau3_manifest=${tmp}/tau3-full.pending
sed \
  -e "s|tau3-q35-e2-s250-full-20260823|${FULL_TAU3_JOB}|g" \
  -e "s|qwen35-mm-e2-step250|${SERVED_MODEL}|g" \
  -e "s|qwen35_e2_replay_s250|${MODEL_KEY}|g" \
  -e "s|http://vllm-qwen35-9b-sft-no-reasoning:8000/v1|${MODEL_API_BASE}|g" \
  -e "s|/data/workspace/eval_models/tau3_axes/qwen35-mm-e2-replay-s250-20260823|${FULL_TAU3_ROOT}|g" \
  -e 's|--max-concurrency 16|--max-concurrency 32|g' \
  "${TAU3_TEMPLATE}" >"${full_tau3_manifest}"

# The benchmark templates are shared with older Qwen runs. Normalize the
# generated manifests to the API and chat-template contract of this model.
for yaml in "${tmp}"/*.yaml; do
  sed -i \
    -e "s|http://vllm-qwen35-9b-sft-no-reasoning:8000/v1|${MODEL_API_BASE}|g" \
    -e "s|enable_thinking|${CHAT_TEMPLATE_THINKING_KEY}|g" \
    -e "s|248044, 248046|${OPENCOMPASS_STOP_TOKEN_IDS}|g" \
    -e "s|${CHAT_TEMPLATE_THINKING_KEY}=True|${CHAT_TEMPLATE_THINKING_KEY}=${CHAT_TEMPLATE_THINKING_VALUE}|g" \
    "${yaml}"
done

for yaml in "${tmp}/mammoth.yaml" "${tmp}/heritage.yaml"; do
  sed -i "/RUNNER=\/data\/workspace\/eval_models\/scripts\/eval_mammoth_six.py/a\\
              export MAMMOTH_STOP_TOKEN_IDS='${MAMMOTH_STOP_TOKEN_IDS}'\\
              export MAMMOTH_THINKING_KEY='${MAMMOTH_THINKING_KEY}'\\
              export MAMMOTH_ENABLE_THINKING='${MAMMOTH_ENABLE_THINKING}'" "${yaml}"
done

kubectl -n "${NAMESPACE}" delete job "${jobs[@]}" --ignore-not-found --wait=true >/dev/null
for yaml in "${tmp}"/*.yaml; do
  kubectl apply --server-side --dry-run=server -f "${yaml}" >/dev/null
done
for yaml in "${tmp}"/*.yaml; do kubectl apply -f "${yaml}"; done
if [[ ${DETACH} == true ]]; then
  trap - EXIT
  log "Detached after launching ${#jobs[@]} evaluation jobs; vLLM remains at ${REPLICAS} replicas"
  exit 0
fi
wait_for_jobs

kubectl -n "${NAMESPACE}" exec upload-pod-san -c uploader -- \
  python "${REMOTE_EVAL_ROOT}/scripts/eval_mammoth_six.py" rescore \
    --predictions "${mammoth_root}/heritage_simple/predictions.jsonl" \
    --summary "${mammoth_root}/heritage_simple/summary.json" \
    --model "${SERVED_MODEL}" \
    --model-label "${MODEL_LABEL}" \
    --heritage-simple-answer-map "${HERITAGE_ANSWER_MAP}"

kubectl -n "${NAMESPACE}" exec upload-pod-san -c uploader -- \
  python "${HERITAGE_SUMMARIZER}" summarize --input-root "${heritage_root}"

kubectl -n "${NAMESPACE}" delete job "${FULL_TAU3_JOB}" --ignore-not-found --wait=true >/dev/null
kubectl apply --server-side --dry-run=server -f "${full_tau3_manifest}" >/dev/null
kubectl apply -f "${full_tau3_manifest}"

monitor_session=$(printf 'monitor-%s' "${FULL_TAU3_JOB}" | tr -cs '[:alnum:]_-' '-')
tmux kill-session -t "${monitor_session}" 2>/dev/null || true
tmux new-session -d -s "${monitor_session}" \
  "env KUBECONFIG_PATH='${KUBECONFIG_PATH}' NAMESPACE='${NAMESPACE}' bash '${ROOT}/eval_models/monitor_async_tau3_job.sh' '${FULL_TAU3_JOB}' '${DEPLOYMENT}' '${ROOT}/eval_models/${FULL_TAU3_JOB}.monitor.log'"
ASYNC_TAU3_LAUNCHED=true

log "${MODEL_LABEL} fast gates completed; full tau3 launched asynchronously as ${FULL_TAU3_JOB}"
