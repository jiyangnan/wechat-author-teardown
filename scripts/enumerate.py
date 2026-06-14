#!/usr/bin/env python3
"""Enumerate a WeChat author's recent article URLs from one seed article.

Primary strategy: the 合集 (album) JSON API, paginated via begin_msgid /
begin_itemidx so it auto-walks back through 往期 until it has N urls or the
album is exhausted (continue_flag != 1).

Fetching is delegated to the gstack `browse` binary (proven WeChat-capable on
this machine): we navigate to the album JSON endpoint and read document.body.

Usage:
    enumerate.py <seed_url> [N=20] [browse_path]

Output (stdout): JSON {account, biz, album_id, count, urls:[...], note}
Progress is printed to stderr.
"""
import sys, os, json, subprocess, re


def browse_bin(override=None):
    if override:
        return override
    root = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True).stdout.strip()
    for cand in ([os.path.join(root, ".claude/skills/gstack/browse/dist/browse")] if root else []) + \
                [os.path.expanduser("~/.claude/skills/gstack/browse/dist/browse")]:
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    sys.exit("browse binary not found")


def strip_wrapper(text):
    return "\n".join(l for l in text.splitlines()
                     if not l.strip().startswith("--- BEGIN UNTRUSTED")
                     and not l.strip().startswith("--- END UNTRUSTED")).strip()


def b_goto(B, url):
    subprocess.run([B, "goto", url], capture_output=True, text=True)


def b_js(B, expr):
    r = subprocess.run([B, "js", expr], capture_output=True, text=True)
    return strip_wrapper(r.stdout)


def get_meta(B, url):
    b_goto(B, url)
    expr = (
        'var name=(document.querySelector("#js_name")||{}).innerText||"";'
        'var html=document.documentElement.innerHTML;'
        'var biz=(html.match(/var biz = "([^"]+)"/)||[])[1]||(location.href.match(/__biz=([^&]+)/)||[])[1]||"";'
        'var alb=(html.match(/album_id["= :]+"?(\\d{10,})"?/)||[])[1]||(location.href.match(/album_id=(\\d+)/)||[])[1]||"";'
        'JSON.stringify({account:name.trim(),biz:biz,album_id:alb});'
    )
    out = b_js(B, expr)
    m = re.search(r"\{.*\}", out, re.S)
    return json.loads(m.group(0)) if m else {"account": "", "biz": "", "album_id": ""}


def fetch_album_page(B, biz, album_id, count, begin_msgid="", begin_itemidx=""):
    api = (f"https://mp.weixin.qq.com/mp/appmsgalbum?action=getalbum"
           f"&__biz={biz}&album_id={album_id}&count={count}&f=json")
    if begin_msgid:
        api += f"&begin_msgid={begin_msgid}&begin_itemidx={begin_itemidx}"
    b_goto(B, api)
    raw = b_js(B, "document.body.innerText")
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def main():
    seed = sys.argv[1] if len(sys.argv) > 1 else sys.exit("seed url required")
    N = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    B = browse_bin(sys.argv[3] if len(sys.argv) > 3 else None)

    meta = get_meta(B, seed)
    biz, album_id, account = meta.get("biz", ""), meta.get("album_id", ""), meta.get("account", "")
    sys.stderr.write(f"[meta] account={account} biz={biz} album_id={album_id or 'none'}\n")

    urls, seen = [], set()
    note = ""

    if album_id and biz:
        begin_msgid = begin_itemidx = ""
        page = 0
        while len(urls) < N:
            page += 1
            data = fetch_album_page(B, biz, album_id, min(N, 20), begin_msgid, begin_itemidx)
            resp = (data or {}).get("getalbum_resp", {})
            lst = resp.get("article_list", []) or []
            if not lst:
                break
            for a in lst:
                u = (a.get("url") or "").replace("\\/", "/")
                if u and u not in seen:
                    seen.add(u)
                    urls.append({"title": a.get("title", ""), "url": u})
            sys.stderr.write(f"[album] page {page}: +{len(lst)} (total {len(urls)})\n")
            if str(resp.get("continue_flag")) != "1":
                break
            last = lst[-1]
            begin_msgid, begin_itemidx = last.get("msgid", ""), last.get("itemidx", "")
        note = "enumerated via 合集 album API"
    else:
        note = "no 合集 detected; only seed url returned (pass extra seeds or use a logged-in browse session for 历史消息)"

    # The album already contains the seed (newest-first). Only fall back to the
    # bare seed url when album enumeration produced nothing.
    if not urls:
        urls.insert(0, {"title": "(seed)", "url": seed})

    urls = urls[:N]
    print(json.dumps({"account": account, "biz": biz, "album_id": album_id,
                      "count": len(urls), "urls": urls, "note": note},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
