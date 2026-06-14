---
name: wechat-author-teardown
description: >
  公众号博主拆解全流程：给一个微信公众号文章链接，自动识别博主、走合集 API 枚举其
  近期 N 篇（默认 20，自动翻往期），逐篇抓正文转 Markdown + 图片本地化，做轻量数据分析
  （选题分布/关键词/标题模式/结构/金句），拆解作者方法论（六维度），生成方法论报告 +
  自包含 HTML 看板，提炼可复用写作组件，可选回流到知识库。
  触发词：拆解公众号博主、归档某个号、研究爆款博主方法论、wechat author teardown、
  把这个号的文章扒下来分析、做个写作组件库。
metadata:
  version: 1.0.0
  origin: 由 Claude Code 按苍何同名平台 skill 的能力描述重写，去个人化、可跨 agent 移植
  portability: 配置外置(config.env) + 引擎抽象 + doctor 自检 + CONTRACT 冒烟测试
---

# wechat-author-teardown · 公众号博主拆解（可移植版）

一个链接 → 这个博主的全套归档 + 方法论报告 + 数据看板 + 可复用写作组件。
**为跨 agent / 跨机器移植而设计**：路径全外置、抓取引擎可降级、自带体检与验收测试。

## 接入流程（任何 agent 首次使用务必照做）
1. **体检**：`bash scripts/doctor.sh` —— 查依赖与可用抓取引擎，缺啥给安装命令。
2. **补依赖**（按 doctor 提示）：`pip install beautifulsoup4 markdownify requests` + `jq` + 一个抓取引擎。
3. **冒烟验收**：`bash scripts/smoke_test.sh` —— 跑通 1 个真实链接的全链路，绿了才信任。
4. **（可选）配置**：`cp config.example.env config.env` 改路径 / 开回流。
通过这四步，bundle 才算在你这个 agent / 这台机器上「稳了」。

## 依赖与引擎
- 硬依赖：`python3` + `beautifulsoup4 markdownify requests` + `jq`。详见 [DEPS.md](DEPS.md)。
- 抓取引擎（至少一个，见 [references/fetch-engines.md](references/fetch-engines.md)）：
  - `browse`（gstack，Bun+Playwright CDP）—— 过微信环境验证最稳，**首选**。
  - `requests` —— 仅合集 JSON 枚举常可用；正文常撞验证页。
  - `manual` —— 没有 browse 的 agent：用自己的浏览器 MCP 取 HTML，再手递给转换脚本。
- 引擎与所有路径都在 `config.env` 里配，脚本零硬编码。

## 工作流

### Step 1 — 确认范围
seed 链接、抓几篇（默认 20）、是否要方法论报告/看板/组件、是否开回流。用户说清就别反复问。

### Step 2 — 采集 + 归档（一条命令）
```bash
bash scripts/archive_batch.sh "<seed_url>" <N>     # 输出落 $ARCHIVE_ROOT/<账号>-<时间戳>/
```
内部：`enumerate.py`（合集 API 枚举 + 翻往期）→ 逐篇 `wx_archive_one`（抓 `#js_content`→markdownify→
并发下图本地化）→ `manifest.json` / `enumeration.json` / `INDEX.md`。篇数多时后台跑并轮询。
> 抓到空（0 字）= 撞了环境验证页，单篇重跑 `wx_archive_one` 即可（见 lib.sh）。

### Step 3 — 数据分析
```bash
python3 scripts/analyze.py "<root>" "<root>/analysis.json"
```
纯标准库，算选题分布/中文 n-gram 关键词/标题模式/结构/金句候选。描述性统计，不下判断。

### Step 4 — 拆解方法论 + 提炼组件（Agent 来做，非脚本）
- 读 `articles/*/index.md`，按 [references/methodology-rubric.md](references/methodology-rubric.md)
  写 `<root>/methodology-report.md`（六维度）。
- 按 [references/components-rubric.md](references/components-rubric.md) 写 `<root>/components.md`
  （选题脚手架/标题公式/开头/段落/转场/金句生成器/发布前清单）。
- **底线**：金句原文摘录标出处；仿写标「（仿写，非原文）」；学方法不抄答案。

### Step 5 — 渲染 HTML 看板
```bash
python3 scripts/render_dashboard.py "<root>/analysis.json" "<root>/components.md" "<root>/dashboard.html"
```
自包含单 HTML（瑞士风）。验收：browse 不能开 `file://`，需起本地 http server 再截图。

### Step 6 —（可选）回流知识库
仅当 `OBSIDIAN_ENABLED=true`。见 [references/obsidian-integration.md](references/obsidian-integration.md)。
**改用户核心文件（框架库等）前必须先列方案让用户确认**，不擅自写。

## 合规
仅供个人学习研究。尊重原作者版权，不整篇转载/洗稿/商用。已内置抓取节流防验证码。
