import os, sys, pathlib, shlex
import time

from concurrent.futures import ThreadPoolExecutor, as_completed

import compose_file_autobuilder as cfa

BASE_DIR = os.path.dirname(__file__)
PARENT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
sys.path.insert(0, PARENT_DIR)

import tools
import logger
import runner
import crawl_fingerprints

# LOG_DIR = "compose_logs/"
BASE_PORT = 10000
CONTAINER_PORT = 80

DEFAULT_FILE_PATH = os.environ.get("PWD")
OUTPUT_FILE_PATH = DEFAULT_FILE_PATH + "/fingerprintable_file"

MAX_WORKER = 2

def run_flow(idx, repo, tag):
    suffix = idx
    
    image = f"{repo}:{tag}"
    repo_name = repo.split('/')
    name = f"{tools.sanitize_name(repo_name[-1])}-{tag}"
    yml_file = name + ".yml"
    path = f"./compose_files/{tools.sanitize_name(repo_name[-1])}-{tag}"
    output_path = f"{OUTPUT_FILE_PATH}/{name}"
    host_port = BASE_PORT + suffix

    tools.run(f"docker compose -f {path}/{shlex.quote(yml_file)} down > /dev/null 2>&1 || true", check=False)
    r = tools.run(f"docker compose -f {path}/{shlex.quote(yml_file)} up -d > /dev/null 2>&1 || true", check=False, capture=True)

    if r.returncode != 0:
        logger.log(f"ERROR run 실패: {yml_file} -> {r.stderr.strip()}")

    url = f"localhost:{host_port}/"

    # 세팅 완료
    # http header 받아오기
    code = runner.wait_http_ready(url, timeout=30, interval=1, follow_redirects=True, max_redirs=10, treat_redirect_ok=False)
    r = tools.run(f"./initial_page_builder.sh {repo_name[-1]} {host_port} {tag}", check=False)
    time.sleep(3)
    runner.save_headers(url, os.path.join(output_path, "headers.txt"))

    # html head tag 받아오기
    soup = tools.crawl_url_ready(f'http://localhost:{host_port}')
    head_tag = tools.get_html_head_tag(soup)

    with open(f'{output_path}/html_head_tag.txt', 'w') as f:
        f.write(head_tag)


    if code and code[0] in ("2", "3"):
        logger.log(f"OK    {name} HTTP {code}")
    else:
        logger.log(f"WARN! failed to get {name} HTTP (code={code})")

    crawler = crawl_fingerprints.download_assets(f"http://localhost:{host_port}/", output_dir=output_path)
    logger.log(f"CRAWLEING start")

    tools.run(f"docker compose -f {path}/{shlex.quote(yml_file)} down > /dev/null 2>&1 || true", check=False)
    logger.log("cleanup: docker-compose 정리 완료")
    time.sleep(5)


if __name__ == "__main__":
    REPOs = tools.repo_finder()
    pairs_all = []

    for REPO in REPOs:
        REPO = REPO.strip()
        pairs = tools.docker_images(REPO)

        if not pairs:
            logger.log(f"Image not found: {REPO}")
            continue

        for repo, tag in pairs:
            pairs_all.append((len(pairs_all), repo, tag))

    with ThreadPoolExecutor(max_workers=MAX_WORKER) as executor:
        executor.map(lambda args: run_flow(*args), pairs_all)

        # current = []
        # for i in range(0, len(pairs)):
        #     repo, tag = pairs[i]
        #     image = f"{repo}:{tag}"

        #     repo_name = repo.split('/')
        #     name = f"{tools.sanitize_name(repo_name[-1])}-{tag}"
        #     yml_file = name + ".yml"
        #     path = f"./compose_files/{tools.sanitize_name(repo_name[-1])}-{tag}"
        #     output_path = f"{OUTPUT_FILE_PATH}/{name}"
        #     host_port = BASE_PORT+suffix
        #     suffix += 1
        #     # pathlib.Path(ctr_dir).mkdir(parents=True, exist_ok=True)

        #     # tools.run(f"docker-compose -f {path}/{shlex.quote(yml_file)} down > /dev/null 2>&1 || true", check=False)
        #     # logger.log(f"RUN {yml_file} | {image} | {host_port}:{CONTAINER_PORT}")
        #     # cfa.compose_file_builder(repo, tag, suffix-1)

        #     r = tools.run(f"docker-compose -f {path}/{shlex.quote(yml_file)} up -d > /dev/null 2>&1 || true", check=False, capture=True)

        #     if r.returncode != 0:
        #         logger.log(f"ERROR run 실패: {yml_file} -> {r.stderr.strip()}")

        #     url = f"localhost:{host_port}/"
            
        #     time.sleep(10)
        #     r = tools.run(f"./initial_page_builder.sh {repo_name[-1]} {host_port} {tag}", check=False)
                
        #     code = runner.wait_http_ready(url, timeout=30, interval=1, follow_redirects=True, max_redirs=10, treat_redirect_ok=False)
        #     runner.save_headers(url, os.path.join(output_path, "headers.txt"))

        #     # html head tag 찾아서 저장하기
        #     soup = tools.crawl_url_ready(f'http://localhost:{host_port}')
        #     head_tag = tools.get_html_head_tag(soup)

        #     with open(f'{output_path}/html_head_tag.txt', 'w') as f:
        #         f.write(head_tag)
            

        #     if code and code[0] in ("2", "3"):
        #         logger.log(f"OK    {name} HTTP {code}")
        #     else:
        #         logger.log(f"WARN! failed to get {name} HTTP (code={code})")

        #     current.append(name)

        #     crawler = crawl_fingerprints.download_assets(f"http://localhost:{host_port}/", output_dir=output_path)
        #     logger.log(f"CRAWLEING start")

        #     tools.run(f"docker-compose -f {path}/{shlex.quote(yml_file)} down > /dev/null 2>&1 || true", check=False)
        #     logger.log("cleanup: docker-compose 정리 완료")            
