import os, sys, shlex

from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.dirname(__file__)
PARENT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
sys.path.insert(0, PARENT_DIR)

import tools
import logger

BASE_PORT = 10000
CONTAINER_PORT = 80

DEFAULT_FILE_PATH = os.environ.get("PWD")

MAX_WORKER = 2

def docker_compose_down(path, yml_file, check):
    tools.run(f"docker compose -f {path}/{shlex.quote(yml_file)} down > /dev/null 2>&1 || true", check=check)

def docker_volume_clean(check):
    tools.run("docker volume ls -qf dangling=true | xargs docker volume rm > /dev/null 2>&1 || true", check=check)

def run_flow(idx, repo, tag):
    suffix = idx

    image = f"{repo}:{tag}"
    repo_name = repo.split('/')
    name = f"{tools.sanitize_name(repo_name[-1])}-{tag}"
    yml_file = name + ".yml"
    path = f"./compose_files/{tools.sanitize_name(repo_name[-1])}-{tag}"
    host_port = BASE_PORT + suffix

    docker_compose_down(path=path, yml_file=yml_file, check=False)
    logger.log("cleanup: docker-compose 정리 완료")


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

    docker_volume_clean(check=False)
