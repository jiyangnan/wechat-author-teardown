#!/usr/bin/env python3
"""Lightweight corpus analysis over a folder of archived articles (Markdown).

Reads every `index.md` (or *.md) under <input_dir>, parses front-matter, and
computes the descriptive stats that feed a methodology dashboard:
  - 选题分布 (topic clusters from title keywords)
  - 关键词 (Chinese 2/3-gram + ASCII tech-term frequency, stopword-filtered)
  - 标题模式 (length stats + pattern flags: 数字/问句/第一人称/冒号/书名号/钩子词)
  - 文章结构 (字数/段落/小标题/配图 分布)
  - 金句候选 (heuristic punchline extraction with source)

No external NLP deps (no jieba) — deliberately lightweight, as advertised.

Usage: analyze.py <input_dir> [out_json=analysis.json]
"""
import sys, os, re, json, glob, collections

# Common Chinese function words / fillers to drop from n-gram salience.
STOP = set("的了是在我你他她它们和与及就都也还又很非常这那有没不一个我们你们他们"
           "可以这个那个就是不是这样那样什么怎么因为所以但是如果虽然然后还是已经"
           "自己大家其实现在很多一些这些那些时候东西真的感觉知道觉得开始通过对于"
           "之后之前一下这种一种最后比如以及或者然而而且不过只是这里那里出来起来")
PUNCT = "，。！？、；：""''（）【】《》…—~,.!?;:\"'()[]<>"

HOOK_WORDS = ["实测", "教程", "保姆级", "开源", "附", "手把手", "踩坑", "复盘",
              "免费", "最全", "终于", "竟然", "居然", "我用", "我让", "我做了"]


def read_articles(input_dir):
    root = os.path.abspath(input_dir)
    files = sorted(glob.glob(os.path.join(input_dir, "**", "index.md"), recursive=True))
    if not files:
        files = sorted(glob.glob(os.path.join(input_dir, "**", "*.md"), recursive=True))
    # Drop root-level meta files (INDEX.md / README.md). On case-insensitive
    # filesystems INDEX.md collides with the index.md glob, and meta files like
    # manifest indexes are not articles.
    META = {"index.md", "readme.md", "manifest.md", "methodology-report.md", "components.md"}
    files = [f for f in files
             if not (os.path.dirname(os.path.abspath(f)) == root
                     and os.path.basename(f).lower() in META)]
    arts = []
    for f in files:
        txt = open(f, encoding="utf-8", errors="ignore").read()
        meta = {}
        body = txt
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", txt, re.S)
        if m:
            for line in m.group(1).splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
            body = m.group(2)
        title = meta.get("title") or os.path.basename(os.path.dirname(f))
        arts.append({"file": f, "title": title, "meta": meta,
                     "body": body, "text": clean_for_nlp(body)})
    return arts


# WeChat UI chrome that leaks into #js_content (embedded video/mp-common cards).
BOILER = ["已关注", "观看更多", "退出全屏", "切换到", "正在加载", "继续滑动",
          "轻触阅读原文", "向上滑动", "长按识别", "扫一扫", "视频加载失败",
          "点击上方", "关注公众号", "预览时标签不可点"]


def clean_for_nlp(body):
    """Strip markdown images/links/urls/code + WeChat UI boilerplate."""
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", body)          # images
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)            # links -> keep text
    t = re.sub(r"https?://\S+", " ", t)                       # bare urls
    t = re.sub(r"`[^`]*`", " ", t)                            # inline code
    t = re.sub(r"images/\S+", " ", t)                         # leftover local paths
    for b in BOILER:
        t = t.replace(b, " ")
    return t


def cn_runs(text):
    return re.findall(r"[一-鿿]{2,}", text)


def ngram_freq(arts, n, topk, min_count=3):
    c = collections.Counter()
    for a in arts:
        for run in cn_runs(a["text"]):
            for i in range(len(run) - n + 1):
                g = run[i:i+n]
                if g in STOP:
                    continue
                if any(ch in STOP for ch in g) and n == 2:
                    continue
                c[g] += 1
    return [{"term": t, "count": n_} for t, n_ in c.most_common(topk*3)
            if n_ >= min_count][:topk]


def ascii_terms(arts, topk):
    c = collections.Counter()
    for a in arts:
        for w in re.findall(r"[A-Za-z][A-Za-z0-9.+#-]{1,}", a["text"]):
            if len(w) <= 1:
                continue
            c[w] += 1
    return [{"term": t, "count": n} for t, n in c.most_common(topk)]


def title_patterns(arts):
    pats = collections.Counter()
    lengths = []
    for a in arts:
        t = a["title"]
        lengths.append(len(t))
        if re.search(r"\d", t):
            pats["含数字"] += 1
        if "?" in t or "？" in t:
            pats["问句式"] += 1
        if re.search(r"[我你]", t):
            pats["第一/第二人称"] += 1
        if "：" in t or ":" in t:
            pats["冒号分段"] += 1
        if re.search(r"[《》「」\"]", t):
            pats["书名号/引号"] += 1
        if "，" in t or "," in t:
            pats["逗号断句"] += 1
        for h in HOOK_WORDS:
            if h in t:
                pats[f"钩子词·{h}"] += 1
    avg = round(sum(lengths)/len(lengths), 1) if lengths else 0
    return {"avg_len": avg, "min_len": min(lengths or [0]), "max_len": max(lengths or [0]),
            "patterns": [{"name": k, "count": v} for k, v in pats.most_common()]}


def structure_stats(arts):
    rows = []
    for a in arts:
        body = a["body"]
        chars = len(re.sub(r"\s", "", body))
        paras = len([p for p in re.split(r"\n\s*\n", body) if p.strip()])
        heads = len(re.findall(r"^#{1,6}\s", body, re.M))
        imgs = len(re.findall(r"!\[", body))
        rows.append({"title": a["title"], "chars": chars, "paras": paras,
                     "heads": heads, "imgs": imgs})
    n = len(rows) or 1
    return {"per_article": rows,
            "avg_chars": round(sum(r["chars"] for r in rows)/n),
            "avg_paras": round(sum(r["paras"] for r in rows)/n, 1),
            "avg_imgs": round(sum(r["imgs"] for r in rows)/n, 1)}


def punchlines(arts, topk=30):
    out = []
    markers = ["才是", "不是", "而是", "本质", "真正", "最", "就是", "不过是",
               "关键", "其实", "永远", "唯一", "决定", "区别", "答案", "不要"]
    AD = ["奖池", "挑战季", "OPC", "扫码", "万", "报名", "抽奖", "打卡"]
    for a in arts:
        for sent in re.split(r"[。！？\n]", a["text"]):
            s = sent.strip().strip("*#>—-• \t").strip(PUNCT)
            if not (8 <= len(s) <= 42):
                continue
            if not re.search(r"[一-鿿]", s):
                continue
            if any(ad in s for ad in AD):   # skip promo/marketing lines
                continue
            if any(mk in s for mk in markers):
                out.append({"text": s, "from": a["title"]})
    # de-dup, keep order
    seen, uniq = set(), []
    for p in out:
        if p["text"] in seen:
            continue
        seen.add(p["text"])
        uniq.append(p)
    return uniq[:topk]


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: analyze.py <input_dir> [out_json]")
    input_dir = sys.argv[1]
    out_json = sys.argv[2] if len(sys.argv) > 2 else "analysis.json"

    arts = read_articles(input_dir)
    if not arts:
        sys.exit(f"no markdown articles found under {input_dir}")

    account = ""
    dates = []
    for a in arts:
        account = account or a["meta"].get("account", "")
        d = a["meta"].get("date", "")
        if d:
            dates.append(d)

    result = {
        "account": account,
        "article_count": len(arts),
        "date_range": [min(dates), max(dates)] if dates else [],
        "titles": [a["title"] for a in arts],
        "keywords_2gram": ngram_freq(arts, 2, 40),
        "keywords_3gram": ngram_freq(arts, 3, 25, min_count=2),
        "tech_terms": ascii_terms(arts, 25),
        "title_analysis": title_patterns(arts),
        "structure": structure_stats(arts),
        "punchlines": punchlines(arts),
    }
    json.dump(result, open(out_json, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(json.dumps({"out": out_json, "articles": len(arts),
                      "account": account, "punchlines": len(result["punchlines"])},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
