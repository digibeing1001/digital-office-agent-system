#!/usr/bin/env bash
set -euo pipefail

SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK_DIR="$(mktemp -d)"
WEB_PID=""
trap 'if [ -n "${WEB_PID:-}" ] && kill -0 "$WEB_PID" >/dev/null 2>&1; then kill "$WEB_PID" >/dev/null 2>&1 || true; wait "$WEB_PID" 2>/dev/null || true; fi; rm -rf "$WORK_DIR"' EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

json_assert() {
  local file="$1"
  local expr="$2"
  python3 - "$file" "$expr" <<'PY'
import json
import sys

path, expr = sys.argv[1], sys.argv[2]
with open(path, "r", encoding="utf-8") as handle:
    data = json.load(handle)
if not eval(expr, {"__builtins__": {"len": len, "any": any}}, {"data": data}):
    raise SystemExit(f"assertion failed: {expr}\n{json.dumps(data, ensure_ascii=False, indent=2)}")
PY
}

fetch() {
  local url="$1"
  local output="$2"
  python3 - "$url" "$output" <<'PY'
import sys
import urllib.request

url, output = sys.argv[1], sys.argv[2]
with urllib.request.urlopen(url, timeout=5) as response:
    body = response.read()
with open(output, "wb") as handle:
    handle.write(body)
PY
}

OFFICE="$SOURCE_ROOT/agent-system/bin/office-system"
[ -x "$OFFICE" ] || fail "office-system not executable: $OFFICE"

export DIGITAL_OFFICE_SYSTEM_HOME="$SOURCE_ROOT/agent-system"

test -f "$SOURCE_ROOT/agent-system/web/app/index.html" || fail "missing web index"
test -f "$SOURCE_ROOT/agent-system/web/app/manifest.webmanifest" || fail "missing manifest"
test -f "$SOURCE_ROOT/agent-system/web/app/service-worker.js" || fail "missing service worker"

"$OFFICE" web-config --public-url http://127.0.0.1 >"$WORK_DIR/web-config.json"
json_assert "$WORK_DIR/web-config.json" 'data["kind"] == "digital-office-web-app-config" and data["pwa"]["installable_shell"] is True'
json_assert "$WORK_DIR/web-config.json" 'any(route["path"] == "/api/gui-state" for route in data["api"]["read_routes"])'

WEB_PORT="$(python3 - <<'PY'
import socket

sock = socket.socket()
sock.bind(("127.0.0.1", 0))
print(sock.getsockname()[1])
sock.close()
PY
)"

"$OFFICE" web-serve --host 127.0.0.1 --port "$WEB_PORT" --public-url "http://127.0.0.1:$WEB_PORT" --quiet >"$WORK_DIR/web.log" 2>&1 &
WEB_PID=$!

BASE_URL="http://127.0.0.1:$WEB_PORT"
ready=0
for _ in $(seq 1 50); do
  if fetch "$BASE_URL/api/health" "$WORK_DIR/health.json" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 0.1
done
[ "$ready" -eq 1 ] || { cat "$WORK_DIR/web.log" >&2 || true; fail "web server did not become ready"; }

fetch "$BASE_URL/api/web-app" "$WORK_DIR/web-app.json"
fetch "$BASE_URL/api/gui-state?limit=5" "$WORK_DIR/gui-state.json"
fetch "$BASE_URL/manifest.webmanifest" "$WORK_DIR/manifest.webmanifest"
fetch "$BASE_URL/service-worker.js" "$WORK_DIR/service-worker.js"
fetch "$BASE_URL/" "$WORK_DIR/index.html"

json_assert "$WORK_DIR/health.json" 'data["status"] == "ok" and data["checks"]["web_index"] is True and data["checks"]["service_worker"] is True'
json_assert "$WORK_DIR/web-app.json" 'data["pwa"]["installable_shell"] is True and data["api"]["mutation_policy"].startswith("Mutating GUI actions")'
json_assert "$WORK_DIR/gui-state.json" '"web_ui_pwa" in [item["id"] for item in data["capabilities"]]'
json_assert "$WORK_DIR/manifest.webmanifest" 'data["display"] == "standalone" and data["start_url"] == "/"'
grep -q "digital-office-shell-v1" "$WORK_DIR/service-worker.js" || fail "service worker cache contract missing"
grep -q "Office control room" "$WORK_DIR/index.html" || fail "web shell index not served"

echo "web-pwa-smoke-ok"
