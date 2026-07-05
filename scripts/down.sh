#!/usr/bin/env bash

set -euo pipefail

runtime_dir="${TMPDIR:-/tmp}/social-platform-transparency-dashboard-dev"

stop_pid_file() {
  local pid_file="$1"
  if [[ -f "$pid_file" ]]; then
    kill "$(cat "$pid_file")" 2>/dev/null || true
    rm -f "$pid_file"
  fi
}

stop_pid_file "$runtime_dir/frontend.pid"
stop_pid_file "$runtime_dir/backend.pid"
rmdir "$runtime_dir" 2>/dev/null || true

if command -v docker >/dev/null 2>&1; then
  if docker compose version >/dev/null 2>&1; then
    (cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)" && docker compose down) || true
  elif command -v docker-compose >/dev/null 2>&1; then
    (cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)" && docker-compose down) || true
  fi
fi