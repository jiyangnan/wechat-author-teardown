# 验收契约（CONTRACT）

别的 agent / 别的机器装好后，靠这份契约**自证"我这儿确实跑得通"**，而不是凭感觉。
一键执行：`bash scripts/smoke_test.sh [seed_url]`（默认用一个已知可用的 seed，N=2）。

## 通过判据（全部满足才算 PASS）

| # | 断言 | 说明 |
|---|---|---|
| 1 | 生成 `articles/` 目录 | 采集启动成功 |
| 2 | ≥1 篇 `index.md` | 至少一篇归档成功 |
| 3 | ≥1 篇正文 > 500 字符 | 抓到的是真正文，不是验证页 |
| 4 | ≥1 张图片落地 | 图片本地化生效 |
| 5 | `analyze.py` 产出 `analysis.json` | 数据分析跑通 |
| 6 | `article_count >= 1` | 分析识别到文章 |
| 7 | 生成非空 `dashboard.html` | 看板渲染成功 |
| 8 | 看板含「关键词」「金句墙」区块 | 模板完整 |

## 失败排查
- 全失败 / 卡住 → 先 `bash scripts/doctor.sh` 看引擎和依赖。
- 断言 3 失败（正文是验证页）→ 抓取引擎过不了微信环境验证：换 `browse`，或用 `manual` 手递 HTML。
- 断言 4 失败（无图）→ 网络/Referer 问题；`html2md.py` 会保留远程 URL 兜底，不致命。
- 断言 1/2 失败且引擎是 requests → 正文渲染不支持 requests，见 references/fetch-engines.md。

## 何时重跑契约
- 换机器 / 换 agent 后首次使用。
- 改了 `config.env` 的引擎或路径后。
- 微信页面结构变化导致选择器失效（`#js_content` / `#js_name` 等）时。
