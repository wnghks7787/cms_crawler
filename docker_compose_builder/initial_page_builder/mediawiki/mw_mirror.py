#!/usr/bin/env python3
# mw_mirror.py
# MediaWiki 메인 페이지와 연결 리소스를 로컬에 미러링
# - 동일 호스트만 추적(포트 느슨 모드: 같은 호스트면 포트 없기도 허용)
# - Content-Type으로 확장자 결정 (CSS/JS/JSON/SVG)
# - load.php?... 긴 쿼리는 해시로 축약해 파일명 제한 회피
# - 중복 URL 저장 방지
# - siteinfo.json 저장
# - **메인 페이지(첫 요청)만 <파일>.headers.txt 로 응답 헤더 저장**

import os
import re
import time
import argparse
import urllib.parse
import hashlib
from collections import deque

import requests
from bs4 import BeautifulSoup

CSS_IMPORT_RE = re.compile(r"""@import\s+(?:url\()?['"]?([^'")]+)['"]?\)?\s*;""", re.I)
SAFE_CHARS = "._-~"
MAX_BASENAME = 120
MAX_PATH = 240

def _slug(s: str) -> str:
    out = []
    for ch in s:
        if ch.isalnum() or ch in SAFE_CHARS:
            out.append(ch)
        else:
            out.append("_")
    return "".join(out).strip("_") or "x"

def norm_join(base, url):
    return urllib.parse.urljoin(base, url)

def is_http_url(u: str) -> bool:
    scheme = urllib.parse.urlsplit(u).scheme
    return scheme in ("", "http", "https")

def same_origin_loose(base_netloc, url):
    p = urllib.parse.urlsplit(url)
    if p.netloc == "":
        return True
    base_host, _, base_port = base_netloc.partition(':')
    host, _, port = p.netloc.partition(':')
    return (host == base_host) and (port == base_port or port == "")

def save_bytes(base, url, content, outdir, content_type="", headers=None, status_code=None, save_headers=False):
    p = urllib.parse.urlsplit(url)
    netloc = p.netloc or urllib.parse.urlsplit(base).netloc
    path = p.path or "/"
    query = p.query

    ctype = (content_type or "").lower()
    if "text/css" in ctype:
        ext_from_ctype = ".css"
    elif "javascript" in ctype or "text/js" in ctype or "application/x-javascript" in ctype:
        ext_from_ctype = ".js"
    elif "json" in ctype:
        ext_from_ctype = ".json"
    elif "svg" in ctype:
        ext_from_ctype = ".svg"
    else:
        ext_from_ctype = None

    if ".php" in path:
        pre, post = path.split(".php", 1)
        post = post.replace("/", "__")
        base_name = os.path.basename(pre) + ".php" + post
        if query:
            base_name += "__" + _slug(query)
        base_name += ext_from_ctype or ".html"
        rel_dir = "/".join(filter(None, pre.split("/")[:-1]))
        rel = (rel_dir + "/" if rel_dir else "") + base_name
    else:
        if path.endswith("/"):
            rel = path.lstrip("/") + "index.html"
        else:
            base_name = os.path.basename(path)
            root, ext = os.path.splitext(base_name)
            if ext.lower() in ("",):
                if query:
                    base_name = (root or "index") + "__" + _slug(query)
                else:
                    base_name = (root or "index")
                base_name += ext_from_ctype or ".html"
                rel = "/".join(path.lstrip("/").split("/")[:-1] + [base_name])
            else:
                rel = path.lstrip("/")
                if query:
                    rel = rel + "__" + _slug(query)

    dir_part = os.path.dirname(rel)
    base_part = os.path.basename(rel)
    root, ext = os.path.splitext(base_part)

    def shorten(name_root: str, ext_s: str) -> str:
        s = name_root + ext_s
        if len(s) <= MAX_BASENAME:
            return s
        h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
        prefix = name_root[:80]
        return f"{prefix}_{h}{ext_s}"

    base_part = shorten(root, ext)
    rel = os.path.join(dir_part, base_part)

    local_dir = os.path.join(outdir, netloc, os.path.dirname(rel))
    os.makedirs(local_dir, exist_ok=True)
    local_path = os.path.join(outdir, netloc, rel)

    if len(local_path) > MAX_PATH:
        h = hashlib.sha1(local_path.encode("utf-8")).hexdigest()[:12]
        base_part2 = f"{root[:80]}_{h}{ext}"
        rel = base_part2
        local_dir = os.path.join(outdir, netloc)
        local_path = os.path.join(local_dir, rel)

    with open(local_path, "wb") as f:
        f.write(content)

    if save_headers and headers is not None:
        header_path = local_path + ".headers.txt"
        with open(header_path, "w", encoding="utf-8") as hf:
            if status_code is not None:
                hf.write(f"HTTP {status_code}\n")
            for k, v in headers.items():
                hf.write(f"{k}: {v}\n")

    return local_path

def _extract_srcset_urls(value: str, base_url: str):
    urls = set()
    for part in value.split(","):
        u = part.strip().split(" ")[0]
        if u:
            urls.add(norm_join(base_url, u))
    return urls

def extract_links_from_html(html, page_url):
    soup = BeautifulSoup(html, "html.parser")
    links = set()

    tags = [
        ("a","href"), ("link","href"), ("script","src"),
        ("img","src"), ("source","src"), ("iframe","src"),
        ("video","src"), ("audio","src"),
    ]
    for tag, attr in tags:
        for el in soup.find_all(tag):
            v = el.get(attr)
            if v:
                links.add(norm_join(page_url, v))

    for el in soup.find_all(["img","source"]):
        sv = el.get("srcset")
        if sv:
            links.update(_extract_srcset_urls(sv, page_url))

    for style in soup.find_all("style"):
        css = style.string or ""
        for m in CSS_IMPORT_RE.findall(css):
            links.add(norm_join(page_url, m))

    return links

def extract_css_imports(css_bytes, base_url):
    try:
        css = css_bytes.decode("utf-8", "ignore")
    except Exception:
        css = ""
    found = []
    for u in CSS_IMPORT_RE.findall(css):
        found.append(norm_join(base_url, u))
    return found

def crawl(base, outdir, max_depth=2, max_pages=2000, sleep=0.05):
    session = requests.Session()
    session.headers.update({"User-Agent": "mw-mirror/1.0"})
    base_netloc = urllib.parse.urlsplit(base).netloc

    try:
        r = session.get(urllib.parse.urljoin(base, "api.php?action=query&meta=siteinfo&format=json"), timeout=8)
        if r.status_code == 200:
            jpath = os.path.join(outdir, "siteinfo.json")
            os.makedirs(outdir, exist_ok=True)
            with open(jpath, "wb") as f:
                f.write(r.content)
            print("[OK] saved siteinfo.json")
    except Exception as e:
        print("[WARN] siteinfo:", e)

    q = deque()
    q.append((base, 0))
    seen = set()
    saved_urls = set()
    pages = 0

    while q and pages < max_pages:
        url, depth = q.popleft()
        if (url, depth) in seen:
            continue
        seen.add((url, depth))
        if depth > max_depth:
            continue

        try:
            r = session.get(url, timeout=15, allow_redirects=True)
        except Exception as e:
            print("[ERR] GET", url, e)
            continue

        if r.status_code >= 400:
            print("[SKIP]", r.status_code, url)
            continue

        ctype = r.headers.get("Content-Type", "")
        is_first = (depth == 0)  # 메인페이지(첫 요청)만 헤더 저장
        if r.url not in saved_urls:
            saved = save_bytes(
                base, r.url, r.content, outdir,
                content_type=ctype,
                headers=(r.headers if is_first else None),
                status_code=(r.status_code if is_first else None),
                save_headers=is_first
            )
            print("[SAVE]", r.status_code, r.url, "->", saved, ("[+headers]" if is_first else ""))
            saved_urls.add(r.url)
            pages += 1
        else:
            print("[DUP]", r.url)

        time.sleep(sleep)

        if "text/html" in ctype:
            links = extract_links_from_html(r.text, r.url)
            cand = [u for u in links if is_http_url(u) and same_origin_loose(base_netloc, u)]
            for u in cand:
                q.append((u, depth + 1))
        elif "text/css" in ctype:
            imports = extract_css_imports(r.content, r.url)
            for u in imports:
                if is_http_url(u) and same_origin_loose(base_netloc, u):
                    q.append((u, depth + 1))

    print("Crawl finished: pages saved:", pages)

def pick_entry(base: str) -> str:
    s = requests.Session()
    s.headers.update({"User-Agent": "mw-mirror/1.0"})

    if not base.endswith("/"):
        path = urllib.parse.urlsplit(base).path or ""
        if not path or path.endswith("/"):
            base = base + "/"

    sp = urllib.parse.urlsplit(base)
    candidates = [base]
    if sp.path in ("", "/"):
        root = urllib.parse.urlunsplit((sp.scheme, sp.netloc, "/", "", ""))
        candidates = [
            root,
            urllib.parse.urljoin(root, "index.php"),
            urllib.parse.urljoin(root, "wiki/Main_Page"),
            urllib.parse.urljoin(root, "index.php/Main_Page"),
        ]

    for u in candidates:
        try:
            r = s.get(u, timeout=8, allow_redirects=True)
            if r.status_code < 400:
                print(f"[OK] entry: {u} -> {r.url} ({r.status_code})")
                return r.url
            else:
                print(f"[SKIP] entry cand {u} -> {r.status_code}")
        except Exception as e:
            print(f"[ERR] entry cand {u} -> {e}")

    raise SystemExit("[FATAL] No working entry URL found. Try --base http://localhost:8081/index.php")

def main():
    ap = argparse.ArgumentParser(description="Mirror MediaWiki main page and resources.")
    ap.add_argument("--base", required=True, help="Base URL (e.g., http://localhost:8081/ or /index.php/Main_Page)")
    ap.add_argument("--out", default="./mirror", help="Output directory")
    ap.add_argument("--depth", type=int, default=2, help="Max crawl depth (default: 2)")
    ap.add_argument("--max-pages", type=int, default=2000, help="Max pages to fetch")
    ap.add_argument("--sleep", type=float, default=0.05, help="Delay between requests (seconds)")
    args = ap.parse_args()

    entry = pick_entry(args.base)
    crawl(entry, args.out, max_depth=args.depth, max_pages=args.max_pages, sleep=args.sleep)

if __name__ == "__main__":
    main()

