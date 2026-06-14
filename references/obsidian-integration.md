# Obsidian 回流插件（可选）

> 这是**可选集成**，默认关闭。核心拆解管线不依赖它。开关：`config.env` 里 `OBSIDIAN_ENABLED=true`。
> 这套约定源自一个具体创作者的内容系统，**通用 agent 可整套照搬，也可换成自己的知识库结构**。

## 设计原则
- **原始归档留本地**（不进 Vault）：`$ARCHIVE_ROOT/<博主>-<日期>/`。
  一个号常有几百张图、近百 MB，进 iCloud 同步的 Vault 会拖垮同步。
- **只把精炼成果进 Vault**：报告 / 看板 / 组件 / 清单 / 数据（无图片，~几十 KB）。

## 落地步骤（OBSIDIAN_ENABLED=true 时）
1. 在 Vault 建目录：`$OBSIDIAN_VAULT/$OBSIDIAN_TEARDOWN_DIR/<博主>/`。
2. 从本地归档拷入：`methodology-report.md`、`components.md`、`dashboard.html`、
   `analysis.json`、`manifest.json`。
3. 写入口笔记 `<博主>-拆解.md`：frontmatter（博主/平台/日期/样本数）+ 一句话画像 +
   3 个可偷的招 + 本地归档路径 + 回流 checklist + `[[双链]]`。
4. **回流到框架库**：把验证有效的标题公式/钩子/句式，**带出处、纯追加**地并入
   `$OBSIDIAN_FRAMEWORK_LIBRARY`。

## 红线
- 改用户的核心文件（框架库 / 写作 SOP 等）**前，必须先列出"加到哪一节、加什么内容"让用户确认**，
  得到同意再写。**纯追加 + 出处标注，绝不改写/删除用户原有内容。**
- 回流是"分析→更新框架"闭环的一环，但人始终是把关者。

## 通用化提示
其它 agent 接入时，把上面的目录名（`内容系统/博主拆解`、`爆款框架库.md`）换成自己知识库的
对应结构即可——这些都在 `config.env` 的 `OBSIDIAN_*` 变量里，不用改脚本。
