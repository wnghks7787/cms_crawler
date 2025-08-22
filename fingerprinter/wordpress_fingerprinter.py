import pandas as pd
import csv, os
import argparse
import re

import fingerprinting_tools as fp_tool

# parser = argparse.ArgumentParser()
# parser.add_argument('--target', required=True)

# args = parser.parse_args()

BASE_DIR = os.path.dirname(__file__)
PARENT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
# TARGET_DIR = os.path.abspath(args.target)
RESOURCES_DIR = os.path.abspath(os.path.join(PARENT_DIR, 'resources/fingerprintable_file'))

def find_version_in_html(target):
    TARGET_DIR = os.path.abspath(target)
    # html_head_file = os.path.join(TARGET_DIR, "html.html")
    html_head_file = TARGET_DIR

    if not os.path.exists(html_head_file):
        print(f"오류: html 헤더파일 '{html_head_file}'이 존재하지 않습니다.")
        return None

    pattern = r"wordpress\s+(\d+\.\d+(?:\.\d+)?)"

    with open(html_head_file, 'r', encoding='utf-8') as f:
        content = f.read()

        versions = []
        found_versions = re.findall(pattern, content, re.IGNORECASE)
        if found_versions:
            print("다음 버전이 발견되었습니다.")
            
            for version in found_versions:
                print(f"- {version}")
                versions.append(version)
        
            # else:
            return versions

        else:
            print("패턴이 발견되지 않았습니다.")
            return None

def find_version_in_resources(target):
    versions = fp_tool.version_checker_in_csv(target)
    return versions
    
    # for version in versions:
    #     print(version)
    

def find_version(target):
    versions = []

    # versions = find_version_in_html(target)
    # versions.extend(find_version_in_resources(target))
    
    # 첫 번째 함수 결과를 받습니다.
    versions = find_version_in_html(target)

    # 만약 결과가 None이면, versions를 빈 리스트로 초기화합니다.
    if versions is None:
        versions = []

    # 두 번째 함수 결과를 받습니다.
    resources = find_version_in_resources(target)

    # 두 번째 결과가 None이 아닐 경우에만 리스트를 확장합니다.
    if resources is not None:
        versions.extend(resources)

        return versions
    return versions

    # if version_in_html != None:
    #     return version_in_html


    # return None

# if __name__ == '__main__':  