#!/usr/bin/env bash
set -euo pipefail

SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK_DIR="$(mktemp -d)"
WEB_PID=""
CONFLICT_PID=""
GUI_PID=""
trap 'for pid in "${WEB_PID:-}" "${CONFLICT_PID:-}" "${GUI_PID:-}"; do if [ -n "$pid" ] && kill -0 "$pid" >/dev/null 2>&1; then kill "$pid" >/dev/null 2>&1 || true; wait "$pid" 2>/dev/null || true; fi; done; rm -rf "$WORK_DIR"' EXIT

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
import os
import urllib.request

url, output = sys.argv[1], sys.argv[2]
request = urllib.request.Request(url)
if os.environ.get("WEB_TOKEN"):
    request.add_header("Authorization", f"Bearer {os.environ['WEB_TOKEN']}")
with urllib.request.urlopen(request, timeout=5) as response:
    body = response.read()
with open(output, "wb") as handle:
    handle.write(body)
PY
}

request_json() {
  local method="$1"
  local url="$2"
  local body="$3"
  local output="$4"
  python3 - "$method" "$url" "$body" "$output" <<'PY'
import json
import os
import sys
import urllib.request

method, url, body, output = sys.argv[1:]
request = urllib.request.Request(url, data=body.encode("utf-8") if body else None, method=method)
request.add_header("Authorization", f"Bearer {os.environ['WEB_TOKEN']}")
request.add_header("Content-Type", "application/json")
with urllib.request.urlopen(request, timeout=15) as response:
    payload = json.load(response)
with open(output, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, indent=2)
PY
}

OFFICE="$SOURCE_ROOT/agent-system/bin/office-system"
[ -x "$OFFICE" ] || fail "office-system not executable: $OFFICE"
[ -x "$SOURCE_ROOT/digital-office-gui" ] || fail "digital-office-gui not executable: $SOURCE_ROOT/digital-office-gui"
[ -x "$SOURCE_ROOT/agent-system/bin/digital-office-gui" ] || fail "digital-office-gui bin not executable"
"$SOURCE_ROOT/digital-office-gui" --help >/dev/null
"$SOURCE_ROOT/agent-system/bin/digital-office-gui" --help >/dev/null

cp -a "$SOURCE_ROOT/agent-system" "$WORK_DIR/agent-system"
cp -a "$SOURCE_ROOT/skills" "$WORK_DIR/skills"
export DIGITAL_OFFICE_SYSTEM_HOME="$WORK_DIR/agent-system"

test -f "$SOURCE_ROOT/agent-system/web/app/index.html" || fail "missing web index"
test -f "$SOURCE_ROOT/agent-system/web/app/manifest.webmanifest" || fail "missing manifest"
test -f "$SOURCE_ROOT/agent-system/web/app/service-worker.js" || fail "missing service worker"

"$OFFICE" web-config --public-url http://127.0.0.1 >"$WORK_DIR/web-config.json"
json_assert "$WORK_DIR/web-config.json" 'data["kind"] == "digital-office-web-app-config" and data["pwa"]["installable_shell"] is True'
json_assert "$WORK_DIR/web-config.json" 'any(route["path"] == "/api/gui-state" for route in data["api"]["read_routes"])'
json_assert "$WORK_DIR/web-config.json" '"Bearer token" in data["api"]["authentication"]'

read -r CONFLICT_PORT NEXT_PORT < <(python3 - <<'PY'
import socket

for port in range(20000, 60000):
    sockets = []
    try:
        for candidate in (port, port + 1):
            sock = socket.socket()
            sock.bind(("127.0.0.1", candidate))
            sockets.append(sock)
    except OSError:
        continue
    finally:
        for sock in sockets:
            sock.close()
    print(port, port + 1)
    break
else:
    raise SystemExit("no consecutive test ports available")
PY
)

python3 -m http.server "$CONFLICT_PORT" --bind 127.0.0.1 >"$WORK_DIR/conflict.log" 2>&1 &
CONFLICT_PID=$!
conflict_ready=0
for _ in $(seq 1 50); do
  if fetch "http://127.0.0.1:$CONFLICT_PORT/" "$WORK_DIR/conflict.html" >/dev/null 2>&1; then
    conflict_ready=1
    break
  fi
  sleep 0.1
done
[ "$conflict_ready" -eq 1 ] || fail "conflict test server did not become ready"

set +e
"$WORK_DIR/agent-system/bin/digital-office-gui" --background --no-open --port "$CONFLICT_PORT" --quiet >"$WORK_DIR/gui-explicit.out" 2>&1
explicit_port_code=$?
set -e
[ "$explicit_port_code" -eq 2 ] || fail "explicit occupied GUI port was not rejected"
grep -q "port $CONFLICT_PORT is already in use" "$WORK_DIR/gui-explicit.out" || fail "explicit port conflict was not explained"

DIGITAL_OFFICE_GUI_PORT="$CONFLICT_PORT" "$WORK_DIR/agent-system/bin/digital-office-gui" --background --no-open --quiet >"$WORK_DIR/gui-auto.out" 2>&1
grep -q "Port $CONFLICT_PORT is busy; using $NEXT_PORT instead" "$WORK_DIR/gui-auto.out" || fail "GUI did not report its automatically selected port"
GUI_PID="$(cat "$WORK_DIR/agent-system/tmp/digital-office-gui.pid")"
fetch "http://127.0.0.1:$NEXT_PORT/healthz" "$WORK_DIR/gui-auto-health.json"
json_assert "$WORK_DIR/gui-auto-health.json" 'data["status"] == "ok"'
kill "$GUI_PID" >/dev/null 2>&1 || true
wait "$GUI_PID" 2>/dev/null || true
GUI_PID=""
kill "$CONFLICT_PID" >/dev/null 2>&1 || true
wait "$CONFLICT_PID" 2>/dev/null || true
CONFLICT_PID=""

set +e
timeout 2 "$OFFICE" web-serve --host 0.0.0.0 --port 0 --quiet >"$WORK_DIR/non-loopback.out" 2>"$WORK_DIR/non-loopback.err"
non_loopback_code=$?
set -e
[ "$non_loopback_code" -eq 2 ] || fail "non-loopback web server started without authentication token"
grep -q "requires a Bearer token" "$WORK_DIR/non-loopback.err" || fail "non-loopback denial did not explain token requirement"

WEB_PORT="$(python3 - <<'PY'
import socket

sock = socket.socket()
sock.bind(("127.0.0.1", 0))
print(sock.getsockname()[1])
sock.close()
PY
)"

DIGITAL_OFFICE_WEB_TOKEN="smoke-web-token" "$OFFICE" web-serve --host 127.0.0.1 --port "$WEB_PORT" --public-url "http://127.0.0.1:$WEB_PORT" --user smoke-admin --role owner --quiet >"$WORK_DIR/web.log" 2>&1 &
WEB_PID=$!

BASE_URL="http://127.0.0.1:$WEB_PORT"
ready=0
for _ in $(seq 1 50); do
  if fetch "$BASE_URL/healthz" "$WORK_DIR/healthz.json" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 0.1
done
[ "$ready" -eq 1 ] || { cat "$WORK_DIR/web.log" >&2 || true; fail "web server did not become ready"; }

python3 - "$BASE_URL/api/gui-state" <<'PY'
import sys
import urllib.error
import urllib.request

try:
    urllib.request.urlopen(sys.argv[1], timeout=5)
except urllib.error.HTTPError as exc:
    assert exc.code == 401, exc.code
else:
    raise SystemExit("API accepted a request without Bearer authentication")
PY

export WEB_TOKEN="smoke-web-token"
fetch "$BASE_URL/api/health" "$WORK_DIR/health.json"

fetch "$BASE_URL/api/web-app" "$WORK_DIR/web-app.json"
fetch "$BASE_URL/api/gui-state?limit=5" "$WORK_DIR/gui-state.json"
fetch "$BASE_URL/manifest.webmanifest" "$WORK_DIR/manifest.webmanifest"
fetch "$BASE_URL/service-worker.js" "$WORK_DIR/service-worker.js"
fetch "$BASE_URL/" "$WORK_DIR/index.html"
fetch "$BASE_URL/admin" "$WORK_DIR/admin.html"

request_json POST "$BASE_URL/api/agents" '{"agent_id":"web-smoke-writer","display_name":"Web Smoke Writer","role_description":"Web lifecycle verification","template_agent_id":"writer","keywords":["web smoke"]}' "$WORK_DIR/agent-created.json"
request_json POST "$BASE_URL/api/agents/web-smoke-writer/status" '{"status":"archived","reason":"web smoke cleanup"}' "$WORK_DIR/agent-archived.json"
request_json DELETE "$BASE_URL/api/agents/web-smoke-writer?confirmed=true" '' "$WORK_DIR/agent-deleted.json"
request_json POST "$BASE_URL/api/projects" '{"project_id":"web-smoke-project","name":"Web Smoke Project"}' "$WORK_DIR/project-created.json"
request_json POST "$BASE_URL/api/knowledge/uploads" '{"scope":"project","project_id":"web-smoke-project","title":"Web Smoke Note","body":"alpha beta gamma","approve":true}' "$WORK_DIR/knowledge-uploaded.json"

json_assert "$WORK_DIR/healthz.json" 'len(data) == 2 and "status" in data and "timestamp" in data and data["status"] == "ok"'
json_assert "$WORK_DIR/health.json" 'data["status"] == "ok" and data["checks"]["web_index"] is True and data["checks"]["service_worker"] is True'
json_assert "$WORK_DIR/web-app.json" 'data["pwa"]["installable_shell"] is True and data["api"]["mutation_policy"].startswith("Mutating GUI actions")'
json_assert "$WORK_DIR/web-app.json" 'any(route["method"] == "POST" and route["path"] == "/api/agents" for route in data["api"]["mutation_routes"])'
json_assert "$WORK_DIR/web-app.json" 'any(route["method"] == "POST" and route["path"] == "/api/projects" for route in data["api"]["mutation_routes"])'
json_assert "$WORK_DIR/web-app.json" 'any(route["method"] == "POST" and route["path"] == "/api/knowledge/uploads" for route in data["api"]["mutation_routes"])'
json_assert "$WORK_DIR/gui-state.json" '"web_ui_pwa" in [item["id"] for item in data["capabilities"]]'
json_assert "$WORK_DIR/manifest.webmanifest" 'data["display"] == "standalone" and data["start_url"] == "/"'
json_assert "$WORK_DIR/agent-created.json" 'data["agent_id"] == "web-smoke-writer" and data["status"] == "active"'
json_assert "$WORK_DIR/agent-archived.json" 'data["agent_id"] == "web-smoke-writer" and data["status"] == "archived"'
json_assert "$WORK_DIR/agent-deleted.json" 'data["agent_id"] == "web-smoke-writer" and data["status"] == "deleted" and data["history_preserved"] is True'
json_assert "$WORK_DIR/project-created.json" 'data["status"] == "created" and data["project_id"] == "web-smoke-project"'
json_assert "$WORK_DIR/knowledge-uploaded.json" 'data["status"] == "uploaded" and data["entry"]["scope"] == "project" and data["entry"]["agent_readable"] is True'
grep -q "digital-office-shell-v2" "$WORK_DIR/service-worker.js" || fail "service worker cache contract missing"
grep -q '<div id="root"></div>' "$WORK_DIR/index.html" || fail "user application root not served"
grep -q '<div id="root"></div>' "$WORK_DIR/admin.html" || fail "admin application route not served"
grep -q '/assets/index-' "$WORK_DIR/index.html" || fail "production web assets not linked"
grep -q 'sidebar-projects' "$SOURCE_ROOT"/agent-system/web/app/assets/index-*.css || fail "project tree styles missing from production assets"
grep -q 'conversation-tree-link' "$SOURCE_ROOT"/agent-system/web/app/assets/index-*.css || fail "conversation tree styles missing from production assets"
grep -q '返回项目列表' "$SOURCE_ROOT"/agent-system/web/app/assets/index-*.js || fail "project back navigation missing from production assets"

echo "web-pwa-smoke-ok"
