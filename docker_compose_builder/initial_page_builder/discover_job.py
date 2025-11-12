import os
from tqdm import tqdm

BASE_DIR = os.path.dirname(__file__)
ROOT_RESOURCES_DIR = os.path.abspath(os.path.join(BASE_DIR, './fingerprintable_file/'))

def discover_jobs(root_dir):
    print(f"Discovering jobs in {root_dir}...")

    job_paths = []

    file_iterator = tqdm(os.walk(root_dir), desc="Scanning directories")

    for dirpath, _, filenames in os.walk(root_dir):
        if 'joomla' not in dirpath:
            continue
        if 'landing.html' in filenames and 'headers.txt' in filenames:
            job_paths.append(dirpath)
    
    print("Sorting...")
    job_paths.sort(key=lambda path: os.path.basename(path), reverse=True)

    print(f"Found {len(job_paths)} snapshots to analyze.")

    with open('jobs', 'w', encoding='utf-8') as f:
        f.write('\n'.join(job_paths))

if __name__ == '__main__':
    discover_jobs(ROOT_RESOURCES_DIR)
