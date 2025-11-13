import os
import glob
import json
import re
from packaging.version import parse as parse_version

# --- 1. 경로 설정 (기존과 동일) ---
BASE_DIR = os.path.dirname(__file__)
PARENT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
RESOURCES_DIR = os.path.abspath(os.path.join(PARENT_DIR, 'resources/fingerprintable_file'))

# --- 2. 헤더 텍스트 파일 파서 (모든 헤더 수집) ---
def analyze_header_file(file_path):
    """
    'headers.txt' 파일을 읽어 'Date'를 제외한 모든 헤더를
    파싱하여 딕셔너리로 반환합니다.
    
    반환 형식:
    {
        'server': ('Server', 'Apache/1.0'), 
        'set-cookie-names': ('Set-Cookie-Names', ('cookie1', 'cookie2'))
    }
    키는 소문자 논리 키, 
    값은 (원본 키, 최종 값) 튜플입니다.
    """
    
    # { lkey: (original_key, [value_list]) }
    headers_map = {} 
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('HTTP/'):
                    continue
                
                try:
                    key_orig, value = line.split(':', 1)
                    key_orig = key_orig.strip()
                    key_low = key_orig.lower() # 비교를 위한 소문자 키
                    value = value.strip()
                    
                    # === 요청하신 예외 처리 ===
                    if key_low == 'date':
                        continue
                    
                    # === 특수 처리: Set-Cookie (이름만 추적) ===
                    if key_low == 'set-cookie':
                        key_orig = 'Set-Cookie-Names' # 출력될 키 이름
                        key_low = 'set-cookie-names' # 내부 논리 키
                        value = value.split('=')[0].split(';')[0].strip()
                    
                    # 맵에 (원본 키, [값 리스트]) 저장
                    if key_low not in headers_map:
                        headers_map[key_low] = (key_orig, [value])
                    else:
                        # 이미 키가 있으면 (다중 값 헤더), 값 리스트에 추가
                        headers_map[key_low][1].append(value)
                        
                except ValueError:
                    pass # ':'가 없는 줄 무시

        # --- 최종 핑거프린트 객체 생성 ---
        final_fingerprint = {}
        for lkey, (okey, values_list) in headers_map.items():
            if len(values_list) == 1:
                # 값이 하나면 문자열 그대로
                final_fingerprint[lkey] = (okey, values_list[0])
            else:
                # 값이 여러 개면 (Set-Cookie, Vary 등)
                # 정렬된 튜플로 변환 (비교 가능하도록)
                final_fingerprint[lkey] = (okey, tuple(sorted(list(set(values_list)))))
    
    except Exception as e:
        print(f"    - 헤더 분석 중 에러 발생 ({file_path}): {e}")
        return {}
        
    return final_fingerprint # {'server': ('Server', 'Apache'), ...}

# --- 3. 1:1 비교 Diff 생성기 (<<< 핵심 로직) ---
def generate_http_diffs(root_directory):
    """
    디렉터리를 순회하며 'headers.txt' 파일의 1:1 Diff를 생성합니다.
    """
    # (파일 경로 수집 로직은 이전과 동일)
    cms_data = {}
    version_dirs = glob.glob(os.path.join(root_directory, '*-*'))
    for dir_path in version_dirs:
        dir_name = os.path.basename(dir_path)
        try:
            cms_name, version_str = dir_name.rsplit('-', 1)
        except ValueError:
            continue
        header_file_path = os.path.join(dir_path, 'headers.txt')
        if not os.path.exists(header_file_path):
            continue
        if cms_name not in cms_data:
            cms_data[cms_name] = []
        cms_data[cms_name].append({'version': version_str, 'path': header_file_path})

    final_diffs_db = {}
    for cms_name, version_info_list in cms_data.items():
        print(f"\n[*] '{cms_name}'의 HTTP Diff 생성을 시작합니다...")
        
        # 1. 버전 순으로 정렬 (필수)
        version_info_list.sort(key=lambda x: parse_version(x['version']))
        
        if len(version_info_list) < 2:
            print(f"    - 버전이 1개뿐이라 비교를 건너뜁니다.")
            continue

        cms_diffs_list = [] # 최종 결과 (모든 Diff)
        
        # 2. 인접한 버전 쌍(Pair)으로 순회 (1:1 비교)
        for i in range(len(version_info_list) - 1):
            old_info = version_info_list[i]
            new_info = version_info_list[i+1]
            
            old_version_str = old_info['version']
            new_version_str = new_info['version']

            print(f"    - {old_version_str} vs {new_version_str} 비교 중...")
            
            old_fp = analyze_header_file(old_info['path'])
            new_fp = analyze_header_file(new_info['path'])
            
            # 3. 모든 헤더 키를 기준으로 변경 사항 비교
            # (이전 버전에만 있거나, 새 버전에만 있는 키 모두 포함)
            all_lkeys = set(old_fp.keys()).union(set(new_fp.keys()))
            
            for lkey in all_lkeys:
                old_entry = old_fp.get(lkey) # 예: ('Server', 'Apache/1.0')
                new_entry = new_fp.get(lkey) # 예: ('Server', 'Apache/2.0')
                
                old_val = old_entry[1] if old_entry else None
                new_val = new_entry[1] if new_entry else None
                
                # 4. 값이 변경되었을 경우에만 (추가, 삭제, 수정)
                if old_val != new_val:
                    # 출력될 헤더 키 이름 (새 버전 기준, 없으면 이전 버전 기준)
                    output_key = new_entry[0] if new_entry else old_entry[0]
                    
                    # 5. 요청하신 예시 형식으로 Diff 객체 생성
                    diff_obj = {
                        "key": output_key,
                        "value": new_val,
                        "version from": old_version_str,
                        "version to": new_version_str,
                        "previous_value": old_val
                    }
                    cms_diffs_list.append(diff_obj)
        
        # 6. CMS별 결과 저장
        final_diffs_db[cms_name] = cms_diffs_list
        print(f"'{cms_name}'의 헤더 변경 내역 {len(cms_diffs_list)}개를 생성했습니다.")

    return final_diffs_db


# --- 4. 스크립트 실행 ---
if __name__ == "__main__":
    ROOT_DATA_DIR = RESOURCES_DIR 
    
    if not os.path.exists(ROOT_DATA_DIR):
        print(f"[!] 오류: 데이터 디렉터리 '{ROOT_DATA_DIR}'를 찾을 수 없습니다.")
    else:
        diff_db = generate_http_diffs(ROOT_DATA_DIR)
        
        if diff_db:
            # 결과 파일명을 'http_diffs.json'으로 변경
            with open('http_fingerprints2.json', 'w', encoding='utf-8') as f:
                json.dump(diff_db, f, indent=2, ensure_ascii=False)
            print("\n[+] HTTP Diff(http_fingerprints2.json) 파일이 성공적으로 생성되었습니다.")
        else:
            print("\n[-] 생성된 HTTP Diff가 없습니다.")