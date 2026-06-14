#!/usr/bin/env bash
# Pre-flight check. Any agent runs this FIRST to learn what's available and what
# to install. Exit 0 = ready to run (some engine + all converters present).
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/config.sh"

ok=0; warn=0; fail=0
pass(){ echo "  ✓ $1"; ok=$((ok+1)); }
note(){ echo "  ⚠ $1"; warn=$((warn+1)); }
bad(){  echo "  ✗ $1"; fail=$((fail+1)); }

echo "== wechat-author-teardown · doctor =="

echo "[1] 转换/分析依赖（硬性，缺了管线跑不动）"
command -v python3 >/dev/null && pass "python3 ($(python3 -V 2>&1))" || bad "python3 缺失"
for m in bs4 markdownify requests; do
  python3 -c "import $m" 2>/dev/null && pass "python: $m" || bad "python 模块 $m 缺失 → pip install ${m/bs4/beautifulsoup4}"
done
command -v jq >/dev/null && pass "jq" || bad "jq 缺失 → brew install jq / apt install jq"

echo "[2] 抓取引擎（至少要有一个能渲染微信页）"
eng="$(effective_engine)"
echo "  config FETCH_ENGINE=$FETCH_ENGINE → 生效引擎: $eng"
if [ -n "$RESOLVED_BROWSE" ]; then
  pass "browse 引擎可用: $RESOLVED_BROWSE"
else
  note "未找到 gstack browse 二进制（最稳引擎）。可在 config.env 设 BROWSE_BIN，或改用 manual 引擎（见 references/fetch-engines.md）"
fi
if [ "$eng" != "browse" ]; then
  note "当前生效引擎=$eng：合集枚举可能仍可用（requests），但正文渲染需 browse 或 manual 手递 HTML"
fi

echo "[3] 配置"
[ -f "$HERE/../config.env" ] && pass "config.env 已自定义" || note "用默认配置（无 config.env）。如需改路径/开回流：cp config.example.env config.env"
echo "  ARCHIVE_ROOT=$ARCHIVE_ROOT"
echo "  OBSIDIAN_ENABLED=$OBSIDIAN_ENABLED"
[ "$OBSIDIAN_ENABLED" = "true" ] && { [ -d "$OBSIDIAN_VAULT" ] && pass "Obsidian vault 存在" || bad "OBSIDIAN_ENABLED=true 但 vault 路径不存在: $OBSIDIAN_VAULT"; }

echo
echo "结果: ✓$ok  ⚠$warn  ✗$fail"
if [ "$fail" -gt 0 ]; then
  echo "→ 有硬性依赖缺失，先按上面提示安装再跑。"; exit 1
fi
if [ -z "$RESOLVED_BROWSE" ] && [ "$eng" != "manual" ]; then
  echo "→ 无脚本可用引擎：要么装 browse，要么用 FETCH_ENGINE=manual + 浏览器 MCP 手递 HTML。"; exit 1
fi
echo "→ 就绪。建议接着跑 scripts/smoke_test.sh 做一次冒烟验收。"; exit 0
