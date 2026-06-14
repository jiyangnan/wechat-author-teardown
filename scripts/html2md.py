#!/usr/bin/env python3
"""Convert a WeChat article body (#js_content innerHTML) into clean Markdown.

Downloads inline images to <out_dir>/images/ and rewrites <img> to local
relative paths. Handles WeChat lazy-loading (data-src) and the browse
UNTRUSTED-content wrapper.

Usage:
    html2md.py <body_html_file> <out_dir> <article_url> [meta_json]

Writes <out_dir>/index.md  (front-matter + markdown body)
"""
import sys, os, re, json, hashlib, pathlib
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def strip_wrapper(text: str) -> str:
    """Remove browse's --- BEGIN/END UNTRUSTED EXTERNAL CONTENT --- markers."""
    lines = text.splitlines()
    out = [ln for ln in lines if not ln.strip().startswith("--- BEGIN UNTRUSTED")
           and not ln.strip().startswith("--- END UNTRUSTED")]
    return "\n".join(out).strip()


def download_image(url: str, dest_dir: pathlib.Path, referer: str) -> str | None:
    if not url or url.startswith("data:"):
        return None
    # WeChat image format hint lives in wx_fmt query param
    fmt = "jpg"
    m = re.search(r"wx_fmt=(\w+)", url)
    if m:
        fmt = m.group(1)
    elif url.lower().endswith((".png", ".gif", ".jpeg", ".jpg", ".webp")):
        fmt = url.rsplit(".", 1)[-1]
    name = hashlib.md5(url.encode()).hexdigest()[:16] + "." + fmt
    dest = dest_dir / name
    if dest.exists():
        return name
    try:
        r = requests.get(url, headers={"User-Agent": UA, "Referer": referer},
                         timeout=(5, 15))
        if r.status_code == 200 and r.content:
            dest.write_bytes(r.content)
            return name
    except Exception as e:
        sys.stderr.write(f"[img-fail] {url} :: {e}\n")
    return None


def main():
    if len(sys.argv) < 4:
        sys.exit("usage: html2md.py <body_html_file> <out_dir> <article_url> [meta_json]")
    body_file, out_dir, url = sys.argv[1], sys.argv[2], sys.argv[3]
    meta = json.loads(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4] else {}

    out = pathlib.Path(out_dir)
    img_dir = out / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    raw = strip_wrapper(pathlib.Path(body_file).read_text(encoding="utf-8", errors="ignore"))
    soup = BeautifulSoup(raw, "html.parser")

    # Fix lazy-loaded images (prefer data-src), download in parallel.
    imgs = soup.find_all("img")
    reals = [img.get("data-src") or img.get("src") or "" for img in imgs]
    with ThreadPoolExecutor(max_workers=8) as pool:
        locals_ = list(pool.map(lambda u: download_image(u, img_dir, url), reals))
    for img, real, local in zip(imgs, reals, locals_):
        if local:
            img["src"] = f"images/{local}"
            for attr in ("data-src", "srcset", "data-srcset"):
                if img.has_attr(attr):
                    del img[attr]
        else:
            img["src"] = real  # keep remote url as fallback

    markdown = md(str(soup), heading_style="ATX", strip=["section", "span"])
    markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip()

    fm = [
        "---",
        f"title: {meta.get('title','').strip()}",
        f"account: {meta.get('account','').strip()}",
        f"date: {meta.get('date','').strip()}",
        f"url: {url}",
        "---",
        "",
    ]
    (out / "index.md").write_text("\n".join(fm) + markdown + "\n", encoding="utf-8")
    n_img = len(list(img_dir.glob("*")))
    print(json.dumps({"out": str(out / 'index.md'), "images": n_img,
                      "chars": len(markdown)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
