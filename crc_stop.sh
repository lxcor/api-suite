#!/bin/bash
set -e

PROJECT=$(basename "$(cd "$(dirname "$0")" && pwd)")
SESSION="crc-$PROJECT"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux kill-session -t "$SESSION"
    echo "Stopped CRC session: $SESSION"
else
    echo "No CRC session running for: $PROJECT"
fi
