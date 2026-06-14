#!/usr/bin/env python3
"""Render analysis.json (+ optional components.md) into a self-contained HTML
methodology dashboard. Swiss-international style, no external assets.

Usage: render_dashboard.py <analysis.json> [components.md] [out.html=dashboard.html]
"""
import sys, os, json, html, re


def md_min(text):
    """Tiny markdown -> HTML (headings, bold, inline code, ul/ol, paragraphs)."""
    out, in_ul, in_ol = [], False, False
    def close():
        nonlocal in_ul, in_ol
        if in_ul: out.append("</ul>"); in_ul = False
        if in_ol: out.append("</ol>"); in_ol = False
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            close(); continue
        line_e = html.escape(line)
        line_e = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line_e)
        line_e = re.sub(r"`(.+?)`", r"<code>\1</code>", line_e)
        h = re.match(r"^(#{1,6})\s+(.*)$", line.strip())
        if h:
            close(); lvl = len(h.group(1))
            out.append(f"<h{lvl+1}>{html.escape(h.group(2))}</h{lvl+1}>"); continue
        m_ol = re.match(r"^\s*\d+[.)]\s+(.*)$", line)
        m_ul = re.match(r"^\s*[-*]\s+(.*)$", line)
        if m_ol:
            if not in_ol: close(); out.append("<ol>"); in_ol = True
            body = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html.escape(m_ol.group(1)))
            out.append(f"<li>{body}</li>"); continue
        if m_ul:
            if not in_ul: close(); out.append("<ul>"); in_ul = True
            body = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html.escape(m_ul.group(1)))
            out.append(f"<li>{body}</li>"); continue
        close(); out.append(f"<p>{line_e}</p>")
    close()
    return "\n".join(out)


def bars(items, label_key, val_key, max_n=12):
    items = items[:max_n]
    mx = max([i[val_key] for i in items], default=1) or 1
    rows = []
    for it in items:
        w = round(it[val_key] / mx * 100)
        rows.append(
            f'<div class="bar"><span class="bl">{html.escape(str(it[label_key]))}</span>'
            f'<span class="bt"><i style="width:{w}%"></i></span>'
            f'<span class="bn">{it[val_key]}</span></div>')
    return "\n".join(rows)


def chips(items, key="term", val="count", max_n=40):
    items = items[:max_n]
    mx = max([i[val] for i in items], default=1) or 1
    out = []
    for it in items:
        size = 0.85 + (it[val] / mx) * 1.1
        out.append(f'<span class="chip" style="font-size:{size:.2f}rem">'
                   f'{html.escape(str(it[key]))}<sub>{it[val]}</sub></span>')
    return "\n".join(out)


def main():
    aj = sys.argv[1] if len(sys.argv) > 1 else sys.exit("usage: render_dashboard.py <analysis.json> [components.md] [out.html]")
    comp_md = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2].endswith(".md") else None
    out_html = next((a for a in sys.argv[2:] if a.endswith(".html")), "dashboard.html")

    d = json.load(open(aj, encoding="utf-8"))
    acc = html.escape(d.get("account", "") or "未知作者")
    dr = d.get("date_range", [])
    span = f"{dr[0]} ~ {dr[1]}" if dr else "—"
    st = d["structure"]

    titles_html = "\n".join(f"<li>{html.escape(t)}</li>" for t in d.get("titles", []))
    comp_html = md_min(open(comp_md, encoding="utf-8").read()) if comp_md and os.path.exists(comp_md) else \
        '<p class="muted">（未提供 components.md —— 由 Agent 按 components-rubric 填写后重渲染）</p>'

    punch_html = "\n".join(
        f'<div class="quote">{html.escape(p["text"])}<span class="src">— {html.escape(p["from"])}</span></div>'
        for p in d.get("punchlines", []))

    struct_rows = "\n".join(
        f"<tr><td>{html.escape(r['title'][:28])}</td><td>{r['chars']}</td>"
        f"<td>{r['paras']}</td><td>{r['heads']}</td><td>{r['imgs']}</td></tr>"
        for r in st["per_article"])

    page = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{acc} · 方法论看板</title>
<style>
:root{{--ink:#111;--bg:#f4f3ee;--card:#fff;--accent:#1a1aff;--y:#e8ff00;--g:#9cff57;--o:#ff5c00;--mut:#888}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,"PingFang SC","Helvetica Neue",Arial,sans-serif;line-height:1.5}}
.wrap{{max-width:980px;margin:0 auto;padding:48px 24px 80px}}
header{{border-bottom:4px solid var(--ink);padding-bottom:16px;margin-bottom:8px}}
h1{{font-size:2.6rem;margin:0;letter-spacing:-1px}}
.sub{{color:var(--mut);font-size:.95rem;margin-top:6px}}
section{{background:var(--card);border:1.5px solid var(--ink);margin-top:28px;padding:22px 24px}}
h2{{font-size:1.2rem;margin:0 0 16px;display:flex;align-items:center;gap:10px}}
h2::before{{content:"";width:14px;height:14px;background:var(--accent);display:inline-block}}
h3{{font-size:1rem;margin:18px 0 8px}}
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}
.kpi{{border:1.5px solid var(--ink);padding:14px}}
.kpi b{{font-size:2rem;display:block;line-height:1}}
.kpi span{{color:var(--mut);font-size:.8rem}}
.bar{{display:flex;align-items:center;gap:10px;margin:5px 0;font-size:.85rem}}
.bl{{width:130px;flex:none;text-align:right;color:#333}}
.bt{{flex:1;background:#eee;height:14px;position:relative}}
.bt i{{position:absolute;left:0;top:0;bottom:0;background:var(--accent);display:block}}
.bn{{width:34px;flex:none;color:var(--mut)}}
.chips{{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:baseline}}
.chip{{background:var(--y);padding:2px 8px;border:1px solid var(--ink)}}
.chip sub{{color:var(--mut);font-size:.6em;margin-left:3px}}
.chip.tech{{background:var(--g)}}
table{{width:100%;border-collapse:collapse;font-size:.85rem}}
th,td{{border:1px solid #ddd;padding:6px 8px;text-align:left}}
th{{background:var(--ink);color:#fff}}
.quotes{{columns:2;column-gap:18px}}
.quote{{break-inside:avoid;border-left:4px solid var(--o);padding:8px 12px;margin:0 0 12px;background:#faf9f4;font-size:.92rem}}
.quote .src{{display:block;color:var(--mut);font-size:.75rem;margin-top:4px}}
.titles{{columns:2;column-gap:24px;font-size:.88rem;padding-left:18px}}
.components h3{{border-left:4px solid var(--g);padding-left:8px}}
.components code{{background:#f0f0f0;padding:1px 4px}}
.muted{{color:var(--mut)}}
footer{{margin-top:40px;color:var(--mut);font-size:.78rem;text-align:center}}
@media(max-width:640px){{.kpis{{grid-template-columns:repeat(2,1fr)}}.quotes,.titles{{columns:1}}.bl{{width:88px}}}}
</style></head><body><div class="wrap">
<header>
  <h1>{acc} · 方法论看板</h1>
  <div class="sub">样本 {d.get('article_count',0)} 篇 · 时间跨度 {html.escape(span)} · author-methodology-analysis</div>
</header>

<section><h2>概览</h2>
<div class="kpis">
  <div class="kpi"><b>{d.get('article_count',0)}</b><span>文章数</span></div>
  <div class="kpi"><b>{st['avg_chars']}</b><span>平均字数</span></div>
  <div class="kpi"><b>{st['avg_paras']}</b><span>平均段落</span></div>
  <div class="kpi"><b>{st['avg_imgs']}</b><span>平均配图</span></div>
</div></section>

<section><h2>关键词 · 选题画像</h2>
<h3>高频词（中文 2-gram）</h3><div class="chips">{chips(d.get('keywords_2gram',[]))}</div>
<h3>技术 / 专有名词</h3><div class="chips">{chips([{**t,'_t':1} for t in d.get('tech_terms',[])]).replace('class="chip"','class="chip tech"')}</div>
</section>

<section><h2>标题模式</h2>
<p class="muted">平均标题长度 {d['title_analysis']['avg_len']} 字（{d['title_analysis']['min_len']}–{d['title_analysis']['max_len']}）</p>
{bars(d['title_analysis']['patterns'],'name','count')}
</section>

<section><h2>文章结构</h2>
<table><tr><th>标题</th><th>字数</th><th>段落</th><th>小标题</th><th>配图</th></tr>
{struct_rows}</table></section>

<section><h2>选题分布 · 标题清单</h2><ol class="titles">{titles_html}</ol></section>

<section><h2>金句墙</h2><div class="quotes">{punch_html}</div></section>

<section class="components"><h2>可复用写作组件</h2>{comp_html}</section>

<footer>由 author-methodology-analysis 生成 · 数据为描述性统计，方法论判断由 Agent 按 rubric 完成 · 仅供学习</footer>
</div></body></html>"""
    open(out_html, "w", encoding="utf-8").write(page)
    print(json.dumps({"out": out_html, "bytes": len(page)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
