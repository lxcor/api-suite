#!/bin/bash
set -e

PROJECT=$(basename "$(cd "$(dirname "$0")" && pwd)")
SESSION="crc-$PROJECT"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "CRC session already running: $SESSION"
    exit 0
fi

tmux new-session -d -s "$SESSION" -c "$PROJECT_DIR" "claude --remote-control $SESSION"

# Confirm the trust-this-folder prompt that appears on every fresh process start
for i in $(seq 1 30); do
    sleep 1
    if tmux capture-pane -t "$SESSION" -p 2>/dev/null | grep -q "Yes, I trust this folder"; then
        tmux send-keys -t "$SESSION" "" Enter
        break
    fi
done

echo "Started CRC in tmux session '$SESSION' (attach: tmux attach -t $SESSION)"
