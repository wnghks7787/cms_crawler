# import os, sys, pathlib, shlex
# import time

# BASE_DIR = os.path.dirname(__file__)
# PARENT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
# sys.path.insert(0, PARENT_DIR)

# import tools

# BASE_PORT = 10000

# DEFAULT_FILE_PATH = os.environ.get('PWD')

# if __name__ == '__main__':
#     REPOs = tools.repo_finder()
#     suffix = 0

#     with open('repo_list.csv', 'w', encoding='utf-8') as f:

#         for REPO in REPOs:
#             REPO = REPO.strip()
#             pairs = tools.docker_images(REPO)

#             if not pairs:
#                 continue
            
#             current = []
#             for i in range(0, len(pairs)):
#                 repo, tag = pairs[i]
#                 host_port = BASE_PORT+suffix
#                 suffix += 1

#                 f.write(f'http:/host.docker.internal:{host_port},{repo},{tag}\n')
import os
import csv
import yaml  # PyYAML 라이브러리

# --- 설정 ---
# Docker Compose yml 파일들이 들어있는 최상위 폴더 경로를 지정해주세요.
COMPOSE_ROOT_DIR = 'compose_files'
# 최종적으로 생성될 CSV 파일의 이름
OUTPUT_CSV_FILE = 'actual_data.csv'
# -----------------

def generate_ground_truth():
    """
    Compose 폴더 구조를 분석하여 '실제 정보' CSV 파일을 생성합니다.
    """
    ground_truth_data = []
    print(f"'{COMPOSE_ROOT_DIR}' 폴더를 스캔합니다...")

    # 최상위 폴더의 모든 항목을 순회합니다.
    for dir_name in sorted(os.listdir(COMPOSE_ROOT_DIR)):
        full_dir_path = os.path.join(COMPOSE_ROOT_DIR, dir_name)

        # 폴더인 경우에만 처리
        if os.path.isdir(full_dir_path):
            print(f"  - 처리 중: {dir_name}")
            
            # 1. 폴더 이름에서 CMS 이름과 버전 정보 추출
            try:
                # 마지막 하이픈(-)을 기준으로 CMS와 버전을 분리합니다.
                # 예: 'wordpress-6.8.2' -> ('wordpress', '6.8.2')
                last_hyphen_index = dir_name.rfind('-')
                cms_name = dir_name[:last_hyphen_index]
                version = dir_name[last_hyphen_index+1:]
            except Exception:
                print(f"    [경고] '{dir_name}' 폴더 이름 형식이 올바르지 않아 건너<binary data, 3 bytes><binary data, 3 bytes><binary data, 3 bytes>니다.")
                continue

            # 2. yml 파일에서 포트 번호 추출
            try:
                yml_file_path = os.path.join(full_dir_path, f"{dir_name}.yml")
                with open(yml_file_path, 'r') as f:
                    # YAML 파일을 파이썬 딕셔너리로 변환
                    compose_data = yaml.safe_load(f)
                
                # yml 파일 구조를 탐색하여 포트 번호 찾기
                # services -> (첫 번째 서비스 이름) -> ports -> (첫 번째 포트 매핑)
                service_name = list(compose_data['services'].keys())[1]
                port_mapping = compose_data['services'][service_name]['ports'][0]
                
                # "10001:80" 에서 호스트 포트('10001')만 추출
                host_port = str(port_mapping).split(':')[0]
                
                # 3. URL 및 최종 데이터 생성
                url = f"http://host.docker.internal:{host_port}"
                ground_truth_data.append([url, cms_name, version])

            except (IOError, KeyError, IndexError, AttributeError) as e:
                print(f"    [경고] '{yml_file_path}' 파일을 처리하는 중 오류가 발생하여 건너<binary data, 3 bytes><binary data, 3 bytes><binary data, 3 bytes>니다: {e}")
                continue

    # 4. 수집된 모든 데이터를 CSV 파일로 저장
    if ground_truth_data:
        with open(OUTPUT_CSV_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            # 헤더(열 이름) 없이 데이터만 저장
            writer.writerows(ground_truth_data)
        print(f"\n성공! 총 {len(ground_truth_data)}개의 항목을 '{OUTPUT_CSV_FILE}' 파일에 저장했습니다.")
    else:
        print("\n처리할 폴더를 찾지 못했거나, 처리 중 오류가 발생했습니다.")


if __name__ == '__main__':
    generate_ground_truth()
