#!/bin/bash
set -e

PROJECT=$(basename "$(cd "$(dirname "$0")" && pwd)")
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Per-machine differentiator (e.g. "prod" on Alaude, "dev" on Sophia) so the
# same project name on two different boxes shows up as two distinct, clearly
# labeled entries in the Claude app's remote-session picker instead of
# colliding. Lives in one place per machine, not per-project -- every
# project's crc_start.sh on this box picks it up the same way. If unset,
# falls back to "unlabeled" rather than silently matching a differently-
# labeled session with the same project name on another box.
CRC_ENV=$(cat /etc/crc-environment 2>/dev/null || echo "unlabeled")
SESSION="crc-$PROJECT-$CRC_ENV"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "CRC session already running: $SESSION"
    exit 0
fi

tmux new-session -d -s "$SESSION" -c "$PROJECT_DIR" "claude --remote-control $SESSION"

# Confirm the trust-this-folder prompt that appears on every fresh process start
for i in $(seq 1 30); do
    sleep 1
    if tmux capture-pane -t "$SESSION" -p 2>/dev/null | grep -q "Yes, I trust this folder"; then
        # Newer Claude Code versions default the cursor to "No, exit" -- move to
        # "Yes" before confirming, or Enter quits the session.
        if ! tmux capture-pane -t "$SESSION" -p | grep -q "❯ Yes, I trust this folder"; then
            tmux send-keys -t "$SESSION" Down
            sleep 0.5
        fi
        tmux send-keys -t "$SESSION" Enter
        break
    fi
done

echo "Started CRC in tmux session '$SESSION' (attach: tmux attach -t $SESSION)"
