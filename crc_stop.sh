#!/bin/bash
set -e

PROJECT=$(basename "$(cd "$(dirname "$0")" && pwd)")

# Must compute the session name exactly the same way crc_start.sh does --
# see its comment for why this lives in /etc/crc-environment.
CRC_ENV=$(cat /etc/crc-environment 2>/dev/null || echo "unlabeled")
SESSION="crc-$PROJECT-$CRC_ENV"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux kill-session -t "$SESSION"
    echo "Stopped CRC session: $SESSION"
else
    echo "No CRC session running for: $PROJECT ($SESSION)"
fi
