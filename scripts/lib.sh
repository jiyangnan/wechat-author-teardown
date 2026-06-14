#!/usr/bin/env bash
# Fetch + archive helpers with a config-driven engine abstraction.
# Source after config.sh. The only engine-dependent part of the whole pipeline
# lives here; html2md.py / analyze.py / render_dashboard.py are pure & portable.

_lib_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$_lib_dir/config.sh"

# Strip browse's UNTRUSTED-content wrapper lines from stdin.
strip_wrapper() { grep -vE '^--- (BEGIN|END) UNTRUSTED EXTERNAL CONTENT' || true; }

# --- Engine: navigate to URL, run a JS expression, return its value via stdout. ---
# Only the `browse` engine can render WeChat pages from a script. For `manual`,
# the agent must pre-save the page HTML (see references/fetch-engines.md).
wx_render() {  # wx_render <url> <js_expr>
  local url="$1" js="$2" eng; eng="$(effective_engine)"
  case "$eng" in
    browse)
      "$RESOLVED_BROWSE" goto "$url" >/dev/null 2>&1
      "$RESOLVED_BROWSE" js "$js" 2>/dev/null | strip_wrapper ;;
    *)
      echo "WX_ENGINE_UNSUPPORTED" ;;   # caller handles manual/requests path
  esac
}

# Extract article meta as JSON: {account,title,date,biz,album_id}
wx_meta() {  # wx_meta <url>
  wx_render "$1" '
    var name=(document.querySelector("#js_name")||{}).innerText||"";
    var title=(document.querySelector("#activity-name")||document.querySelector(".rich_media_title")||{}).innerText||"";
    var date=(document.querySelector("#publish_time")||{}).innerText||"";
    var html=document.documentElement.innerHTML;
    var biz=(html.match(/var biz = "([^"]+)"/)||[])[1]||(location.href.match(/__biz=([^&]+)/)||[])[1]||"";
    var album=(html.match(/album_id["= :]+"?(\d{10,})"?/)||[])[1]||(location.href.match(/album_id=(\d+)/)||[])[1]||"";
    JSON.stringify({account:name.trim(),title:title.trim(),date:date.trim(),biz:biz,album_id:album});
  ' | grep '{' | head -1
}

# Archive a single article -> <out>/index.md (+ images/). Honors FETCH_ENGINE.
# manual engine: if WX_HTML_FILE is set, use that pre-fetched body html (+ optional WX_META_JSON).
wx_archive_one() {  # wx_archive_one <url> <out_dir>
  local url="$1" out="$2" tmp meta eng cleanup=0; eng="$(effective_engine)"
  mkdir -p "$out"
  if [ "$eng" = "browse" ]; then
    meta=$(wx_meta "$url")
    tmp=$(mktemp "${TMPDIR:-/tmp}/wxbody.XXXXXX"); cleanup=1
    "$RESOLVED_BROWSE" js 'var e=document.querySelector("#js_content"); e? e.innerHTML : "";' 2>/dev/null | strip_wrapper > "$tmp"
  elif [ "$eng" = "manual" ] && [ -n "${WX_HTML_FILE:-}" ]; then
    meta="${WX_META_JSON:-{}}"
    tmp="$WX_HTML_FILE"
  else
    echo "{\"error\":\"engine '$eng' cannot render WeChat from a script — use FETCH_ENGINE=browse or the manual hand-off (references/fetch-engines.md)\",\"url\":\"$url\"}"
    return 2
  fi
  if [ ! -s "$tmp" ]; then
    echo "{\"error\":\"empty body (env-check page? retry)\",\"url\":\"$url\"}"
    [ "$cleanup" = 1 ] && rm -f "$tmp"; return 1
  fi
  python3 "$_lib_dir/html2md.py" "$tmp" "$out" "$url" "$meta"
  [ "$cleanup" = 1 ] && rm -f "$tmp"
  return 0
}
