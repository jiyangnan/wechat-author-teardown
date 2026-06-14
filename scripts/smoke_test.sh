#!/usr/bin/env bash
# Acceptance smoke test (CONTRACT.md). Runs the full pipeline on one seed url
# at N=2 and asserts the contract. Exit 0 = the bundle works end-to-end here.
#
# Usage: smoke_test.sh [seed_url]
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SEED="${1:-https://mp.weixin.qq.com/s/fG7mdtQeO03lxcS406apow}"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/wxsmoke.XXXXXX")"
fail=0; chk(){ if eval "$2"; then echo "  ✓ $1"; else echo "  ✗ $1"; fail=$((fail+1)); fi; }

echo "== smoke test (N=2) seed=$SEED =="
ROOT=$(bash "$HERE/archive_batch.sh" "$SEED" 2 "$TMP/arch" 2>/dev/null)
chk "归档目录生成"        '[ -d "$TMP/arch/articles" ]'
chk "至少1篇 index.md"    '[ "$(find "$TMP/arch/articles" -name index.md | wc -l)" -ge 1 ]'
chk "正文非空(>500字符)"  '[ "$(jq "[.[]|select(.chars>500)]|length" "$TMP/arch/manifest.json" 2>/dev/null)" -ge 1 ]'
chk "至少下到1张图"       '[ "$(find "$TMP/arch/articles" -type f \( -name "*.jpg" -o -name "*.png" \) | wc -l)" -ge 1 ]'

python3 "$HERE/analyze.py" "$TMP/arch" "$TMP/analysis.json" >/dev/null 2>&1
chk "analyze 产出 json"   '[ -f "$TMP/analysis.json" ]'
chk "article_count>=1"    '[ "$(jq ".article_count" "$TMP/analysis.json" 2>/dev/null)" -ge 1 ]'

python3 "$HERE/render_dashboard.py" "$TMP/analysis.json" "$TMP/dashboard.html" >/dev/null 2>&1
chk "dashboard.html 生成" '[ -s "$TMP/dashboard.html" ]'
chk "看板含全部区块"      'grep -q 关键词 "$TMP/dashboard.html" && grep -q 金句墙 "$TMP/dashboard.html"'

echo
if [ "$fail" -eq 0 ]; then echo "✅ CONTRACT 通过，bundle 在本机可用。产物: $TMP"; exit 0
else echo "❌ $fail 项未通过，见上。产物留存: $TMP"; exit 1; fi
