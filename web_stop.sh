#!/bin/bash
set -e

SESSION="web-api-suite"

cd "$(dirname "$0")"

tmux kill-session -t "$SESSION" 2>/dev/null && echo "Stopped '$SESSION'" || echo "Session '$SESSION' was not running"
