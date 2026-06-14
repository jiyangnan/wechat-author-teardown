#!/usr/bin/env bash
# Batch-archive an author's recent N articles from one seed url.
#
# Usage: archive_batch.sh <seed_url> [N=20] [output_root]
# Default output_root: $ARCHIVE_ROOT/<account>-<timestamp>  (config.env)
#
# Produces:
#   <root>/articles/NN-<title>/index.md (+ images/)
#   <root>/manifest.json        machine-readable article list
#   <root>/INDEX.md             human-readable 文章清单
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/lib.sh"

SEED="${1:?seed url required}"
N="${2:-20}"
ROOT="${3:-}"

# Enumerate first (also gives us the account name for the default folder).
# Pass the resolved browse binary so enumerate.py uses the same engine.
ENUM=$(python3 "$HERE/enumerate.py" "$SEED" "$N" "${RESOLVED_BROWSE:-}")
ACCOUNT=$(echo "$ENUM" | jq -r '.account // "unknown"')
[ -z "$ACCOUNT" ] && ACCOUNT="unknown"

if [ -z "$ROOT" ]; then
  TS=$(date +%Y%m%d-%H%M%S)
  ROOT="${ARCHIVE_ROOT}/${ACCOUNT}-${TS}"
fi
mkdir -p "$ROOT/articles"
echo "$ENUM" > "$ROOT/enumeration.json"

COUNT=$(echo "$ENUM" | jq '.urls | length')
echo "[batch] account=$ACCOUNT  articles=$COUNT  root=$ROOT" >&2

MANIFEST="$ROOT/manifest.json"
echo "[]" > "$MANIFEST"
INDEX="$ROOT/INDEX.md"
{ echo "# ${ACCOUNT} · 文章归档清单"; echo; echo "> 共 ${COUNT} 篇 · seed: ${SEED}"; echo; } > "$INDEX"

i=0
while [ "$i" -lt "$COUNT" ]; do
  url=$(echo "$ENUM" | jq -r ".urls[$i].url")
  title=$(echo "$ENUM" | jq -r ".urls[$i].title")
  n=$(printf "%02d" $((i+1)))
  # filesystem-safe slug: char-aware truncation (byte-cut breaks UTF-8 -> APFS rejects).
  slug=$(python3 -c "import sys,re; t=re.sub(r'[/\\\\:*?\"<>|\n\r\t]','',sys.argv[1]); print(t[:30].strip() or 'article')" "$title")
  dir="$ROOT/articles/${n}-${slug}"
  echo "[$n/$COUNT] $title" >&2
  res=$(wx_archive_one "$url" "$dir" 2>/dev/null || echo '{"error":"archive failed"}')
  imgs=$(echo "$res" | jq -r '.images // 0' 2>/dev/null || echo 0)
  chars=$(echo "$res" | jq -r '.chars // 0' 2>/dev/null || echo 0)
  # append to manifest
  jq --arg n "$n" --arg t "$title" --arg u "$url" --arg d "articles/${n}-${slug}/index.md" \
     --argjson img "${imgs:-0}" --argjson ch "${chars:-0}" \
     '. += [{seq:$n,title:$t,url:$u,path:$d,images:$img,chars:$ch}]' "$MANIFEST" > "$MANIFEST.tmp" && mv "$MANIFEST.tmp" "$MANIFEST"
  echo "${n}. [${title}](articles/${n}-${slug}/index.md) — ${chars}字 / ${imgs}图" >> "$INDEX"
  i=$((i+1))
  sleep "${THROTTLE_SECONDS:-1}"   # be gentle; high-frequency requests trigger captcha
done

echo "[batch] done -> $ROOT" >&2
echo "$ROOT"
