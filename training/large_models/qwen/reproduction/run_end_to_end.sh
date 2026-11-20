#!/usr/bin/env bash
set -euo pipefail

ROOT=${ROOT:-/data/workspace}
NAMESPACE=${NAMESPACE:-p-keti-airc-h200-128}
KUBECONFIG_PATH=${KUBECONFIG_PATH:-}
RUN_TAG=${RUN_TAG:-20260902r1}
LOG=${ROOT}/eval_models/qwen35_27b_v28c_like_9b_end_to_end_${RUN_TAG}.log
LOCK=${ROOT}/eval_models/qwen35_27b_v28c_like_9b_end_to_end_${RUN_TAG}.lock

if [[ -n ${KUBECONFIG_PATH} ]]; then
  export KUBECONFIG=${KUBECONFIG_PATH}
else
  unset KUBECONFIG
fi

exec 9>"${LOCK}"
flock -n 9 || { echo "The Qwen3.5-27B v28c-like workflow is already running"; exit 0; }
exec > >(tee -a "${LOG}") 2>&1

log() {
  printf '[%s] %s\n' "$(date '+%F %T')" "$*"
}

remote_file_exists() {
  kubectl -n "${NAMESPACE}" exec upload-pod-san -c uploader -- test -f "$1"
}

wait_for_job() {
  local job=$1 deadline=$((SECONDS + 21600))
  while (( SECONDS < deadline )); do
    local complete failed
    complete=$(kubectl -n "${NAMESPACE}" get job "${job}" -o jsonpath='{.status.conditions[?(@.type=="Complete")].status}' 2>/dev/null || true)
    failed=$(kubectl -n "${NAMESPACE}" get job "${job}" -o jsonpath='{.status.conditions[?(@.type=="Failed")].status}' 2>/dev/null || true)
    if [[ ${complete:-} == True ]]; then return 0; fi
    if [[ ${failed:-} == True ]]; then
      kubectl -n "${NAMESPACE}" logs job/"${job}" --all-containers --prefix --tail=400 || true
      return 1
    fi
    log "Waiting for job/${job}"
    sleep 60
  done
  return 1
}

wait_for_training() {
  local job=$1 output=$2 step=$3 deadline=$((SECONDS + 345600))
  while (( SECONDS < deadline )); do
    local phases total succeeded failed restarts high_restarts checkpoint
    phases=$(kubectl -n "${NAMESPACE}" get pods -l "training.kubeflow.org/job-name=${job}" \
      -o jsonpath='{range .items[*]}{.status.phase}{"\n"}{end}' 2>/dev/null || true)
    total=$(grep -c . <<<"${phases}" || true)
    succeeded=$(grep -c '^Succeeded$' <<<"${phases}" || true)
    failed=$(grep -c '^Failed$' <<<"${phases}" || true)
    restarts=$(kubectl -n "${NAMESPACE}" get pods -l "training.kubeflow.org/job-name=${job}" \
      -o jsonpath='{range .items[*]}{range .status.containerStatuses[*]}{.restartCount}{"\n"}{end}{end}' 2>/dev/null || true)
    high_restarts=$(awk '$1 >= 3 { count++ } END { print count + 0 }' <<<"${restarts}")
    if remote_file_exists "${output}/checkpoint-${step}/trainer_state.json"; then checkpoint=yes; else checkpoint=no; fi
    log "${job}: workers ${succeeded}/${total} succeeded, failed=${failed}, restart>=3=${high_restarts}, checkpoint-${step}=${checkpoint}"
    if [[ ${total} -eq 16 && ${succeeded} -eq 16 && ${checkpoint} == yes ]]; then return 0; fi
    if (( failed > 0 || high_restarts > 0 )); then
      kubectl -n "${NAMESPACE}" get pods -l "training.kubeflow.org/job-name=${job}" -o wide || true
      kubectl -n "${NAMESPACE}" logs "${job}-worker-0" --tail=400 || true
      return 1
    fi
    sleep 60
  done
  return 1
}

run_training() {
  local job=$1 output=$2 step=$3 manifest=$4
  if remote_file_exists "${output}/checkpoint-${step}/trainer_state.json"; then
    log "${job}: checkpoint-${step} already exists; skipping training"
    return 0
  fi
  kubectl -n "${NAMESPACE}" delete pytorchjob "${job}" --ignore-not-found --wait=true
  kubectl apply -f "${ROOT}/${manifest}"
  wait_for_training "${job}" "${output}" "${step}"
}

run_job() {
  local job=$1 manifest=$2 ready_file=$3
  if [[ -n ${ready_file} ]] && remote_file_exists "${ready_file}"; then
    log "${job}: output already exists; skipping"
    return 0
  fi
  kubectl -n "${NAMESPACE}" delete job "${job}" --ignore-not-found --wait=true
  kubectl apply -f "${ROOT}/${manifest}"
  wait_for_job "${job}"
  if [[ -n ${ready_file} ]]; then remote_file_exists "${ready_file}"; fi
}

PARENT=/data/workspace/post-training/outputs/qwen35-27b-official-heritage-title-acq-step1000-hf
HSM_TRAIN=/data/workspace/post-training/outputs/qwen35-27b-v28cl-hsm3k-v1-16n
HSM_HF=/data/workspace/post-training/outputs/qwen35-27b-v28cl-hsm-step3000-hf
HSM_MERGED=/data/workspace/post-training/outputs/qwen35-27b-v28cl-hsm-s3000-tv-t015-m100
STAGEA_TRAIN=/data/workspace/post-training/outputs/qwen35-27b-v28cl-h400-stagea1k-v1-16n
STAGEA_HF=/data/workspace/post-training/outputs/qwen35-27b-v28cl-h400-stagea-step1000-hf
H300_TRAIN=/data/workspace/post-training/outputs/qwen35-27b-v28cl-h300-idacq1k-v1-16n
H300_HF=/data/workspace/post-training/outputs/qwen35-27b-v28cl-h300-idacq-step500-hf
FINAL_TRAIN=/data/workspace/post-training/outputs/qwen35-27b-v28cl-h400-hs100-scale2500-v1-16n
FINAL_HF=/data/workspace/post-training/outputs/qwen35-27b-v28cl-h400-hs100-scale2500-step2500-hf

remote_file_exists "${PARENT}/config.json"

log "Stage 1/9: 27B HSM specialist, matching the successful 9B Fable/VisualWeb/Mammoth recipe"
run_training sft-q35-27b-v28cl-hsm3k-16n "${HSM_TRAIN}" 3000 \
  kubectl_yml/sft_qwen35_27b_v28c_like_hsm_3000steps_16nodes.yaml

log "Stage 2/9: convert the HSM checkpoint to Hugging Face format"
run_job convert-q35-27b-v28cl-hsm3k \
  kubectl_yml/convert_qwen35_27b_v28c_like_hsm_step3000_to_hf_job.yaml \
  "${HSM_HF}/config.json"

log "Stage 3/9: module-wise task-vector merge, text=0.15 merger=1.0 vision=0.0"
run_job merge-q35-27b-v28cl-hsm-t015 \
  kubectl_yml/merge_qwen35_27b_v28c_like_hsm_t015_m100_job.yaml \
  "${HSM_MERGED}/config.json"

log "Stage 4/9: H400/OCR Stage A preservation and grounding"
run_training sft-q35-27b-v28cl-stagea1k-16n "${STAGEA_TRAIN}" 1000 \
  kubectl_yml/sft_qwen35_27b_v28c_like_h400_stagea_1000steps_16nodes.yaml

log "Stage 5/9: convert Stage A checkpoint"
run_job convert-q35-27b-v28cl-stagea1k \
  kubectl_yml/convert_qwen35_27b_v28c_like_h400_stagea_step1000_to_hf_job.yaml \
  "${STAGEA_HF}/config.json"

log "Stage 6/9: class-balanced H300 identity acquisition"
run_training sft-q35-27b-v28cl-h300-id1k-16n "${H300_TRAIN}" 1000 \
  kubectl_yml/sft_qwen35_27b_v28c_like_h300_identity_acquisition_1000steps_16nodes.yaml

log "Stage 7/9: convert H300 milestones; step 500 is the predeclared 9B-matched parent"
run_job convert-q35-27b-v28cl-h300-ms \
  kubectl_yml/convert_qwen35_27b_v28c_like_h300_step500_to_hf_job.yaml \
  "${H300_HF}/config.json"

log "Stage 8/9: H400/HS100 scale-up with behavior and general-VL replay"
run_training sft-q35-27b-v28cl-h400hs25-16n "${FINAL_TRAIN}" 2500 \
  kubectl_yml/sft_qwen35_27b_v28c_like_h400_hs100_scaleup_2500steps_16nodes.yaml
run_job convert-q35-27b-v28cl-h400hs25 \
  kubectl_yml/convert_qwen35_27b_v28c_like_h400_hs100_scale2500_to_hf_job.yaml \
  "${FINAL_HF}/config.json"

log "Stage 9/9: full automatic benchmark suite on 16 H200 nodes"
RUN_TAG="${RUN_TAG}" \
MODEL_DIR="${FINAL_HF}" \
SERVED_MODEL=qwen35-27b-v28cl-h400-hs100-scale2500 \
MODEL_LABEL=qwen35-27b-v28cl-h400-hs100-scale2500 \
RESULT_SLUG="q35-27b-v28cl-hs25-${RUN_TAG}" \
JOB_STEM=q35-27b-v28cl-hs25 \
MODEL_KEY=qwen35_27b_v28cl_hs25 \
DEPLOYMENT=vllm-q35-mm-e1b-s100-16n \
REPLICAS=16 \
  bash "${ROOT}/eval_models/run_qwen35_27b_h400_hs100_scale2500_gates.sh"

log "Qwen3.5-27B v28c-like training and full evaluation completed"
