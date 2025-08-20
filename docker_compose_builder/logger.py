import time
import os, pathlib

BATCH_LOG_DIR = os.environ.get("BATCH_LOG_DIR", f"logs/")
RUN_LOG = os.path.join(BATCH_LOG_DIR, "run.log")

pathlib.Path(RUN_LOG).parent.mkdir(parents=True, exist_ok=True)
pathlib.Path(RUN_LOG).touch(exist_ok=True)

def log(msg):
    # run_log_path = os.path.join(RUN_LOG, path)
    # run_log_path = os.path.join(run_log_path, "run.log")
    # pathlib.Path(RUN_LOG).mkdir(parents=True, exist_ok=True)

    line = f"[{time.strftime('%F %T')}] {msg}"
    print(line)
    with open(RUN_LOG, "a") as f:
        f.write(line + "\n")