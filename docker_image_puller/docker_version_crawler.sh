#!/bin/bash

# Resource 파일 경로 설정
RELATIVE_PATH="../resources"
RESOURCES_PATH=${PWD}'/'$RELATIVE_PATH
FILE=$RESOURCES_PATH/"docker_hub_library.csv"

# CSV 파일의 각 라인을 읽어들입니다.
# 파이프를 사용하여 tail의 출력을 while 루프로 전달하는 방식으로 수정했습니다.
tail -n +1 "$FILE" | while IFS=',' read -r provider cms;
do
  # 공백만 있는 라인은 건너뜁니다.
  if [ -z "$provider" ] || [ -z "$cms" ]; then
    continue
  fi

  echo "Provider: $provider, CMS: $cms"

  page=1
  result_directory=$RESOURCES_PATH"/docker_hub_library_version" # 결과 저장 위치
  result_file=$result_directory"/"$cms"_version"

  # 결과 디렉토리가 없으면 생성합니다. (-p 옵션으로 오류 방지)
  mkdir -p "$result_directory"
  # 결과 파일을 새로 생성하거나 비웁니다.
  > "$result_file"

  # 임시 파일을 생성하여 모든 버전 정보를 저장합니다.
  temp_file=$(mktemp)

  while true;
  do
    # Docker Hub API를 호출하여 태그 정보를 가져옵니다. (도커 허브의 API입니다. $provider 와 $cms 부분에 따라 도커 허브에 업로드된 이미지들에 접근할 수 있습니다.)
    result=$(curl -s "https://hub.docker.com/v2/repositories/$provider/$cms/tags?page_size=100&page=$page")

    # 숫자와 점(.)으로만 구성된 버전 태그를 추출하여 임시 파일에 추가합니다.
    echo "$result" | jq -r '.results[].name' | grep -E '^[0-9]+(\.[0-9]+)*$' >> "$temp_file"

    # 다음 페이지가 있는지 확인합니다.
    next=$(echo "$result" | jq -r '.next')
    if [ "$next" = "null" ]; then
      break
    fi
    page=$((page + 1))
  done

  # 임시 파일의 내용을 버전순으로 정렬하고, 가장 구체적인 버전만 필터링하여 최종 파일에 저장합니다.
  sort -V -u "$temp_file" | awk '
    # 이전 라인과 현재 라인을 비교하여 덜 구체적인 버전을 필터링합니다.
    # 예: prev="8.0", $0="8.0.0" 이면 "8.0"은 "8.0.0"의 접두사이므로 출력하지 않습니다.
    NR > 1 {
        if (length(prev) < length($0) && index($0, prev".") == 1) {
            # 이전 버전이 현재 버전의 접두사인 경우 (예: 8, 8.0), 아무것도 하지 않습니다.
        } else {
            print prev
        }
    }
    { prev = $0 }
    END {
        # 마지막 라인을 출력합니다.
        if (NR > 0) print prev
    }
  ' > "$result_file"

  # 임시 파일을 삭제합니다.
  rm "$temp_file"

done

echo "모든 작업이 완료되었습니다."