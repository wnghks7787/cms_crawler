#!/bin/bash
set -euo pipefail

# LOGGER
log() {
    local msg="[$(date '+%H:%M:%S')] $*"
    echo "$msg"
    [[ -n "${RUN_LOG:-}" ]] && echo "$msg" >> "$RUN_LOG"
}

# 컨테이너 상태/로그/inspect를 저장
save_docker_artifacts() {
  local name="$1" out_dir="$2"
  mkdir -p "$out_dir"
  # 상태 요약
  docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -F -- " ${name} " \
    > "${out_dir}/ps.log" 2>/dev/null || true
  docker inspect "$name" > "${out_dir}/inspect.json" 2>/dev/null || true
  docker logs --tail=500 "$name" > "${out_dir}/docker.log" 2>&1 || true
  docker port "$name" > "${out_dir}/port.log" 2>/dev/null || true
}

# 컨테이너가 "running"인지 확인(성공=0, 아니면 1)
check_running() {
  local name="$1"
  local st
  st="$(docker inspect -f '{{.State.Status}}' "$name" 2>/dev/null || true)"
  [[ "$st" == "running" ]]
}



# Init Two Vector
REPOSITORIES=()
TAGS=()

# SETTING
BATCH_SIZE=10
BASE_PORT=10000
CONTAINER_PORT=80
HOST_IP=10.20.12.123

declare -a CURRENT_CONTAINERS=()

# Clean Current Containers
cleanup() {
  for name in "${CURRENT_CONTAINERS[@]:-}"; do
    docker rm -f "$name" >/dev/null 2>&1 || true
  done
  CURRENT_CONTAINERS=()
}
trap cleanup EXIT INT TERM


# Read REPO and TAG in "docker images"
while read -r repo tag; do
    REPOSITORIES+=("$repo")
    TAGS+=("$tag")
done < <(docker images --format '{{.Repository}} {{.Tag}}')

REPO_SIZE=${#REPOSITORIES[@]}
BATCHES=$(( (REPO_SIZE + BATCH_SIZE - 1) / BATCH_SIZE ))

for ((i=0 ; i<$BATCHES ;i++))
do
    # logging
    BATCH_LOG_DIR="${BATCH_LOG_DIR:-logs/batch-${b:-0}}"
    RUN_LOG="${RUN_LOG:-${BATCH_LOG_DIR}/run.log}"
    mkdir -p "$BATCH_LOG_DIR"


    echo "⚙️ $((i+1))/${BATCHES} BATCH start!"
    # Clean Previous Batch
    cleanup

    start=$(( i * BATCH_SIZE ))
    end=$(( start + BATCH_SIZE - 1 ))
    (( end >= REPO_SIZE )) && end=$(( REPO_SIZE - 1 ))

    URLS_FILE="$(pwd)/urls-batch-${i}.txt"
    : > "${URLS_FILE}"

    # 1) 컨테이너 실행 + URL 리스트 생성
    for ((j=start; j<=end; j++));
    do
        image="${REPOSITORIES[$j]}:${TAGS[$j]}"
        name="$(echo "${REPOSITORIES[$j]}-${TAGS[$j]}" | tr '/:' '--')"
        host_port=$(( BASE_PORT + j ))

        docker rm -f "${name}" >/dev/null 2>&1 || true
        docker run -d --name "${name}" -p "${host_port}:${CONTAINER_PORT}" "${image}" #>/dev/null

        CURRENT_CONTAINERS+=("$name")
        echo "http://127.0.0.1:${host_port}/" >> "${URLS_FILE}"

        echo $(curl localhost:$host_port)
    done
done
