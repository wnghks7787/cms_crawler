import os, sys, pathlib, shlex
import time

import compose_file_autobuilder as cfa

BASE_DIR = os.path.dirname(__file__)
PARENT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
sys.path.insert(0, PARENT_DIR)

import tools
import logger

# LOG_DIR = "compose_logs/"
BASE_PORT = 10000
CONTAINER_PORT = 80

DEFAULT_FILE_PATH = os.environ.get("PWD")

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
            name = f"{tools.sanitize_name(repo_name[-1])}-{tag}.yml"
            path = f"./compose_files/{tools.sanitize_name(repo_name[-1])}-{tag}"
            host_port = BASE_PORT+suffix
            suffix += 1
            # pathlib.Path(ctr_dir).mkdir(parents=True, exist_ok=True)

            tools.run(f"docker-compose -f {path}/{shlex.quote(name)} down > /dev/null 2>&1 || true", check=False)
            logger.log(f"RUN {name} | {image} | {host_port}:{CONTAINER_PORT}")
            cfa.compose_file_builder(repo, tag, suffix-1)