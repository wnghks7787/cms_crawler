import json
import re
from packaging.version import parse as parse_version

def load_non_standard_json(file_path):
    """
    후행 쉼표(trailing comma)가 포함된 JSON 파일을 읽기 위해
    정규식을 사용해 자동으로 수정하며 로드합니다.
    """
    print(f"'{file_path}' 파일을 읽는 중...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. 리스트의 후행 쉼표 제거 (예: [ "item1", ])
        content = re.sub(r',(\s*\])', r'\1', content)
        # 2. 객체의 후행 쉼표 제거 (예: { "key": "val", })
        content = re.sub(r',(\s*\})', r'\1', content)
        
        # 표준 json 라이브러리로 파싱
        return json.loads(content)
        
    except FileNotFoundError:
        print(f"[오류] '{file_path}' 파일을 찾을 수 없습니다.")
        return None
    except json.JSONDecodeError as e:
        print(f"[오류] JSON 파싱 중 오류 발생: {e}")
        print("     파일이 유효한 JSON 형식(에서 후행 쉼표만 제외)인지 확인하세요.")
        return None

def generate_resource_diffs(data):
    """
    버전 데이터를 받아, 인접한 버전 간의 'resources' 차이점을 계산합니다.
    """
    
    # 1. 모든 버전 키를 가져와서 'packaging' 라이브러리로 정확하게 정렬
    # (예: "6.8.1", "6.8.2", "6.9.0", "6.10.0", ...)
    try:
        all_versions = list(data.keys())
        # parse_version을 키로 사용하여 버전 문자열을 올바른 순서로 정렬
        all_versions.sort(key=parse_version)
    except Exception as e:
        print(f"[오류] 버전 정렬 중 오류 발생: {e}")
        print("      버전 형식이 올바른지 확인하세요.")
        return []

    print(f"총 {len(all_versions)}개의 버전을 찾았습니다.")
    if not all_versions:
        return []
        
    print(f"(정렬 순서: {all_versions[0]} -> ... -> {all_versions[-1]})")
    
    diff_results = []
    
    # 2. 정렬된 버전을 2개씩 (이전, 이후) 짝지어 순회
    for i in range(len(all_versions) - 1):
        old_version_str = all_versions[i]
        new_version_str = all_versions[i+1]
        
        # 3. 각 버전의 'resources' 리스트를 'set' (집합)으로 변환
        try:
            old_resources = set(data[old_version_str].get('resources', []))
            new_resources = set(data[new_version_str].get('resources', []))
        except (AttributeError, KeyError) as e:
            print(f"[경고] '{old_version_str}' 또는 '{new_version_str}'의 데이터 구조가 다릅니다. (resources 키 없음). 건너뜁니다.")
            continue

        # 4. 집합 연산(set operation)으로 차이점 계산
        added = new_resources - old_resources
        removed = old_resources - new_resources
        
        # 5. 차이점이 있을 경우에만 결과 리스트에 추가
        if added or removed:
            diff_entry = {
                "version_from": old_version_str, # 이전 버전
                "version_to": new_version_str,   # 이후 버전
                "added": sorted(list(added)),    # 추가된 항목 (정렬)
                "removed": sorted(list(removed)) # 삭제된 항목 (정렬)
            }
            diff_results.append(diff_entry)
            
    return diff_results

def main():
    # --- 설정 ---
    INPUT_FILE = 'joomla.json'    # <<< 읽어올 JSON 파일
    OUTPUT_FILE = 'joomla_diff.json' # <<< 저장할 차이점 파일
    # --- ---
    
    data = load_non_standard_json(INPUT_FILE)
    
    if data:
        print("버전 간 차이점을 계산하는 중...")
        diffs = generate_resource_diffs(data)
        
        if diffs:
            print(f"총 {len(diffs)}개의 버전 간 변경 사항을 감지했습니다.")
            try:
                # 3. 결과를 별도 JSON 파일로 저장
                with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                    # indent=2: 가독성을 위해 들여쓰기
                    # ensure_ascii=False: 한글 등이 깨지지 않도록
                    json.dump(diffs, f, indent=2, ensure_ascii=False)
                print(f"\n[성공] 차이점 비교 결과가 '{OUTPUT_FILE}' 파일에 저장되었습니다.")
            except IOError as e:
                print(f"[오류] '{OUTPUT_FILE}' 파일 저장 중 오류: {e}")
        else:
            print("\n[완료] 버전 간 차이점이 발견되지 않았습니다.")

if __name__ == "__main__":
    main()