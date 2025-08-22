
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

def run_flow(url):

    output_path = "./test"

    # 세팅 완료
    # http header 받아오기
    code = runner.wait_http_ready(url, timeout=30, interval=1, follow_redirects=True, max_redirs=10, treat_redirect_ok=False)
    time.sleep(3)
    runner.save_headers(url, os.path.join(output_path, "headers.txt"))

    # html head tag 받아오기
    soup = tools.crawl_url_ready(url)
    head_tag = tools.get_html_head_tag(soup)

    with open(f'{output_path}/html_head_tag.txt', 'w') as f:
        f.write(head_tag)


    if code and code[0] in ("2", "3"):
        logger.log(f"OK    HTTP {code}")
    else:
        logger.log(f"WARN! failed to get HTTP (code={code})")

    crawler = crawl_fingerprints.download_assets(url, output_dir=output_path)
    logger.log(f"CRAWLEING start")


if __name__ == "__main__":
    run_flow("https://www.billboard.com")