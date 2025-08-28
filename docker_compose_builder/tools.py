import subprocess, os
import shlex

import requests
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(__file__)

# Docker CLI를 사용하기 위한 함수
# capture=True인 경우, 해당 실행 내역이 subprocess로 분리되어 현 cmd 화면에서 볼 수 없다. 다만, capture하는 경우에는 해당 결과를 return해준다.
def run(cmd, check=True, capture=False):
    # log(f"$ {cmd}")
    if capture:
        return subprocess.run(cmd, shell=True, check=check, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return subprocess.run(cmd, shell=True, check=check)


def check_running(name):
    r = run(f"docker inspect -f '{{{{.State.Status}}}}' {shlex.quote(name)}", check=False, capture=True)
    return r.stdout.strip() == "running"

# 로컬 이미지 태그 목록
def docker_images(repo):
    cmd = f"docker images --format '{{{{.Repository}}}} {{{{.Tag}}}}' --filter reference='{repo}:*' | sort -r"
    r = run(cmd, capture=True)
    pairs = []
    for line in r.stdout.splitlines():
        repo_i, tag = line.strip().split()
        if tag != "<none>":
            pairs.append((repo_i, tag))
    return pairs

# 컨테이너 이름 정규화
def sanitize_name(s):
    p = subprocess.run(f"printf %s {shlex.quote(s)} | tr '/:@' '-' | tr -cs '[:alnum:]._-' '-' | tr -s '-'",
                    shell=True, stdout=subprocess.PIPE, text=True)
    return p.stdout.strip("-\n")


def repo_finder():
    file_name = BASE_DIR + "/../resources/docker_hub_library.csv"

    repo_with_lib = []

    with open(file_name, 'r', encoding='utf-8') as file:
        lines = file.readlines()

        for line in lines:
            repo_lib, repo = line.split(",")

            if repo_lib == "library":
                repo_with_lib.append(f"{repo}")
            else:
                repo_with_lib.append(f"{repo_lib}/{repo}")

    return repo_with_lib

def crawl_url_ready(url):
    response = requests.get(url)

    if(response.status_code == 200):
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    else:
        return response

def get_html_head_tag(soup):
    try:
        head_tag = soup.find('head')

        if head_tag:
            return str(head_tag)
        else:
            print(f"URL: {url} 에서 <head> 태그를 찾을 수 없습니다.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"웹 페이지를 가져오는 중 오류 발생: {e}")
        return None
    except Exception as e:
        print(f"예상치 못한 오류 발생: {e}")
        return None

def get_html(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"웹 페이지를 가져오는 중 오류 발생: {e}")
        return None
    except Exception as e:
        print(f"예상치 못한 오류 발생: {e}")
        return None

if __name__ == "__main__":
    print(repo_finder())