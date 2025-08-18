import os, subprocess, pathlib, json, time, sys, shlex

import tools

import crawl_js

# 환경변수 설정
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "10"))
BASE_PORT = int(os.environ.get("BASE_PORT", "10000"))
CONTAINER_PORT = int(os.environ.get("CONTAINER_PORT", "80"))
BATCH_INDEX = int(os.environ.get("BATCH_INDEX", "0"))
BATCH_LOG_DIR = os.environ.get("BATCH_LOG_DIR", f"logs/batch-{BATCH_INDEX}")
CRAWLER_CMD = os.environ.get("CRAWLER_CMD", 'python crawl_js.py --input "{URLS_FILE}" --out "crawl/batch-{BATCH}"')
DEFAULT_UA = "Mozilla/5.0 (compatible; crawl-js/1.0; +https://example.local)"

RUN_LOG = os.path.join(BATCH_LOG_DIR, "run.log")

# 폴더가 없으면, 만들도록
# pathlib.Path(BATCH_LOG_DIR).mkdir(parents=True, exist_ok=True)
pathlib.Path(RUN_LOG).parent.mkdir(parents=True, exist_ok=True)
# pathlib.Path(RUN_LOG).touch(exist_ok=True)

# 로그 생성
def log(msg):
    line = f"[{time.strftime('%F %T')}] {msg}"
    print(line)
    with open(RUN_LOG, "a") as f:
        f.write(line + "\n")

def save_artifacts(name, out_dir):
    pathlib.Path(out_dir).mkdir(parents=True, exist_ok=True)
    for cmd, out in [
        (f"docker ps -a --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}' | grep -F -- ' {name} '", "ps.txt"),
        (f"docker inspect {shlex.quote(name)}", "inspect.json"),
        (f"docker logs --tail=500 {shlex.quote(name)}", "docker.log"),
        (f"docker port {shlex.quote(name)}", "port.txt"),
    ]:
        try:
            r = tools.run(cmd, check=False, capture=True)
            with open(os.path.join(out_dir, out), "w") as f:
                f.write(r.stdout or r.stderr or "")
        except Exception as e:
            log(f"save_artifacts warn: {e}")

# def check_running(name):
#     r = tools.run(f"docker inspect -f '{{{{.State.Status}}}}' {shlex.quote(name)}", check=False, capture=True)
#     return r.stdout.strip() == "running"


def wait_http_ready(
    url,
    timeout=30,
    interval=1,
    follow_redirects=True,
    max_redirs=10,
    treat_redirect_ok=False  # True면 3xx도 성공으로 인정
):
    start = time.time()
    last = "000"

    flags = "-sS"
    if follow_redirects:
        flags += f" -L --max-redirs {max_redirs}"

    while time.time() - start < timeout:
        cmd = (
            f"curl {flags} -o /dev/null -D - "
            f"-w '%{{http_code}}' --max-time 5 --connect-timeout 3 {shlex.quote(url)}"
        )
        r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        code = (r.stdout or "000").strip()

        if code:
            if treat_redirect_ok:
                ok = code[0] in ("2", "3")
            else:
                ok = code[0] == "2"
            if ok:
                return code

        last = code
        time.sleep(interval)

    return last


def save_headers(
    url: str,
    out_path: str,
    follow_redirects: bool = True,
    max_redirs: int = 10,
    use_head: bool = True,
    timeout: int = 8,
    connect_timeout: int = 3,
    user_agent: str = DEFAULT_UA,
    insecure: bool = False
):
    pathlib.Path(os.path.dirname(out_path)).mkdir(parents=True, exist_ok=True)
    flags = "-sS"
    if follow_redirects:
        flags += f" -L --max-redirs {max_redirs}"
    if insecure:
        flags += " -k"
    if user_agent:
        flags += f" -A {shlex.quote(user_agent)}"

    q = shlex.quote
    meta_path = f"{out_path}.meta"

    if use_head:
        cmd = (
            f"(curl {flags} -I {q(url)} -D {q(out_path)} -o /dev/null "
            f"-w '%{{http_code}} %{{url_effective}}' --max-time {timeout} --connect-timeout {connect_timeout}"
            f" || "
            f"curl {flags} {q(url)} -D {q(out_path)} -o /dev/null "
            f"-w '%{{http_code}} %{{url_effective}}' --max-time {timeout} --connect-timeout {connect_timeout}) "
            f"> {q(meta_path)} 2>/dev/null"
        )
    else:
        cmd = (
            f"curl {flags} {q(url)} -D {q(out_path)} -o /dev/null "
            f"-w '%{{http_code}} %{{url_effective}}' --max-time {timeout} --connect-timeout {connect_timeout} "
            f"> {q(meta_path)} 2>/dev/null"
        )

    tools.run(cmd, check=False)
    


def main():
    REPOs = tools.repo_finder()
    port_set = 0

    for REPO in REPOs:
        REPO = REPO.strip()
        pairs = tools.docker_images(REPO)

        if not pairs:
            log(f"Image not found: {REPO}")
            continue

        # 배치 범위 계산(단순 예시: 전체를 한 배치로 보고 싶으면 조정)
        start = 0
        end = len(pairs) - 1
        urls_file = os.path.join(BATCH_LOG_DIR, f"urls-batch-{BATCH_INDEX}.txt")
        open(urls_file, "w").close()

        current = []
        for i in range(start, end+1):
            repo, tag = pairs[i]
            image = f"{repo}:{tag}"
            name = f"{tools.sanitize_name(repo)}-{tag}"
            host_port = BASE_PORT+port_set
            port_set += 1
            ctr_dir = os.path.join(BATCH_LOG_DIR, name)
            pathlib.Path(ctr_dir).mkdir(parents=True, exist_ok=True)

            tools.run(f"docker rm -f {shlex.quote(name)} > /dev/null 2>&1 || true", check=False)
            log(f"RUN {name} | {image} | {host_port}:{CONTAINER_PORT}")
            r = tools.run(f"docker run -d -p {host_port}:{CONTAINER_PORT} --name {shlex.quote(name)} {shlex.quote(image)}", check=False, capture=True)

            if r.returncode != 0:
                log(f"ERROR run 실패: {name} -> {r.stderr.strip()}")
                save_artifacts(name, ctr_dir)
                open(os.path.join(ctr_dir, "FAILED.run"), "w").close()
                continue

            with open(os.path.join(ctr_dir, "container_id.txt"), "w") as f:
                f.write((r.stdout or "").strip())

            save_artifacts(name, ctr_dir)

            if not check_running(name):
                log(f"WARN! not running: {name}")
                save_header(f"localhost:{host_port}/", os.path.join(ctr_dir, "headers.txt"))

                with open(urls_file, "a") as f:
                    f.write(f"localhost:{host_port}/\n")
                
                open(os.path.join(ctr_dir, "FAILED.running"), "w").close()
                continue

            url = f"localhost:{host_port}/"
            code = wait_http_ready(url, timeout=30, interval=1, follow_redirects=True, max_redirs=10, treat_redirect_ok=False)
            save_headers(url, os.path.join(ctr_dir, "headers.txt"))
            with open(urls_file, "a") as f:
                f.write(url + "\n")
            save_artifacts(name, ctr_dir)

            if code and code[0] in ("2", "3"):
                log(f"OK    {name} HTTP {code}")
                open(os.path.join(ctr_dir, "OK.http"), "w").close()
            else:
                log(f"WARN! failed to get {name} HTTP (code={code})")
                open(os.path.join(ctr_dir, "FAILED.http"), "w").close()

            current.append(name)

            crawler = crawl_js.download_assets(f"http://localhost:{host_port}/", output_dir=f"./assets_file/{name}")
            log(f"CRAWLEING start")

            # crawler = CRAWLER_CMD.replace("{RULS_FILE}", urls_file).replace("{BATCH}", str(BATCH_INDEX))
            # log(f"CRAWLER: {crawler}")
            # rc = subprocess.run(crawler, shell=True).returncode
            # log(f"CRAWLER 종료코드: {rc}")

            tools.run(f"docker rm -f {shlex.quote(name)} > /dev/null 2>&1 || true", check=False)
            log("cleanup: 컨테이너 정리 완료")

if __name__ == "__main__":
    main()