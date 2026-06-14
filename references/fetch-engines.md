# 抓取引擎契约与降级

整条管线里**只有"拿到原始页面"这一步依赖引擎**；转换/分析（html2md.py / analyze.py /
render_dashboard.py）是纯 python，任何 agent 都能跑。所以移植的关键就是：在你这个 agent
能用的引擎下，满足下面的**能力契约**。

## 能力契约（引擎必须能提供这三样）

| 能力 | 输入 | 期望输出 |
|---|---|---|
| C1 文章元信息 | 文章 URL | `#js_name`(作者)、`#activity-name`(标题)、`var biz`、`album_id` |
| C2 正文 HTML | 文章 URL | `#js_content` 的 innerHTML（需通过微信环境验证） |
| C3 合集列表 | `__biz` + `album_id` | `appmsgalbum?action=getalbum...&f=json` 的 JSON |

C3 是普通 JSON 端点，常可用 `requests`/`curl` 直接拿；C1/C2 需要能过环境验证的真实/无头浏览器。

## 引擎选项（按稳定性排序）

### 1. `browse`（gstack，首选）
Bun + Playwright 的 CDP 无头浏览器，过微信环境验证最稳。`config.env` 设 `FETCH_ENGINE=browse`
+ `BROWSE_BIN=<路径>`。`lib.sh` 与 `enumerate.py` 直接调它。本机参考路径
`~/.claude/skills/gstack/browse/dist/browse`。

### 2. `requests`（仅够枚举）
`FETCH_ENGINE=requests`。合集 JSON(C3) 常能直接拿；但正文(C2) 经常返回环境验证页 →
只适合"已有文章 URL 列表、且能换别的方式拿正文"的场景。

### 3. `manual`（无 browse 的 agent 的通用出路）
`FETCH_ENGINE=manual`。你这个 agent 用**自己的浏览器 MCP**（Playwright MCP / Chrome MCP /
computer-use 等）打开文章页，取到所需内容，再手递给纯转换脚本：

```bash
# 1) 你用自己的浏览器 MCP 导航到文章页，取 #js_content 的 innerHTML，存成文件：
#    （示例：mcp 工具返回的 html 写到 /tmp/body.html）
# 2) 取元信息拼成 JSON：{"account":"..","title":"..","date":"..","url":".."}
# 3) 交给纯转换脚本（不依赖任何引擎）：
python3 scripts/html2md.py /tmp/body.html <out_dir> "<article_url>" '<meta_json>'
```
合集枚举(C3)：你的浏览器 MCP 导航到 getalbum JSON 端点，把 body 文本喂给
`enumerate.py` 的解析逻辑，或直接 `curl` 那个 JSON 端点。

> 脚本无法直接调用 MCP 工具（MCP 是 agent 层能力），所以 `manual` 是"agent 驱动浏览器 +
> 脚本做转换"的分工。这是没有 browse 时最通用、最诚实的路径。

## 自检
`bash scripts/doctor.sh` 会报告：硬依赖是否齐、生效引擎是什么、browse 是否找得到。
不确定能不能用，先 `bash scripts/smoke_test.sh` 跑一篇验。
