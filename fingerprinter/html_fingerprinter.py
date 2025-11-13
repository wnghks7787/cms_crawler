###### 완성본 ######
import os
import glob
import json
import re
from packaging.version import parse as parse_version
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(__file__)
PARENT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
RESOURCES_DIR = os.path.abspath(os.path.join(PARENT_DIR, 'resources/fingerprintable_file'))

LOCALHOST_PATTERN = re.compile(r'(https?://)?localhost(:\d+)?/?')

# 호스트 부분을 DYNAMIC_HOST로 변경
def normalize_value(value):
    if value is None:
        return None
    if isinstance(value, str):
        return LOCALHOST_PATTERN.sub('[DYNAMIC_HOST]/', value)
    if isinstance(value, list):
        return sorted([LOCALHOST_PATTERN.sub('[DYNAMIC_HOST]/', item) for item in value])
    return value

# file_path는 landing.html 파일의 경로
def analyze_html_structure(file_path):
    # fingerprint 하는거: generator, body_classes, stylesheets, scripts
    fingerprint = {'generator': None, 'body_classes': None, 'stylesheets': [], 'scripts': []}
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            soup = BeautifulSoup(f, 'html.parser')

            gen_tag = soup.find('meta', attrs={'name': 'generator'}) # meta 태그 모두 가져오기 (name='generator' 인 경우만)
            # meta tag의 content를 읽어온 뒤, fingerprint['generator'] 부분에 집어넣는다. 
            if gen_tag and gen_tag.get('content'):
                fingerprint['generator'] = normalize_value(gen_tag.get('content').strip())

            body_tag = soup.find('body') # body 태그 모두 가져오기
            # body tag의 class를 읽어온 뒤, fingerprint['body_classes'] 부분에 집어넣는다. (정렬해서)
            if body_tag and body_tag.get('class'):
                fingerprint['body_classes'] = normalize_value(", ".join(sorted(body_tag.get('class'))))

            # 
            for link_tag in soup.find_all('link', attrs={'rel': 'stylesheet'}):
                if link_tag.get('href'):
                    fingerprint['stylesheets'].append(normalize_value(link_tag.get('href')))
            fingerprint['stylesheets'] = sorted(list(set(fingerprint['stylesheets'])))
            for script_tag in soup.find_all('script', attrs={'src': True}):
                if script_tag.get('src'):
                    fingerprint['scripts'].append(normalize_value(script_tag.get('src')))
            fingerprint['scripts'] = sorted(list(set(fingerprint['scripts'])))

    except Exception as e:
        print(f"    - 분석 중 에러 발생 ({file_path}): {e}")

    return fingerprint

def generate_html_fingerprints(root_directory):
    cms_data = {}
    # wordpress-6.8.2 처럼 {cms_name}-{version}을 분리 (version_dirs는 그렇게 분리된 모든 폴더를 모아놓은 곳)
    version_dirs = glob.glob(os.path.join(root_directory, '*-*'))
    
    # dir_path: 각각의 디렉토리들
    for dir_path in version_dirs:
        dir_name = os.path.basename(dir_path)

        # {cms_name}, {version} 을 뽑아서 cms_name, verison_str 변수에 각각 저장
        try:
            cms_name, version_str = dir_name.rsplit('-', 1)
        except ValueError:
            continue

        # html 파일은 landing.html이다. landing.html이 index.html 등으로 변경되면 이 부분을 고쳐야 한다.
        html_file_path = os.path.join(dir_path, 'landing.html')
        if not os.path.exists(html_file_path):
            continue
            
        # cms_name이 cms_data에 없으면, cms_name을 data에 추가. (wordpress가 처음 들어오면 wordpress를 여기에 추가하겠다는 뜻)
        if cms_name not in cms_data:
            cms_data[cms_name] = []
        # 그리고 version을 추가해준다. 나중에 정렬할 때에도 사용할 예정. (version과 path를 모두 저장)
        cms_data[cms_name].append({'version': version_str, 'path': html_file_path})

    # fingerprints 데이터베이스 구축(dictionary)
    # 아까전에 뽑은 cms_name, version_info_list(버전들)을 cms_data에서 꺼내온다.
    # key: cms_name, value: version_into_list(버전들이 리스트 형식으로 들어있음)
    final_fingerprints_db = {}
    for cms_name, version_info_list in cms_data.items():
        print(f"\n[*] '{cms_name}'의 지문 생성을 시작합니다...")
        # 여기서 정렬함(버전별로)
        version_info_list.sort(key=lambda x: parse_version(x['version']))
        
        # 당연히 버전이 1개 미만이면 패스한다.
        if len(version_info_list) < 1:
            continue

        # 'scripts', 'stylesheets'가 field_states에서 제외됨
        # 단일 값(generator, body_classes)에 대해서는 범위를 추적
        scalar_fields = ['generator', 'body_classes']
        field_states = {field: {'value': None, 'version_start': None} for field in scalar_fields}
        
        # 단일 값 범위와 리스트 Diff를 별도로 저장
        cms_scalar_fingerprints = [] # 'generator' 등 단일 값의 버전 범위
        cms_list_diffs = []          # 'scripts' 등 목록의 버전 간 차이

        # 이전 버전의 전체 핑거프린트 저장(기본은 아무것도 없는것 당연히)
        previous_fingerprint = None 

        for i, current_version_info in enumerate(version_info_list):
            # 이전에 저장해둔 버전과 패스를 다시 분리
            current_version = current_version_info['version']
            current_fingerprint = analyze_html_structure(current_version_info['path'])
            
            # --- 1. 단일 값(Scalar) 처리 ---
            for field in scalar_fields:
                current_value = current_fingerprint[field]
                
                if field_states[field]['version_start'] is None:
                    field_states[field]['value'] = current_value
                    field_states[field]['version_start'] = current_version
                elif field_states[field]['value'] != current_value:
                    if field_states[field]['value'] is not None:
                        cms_scalar_fingerprints.append({ # <<< 변경: 'cms_scalar_fingerprints'에 저장
                            'type': f'html_element_{field}_match',
                            'value': field_states[field]['value'],
                            'version_start': field_states[field]['version_start'],
                            'version_end': version_info_list[i-1]['version']
                        })
                    field_states[field]['value'] = current_value
                    field_states[field]['version_start'] = current_version

            # --- 2. 리스트(List) 처리 ---
            if previous_fingerprint: # 첫 번째 버전(i=0)이 아닐 경우에만 비교
                prev_version_str = version_info_list[i-1]['version']
                
                # 'scripts' 차이점 계산
                prev_scripts = set(previous_fingerprint['scripts'])
                curr_scripts = set(current_fingerprint['scripts'])
                
                added_scripts = sorted(list(curr_scripts - prev_scripts))
                removed_scripts = sorted(list(prev_scripts - curr_scripts))
                
                if added_scripts or removed_scripts:
                    cms_list_diffs.append({
                        'type': 'html_element_scripts_diff',
                        'version_from': prev_version_str,
                        'version_to': current_version,
                        'added': added_scripts,
                        'removed': removed_scripts
                    })

                # 'stylesheets' 차이점 계산
                prev_styles = set(previous_fingerprint['stylesheets'])
                curr_styles = set(current_fingerprint['stylesheets'])
                
                added_styles = sorted(list(curr_styles - prev_styles))
                removed_styles = sorted(list(prev_styles - curr_styles))

                if added_styles or removed_styles:
                    cms_list_diffs.append({
                        'type': 'html_element_stylesheets_diff',
                        'version_from': prev_version_str,
                        'version_to': current_version,
                        'added': added_styles,
                        'removed': removed_styles
                    })
            
            previous_fingerprint = current_fingerprint # <<< 추가: 다음 루프를 위해 현재 값을 이전 값으로 저장

        # --- 3. 단일 값의 마지막 범위 처리 (기존 로직과 동일) ---
        for field, state in field_states.items():
            if state['version_start'] is not None and state['value'] is not None:
                cms_scalar_fingerprints.append({ # <<< 변경: 'cms_scalar_fingerprints'에 저장
                    'type': f'html_element_{field}_match',
                    'value': state['value'],
                    'version_start': state['version_start'],
                    'version_end': None 
                })

        # --- 4. 'previous_value' 추가 (단일 값 핑거프린트에만 적용) ---
        # (기존 로직을 'cms_scalar_fingerprints'에 대해서만 실행)
        grouped_by_type = {}
        for fp in cms_scalar_fingerprints: # <<< 변경: 'cms_scalar_fingerprints' 사용
            fp_type = fp['type']
            if fp_type not in grouped_by_type:
                grouped_by_type[fp_type] = []
            grouped_by_type[fp_type].append(fp)
        
        enriched_scalar_fingerprints = [] # <<< 변경: 새 리스트 이름
        for fp_type, fps_list in grouped_by_type.items():
            fps_list.sort(key=lambda x: parse_version(x['version_start']))
            
            for i, fp in enumerate(fps_list):
                if i > 0:
                    fp['previous_value'] = fps_list[i-1]['value']
                else:
                    fp['previous_value'] = None
                enriched_scalar_fingerprints.append(fp) # <<< 변경
        
        # --- 5. 최종 결과 조합 ---
        # (단일 값 범위 + 리스트 차이점)
        all_entries = enriched_scalar_fingerprints + cms_list_diffs
        all_entries.sort(key=lambda x: parse_version(x.get('version_start', x.get('version_from')))) # <<< 변경: 두 키 모두 고려하여 정렬
        
        final_fingerprints_db[cms_name] = all_entries
        print(f"'{cms_name}'의 최종 지문 {len(all_entries)}개를 생성했습니다.")

    return final_fingerprints_db


if __name__ == "__main__":
    ROOT_DATA_DIR = RESOURCES_DIR
    fingerprint_db = generate_html_fingerprints(ROOT_DATA_DIR)
    
    if fingerprint_db:
        with open('html_fingerprints.json', 'w', encoding='utf-8') as f:
            json.dump(fingerprint_db, f, indent=2, ensure_ascii=False)
        print("\n[+] previous_value가 포함된 최종 html_fingerprints.json 파일이 성공적으로 생성되었습니다.")
    else:
        print("\n[-] 생성된 HTML 지문이 없습니다.")