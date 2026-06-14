# wechat-author-teardown

公众号博主拆解全流程，打包成**可跨 agent / 跨机器稳定复现**的 skill。

> 一个微信公众号文章链接 → 这个博主的全套归档 + 方法论报告 + 数据看板 + 可复用写作组件。

## 它做什么
1. **采集归档**：识别博主 → 合集 API 枚举近期 N 篇（自动翻往期）→ 逐篇正文转 Markdown + 图片本地化。
2. **数据分析**：选题分布 / 中文 n-gram 关键词 / 标题模式 / 文章结构 / 金句候选。
3. **方法论拆解**：六维度（选题系统/分析框架/判断标准/表达模板/案例库/金句风格）。
4. **HTML 看板**：自包含瑞士风单页，含可复用写作组件。
5. **（可选）回流知识库**：精炼成果入库，模式回流框架库。

## 为什么"能稳稳复现"
| 机制 | 作用 |
|---|---|
| `scripts/doctor.sh` | 体检：缺哪个依赖/引擎，给安装命令 |
| `scripts/smoke_test.sh` + `CONTRACT.md` | 跑 1 个真实链接自证可用 |
| `config.example.env` | 路径/约定全外置，脚本零硬编码 |
| `references/fetch-engines.md` | 抓取引擎契约 + 降级（browse / requests / manual） |
| 纯 python 转换/分析 | html2md/analyze/render 不依赖任何引擎，任何 agent 可跑 |

## 快速开始
```bash
bash scripts/doctor.sh                                   # 1. 体检
python3 -m pip install beautifulsoup4 markdownify requests  # 2. 按提示补依赖
bash scripts/smoke_test.sh                               # 3. 冒烟验收
cp config.example.env config.env                         # 4.（可选）改配置/开回流
bash scripts/archive_batch.sh "<公众号文章链接>" 20      # 5. 正式跑
```

## 依赖
`python3` + `beautifulsoup4 markdownify requests` + `jq` + 一个抓取引擎。详见 [DEPS.md](DEPS.md)。
不需要 jieba / jinja2 / pandoc。兼容 macOS bash 3.2 与 Linux。

## 来历
由 Claude Code 按苍何同名平台 skill 的能力描述**重新实现**（原版无源码），去个人化、补齐可移植性。
仅供个人学习研究，尊重原作者版权，不洗稿/不商用。

## License
Apache-2.0 © Aries Warrior Flamenco. 见 [LICENSE](LICENSE)。
