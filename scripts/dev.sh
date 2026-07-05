#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
backend_python="$repo_root/.venv/bin/python"
runtime_dir="${TMPDIR:-/tmp}/social-platform-transparency-dashboard-dev"
backend_pid_file="$runtime_dir/backend.pid"
frontend_pid_file="$runtime_dir/frontend.pid"

if [[ ! -x "$backend_python" ]]; then
  echo "Python virtualenv not found at $backend_python" >&2
  exit 1
fi

mkdir -p "$runtime_dir"

cleanup() {
  if [[ -f "$frontend_pid_file" ]]; then
    kill "$(cat "$frontend_pid_file")" 2>/dev/null || true
    rm -f "$frontend_pid_file"
  fi
  if [[ -f "$backend_pid_file" ]]; then
    kill "$(cat "$backend_pid_file")" 2>/dev/null || true
    rm -f "$backend_pid_file"
  fi
  rmdir "$runtime_dir" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

cd "$repo_root/backend"
"$backend_python" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
echo $! > "$backend_pid_file"

for _ in {1..60}; do
  if curl -fsS http://127.0.0.1:8000/health >/dev/null; then
    break
  fi
  sleep 1
done

curl -fsS -X POST http://127.0.0.1:8000/refresh >/dev/null

cd "$repo_root/frontend"
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev -- --hostname 0.0.0.0 --port 3000 &
echo $! > "$frontend_pid_file"

wait -n "$(cat "$backend_pid_file")" "$(cat "$frontend_pid_file")"