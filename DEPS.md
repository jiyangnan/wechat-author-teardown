# 运行依赖

`bash scripts/doctor.sh` 会自动检测下面所有项并给出缺失提示。

## 硬依赖（缺了管线跑不动）
| 依赖 | 检测 | 安装 |
|---|---|---|
| Python 3.8+ | `python3 -V` | macOS: `brew install python` / Linux: 系统包管理器 |
| beautifulsoup4 | `python3 -c "import bs4"` | `pip install beautifulsoup4` |
| markdownify | `python3 -c "import markdownify"` | `pip install markdownify` |
| requests | `python3 -c "import requests"` | `pip install requests` |
| jq | `command -v jq` | `brew install jq` / `apt install jq` |

一行装齐 python 依赖：`python3 -m pip install beautifulsoup4 markdownify requests`

## 抓取引擎（至少一个，详见 references/fetch-engines.md）
| 引擎 | 说明 | 准备 |
|---|---|---|
| gstack `browse`（首选） | Bun+Playwright CDP，过微信验证最稳 | 装 gstack；`config.env` 设 `BROWSE_BIN` |
| `requests` | 仅合集枚举常可用 | 无需额外安装（正文需另想办法） |
| `manual` | agent 用自带浏览器 MCP 取 HTML | 你这个 agent 有任意浏览器 MCP 即可 |

## 不依赖
- 不需要 jieba（中文分词用正则 n-gram）。
- 不需要 jinja2 / pyyaml（看板用纯字符串模板；配置用 .env）。
- 不需要 pandoc（markdownify 直接转）。

## 平台
macOS / Linux 均可。注意：脚本兼容 macOS 自带 bash 3.2（不用 `mapfile` 等 4.x 特性）。
