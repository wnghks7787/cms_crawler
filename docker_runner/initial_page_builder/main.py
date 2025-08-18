import os, sys, pathlib, shlex
import time

import compose_file_autobuilder as cfa

BASE_DIR = os.path.dirname(__file__)
PARENT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
sys.path.insert(0, PARENT_DIR)

import tools
import logger
import runner
import crawl_js

# LOG_DIR = "compose_logs/"
BASE_PORT = 10000
CONTAINER_PORT = 80

DEFAULT_FILE_PATH = os.environ.get("PWD")
OUTPUT_FILE_PATH = DEFAULT_FILE_PATH + "/fingerprintable_file"

if __name__ == "__main__":
    REPOs = tools.repo_finder()
    suffix = 0

    for REPO in REPOs:
        REPO = REPO.strip()
        pairs = tools.docker_images(REPO)

        if not pairs:
            logger.log(f"Image not found: {REPO}")
            continue


        current = []
        for i in range(0, len(pairs)):
            repo, tag = pairs[i]
            image = f"{repo}:{tag}"

            repo_name = repo.split('/')
            name = f"{tools.sanitize_name(repo_name[-1])}-{tag}"
            yml_file = name + ".yml"
            path = f"./compose_files/{tools.sanitize_name(repo_name[-1])}-{tag}"
            output_path = f"{OUTPUT_FILE_PATH}/{name}"
            host_port = BASE_PORT+suffix
            suffix += 1
            # pathlib.Path(ctr_dir).mkdir(parents=True, exist_ok=True)

            # tools.run(f"docker-compose -f {path}/{shlex.quote(yml_file)} down > /dev/null 2>&1 || true", check=False)
            # logger.log(f"RUN {yml_file} | {image} | {host_port}:{CONTAINER_PORT}")
            # cfa.compose_file_builder(repo, tag, suffix-1)

            r = tools.run(f"docker-compose -f {path}/{shlex.quote(yml_file)} up -d > /dev/null 2>&1 || true", check=False, capture=True)

            if r.returncode != 0:
                logger.log(f"ERROR run 실패: {yml_file} -> {r.stderr.strip()}")

            url = f"localhost:{host_port}/"
            
            time.sleep(10)
            r = tools.run(f"./initial_page_builder.sh {repo_name[-1]} {host_port} {tag}", check=False)
                
            code = runner.wait_http_ready(url, timeout=30, interval=1, follow_redirects=True, max_redirs=10, treat_redirect_ok=False)
            runner.save_headers(url, os.path.join(output_path, "headers.txt"))
            
            if code and code[0] in ("2", "3"):
                logger.log(f"OK    {name} HTTP {code}")
            else:
                logger.log(f"WARN! failed to get {name} HTTP (code={code})")

            current.append(name)

            crawler = crawl_js.download_assets(f"http://localhost:{host_port}/", output_dir=output_path)
            logger.log(f"CRAWLEING start")

            tools.run(f"docker-compose -f {path}/{shlex.quote(yml_file)} down > /dev/null 2>&1 || true", check=False)
            logger.log("cleanup: docker-compose 정리 완료")            
