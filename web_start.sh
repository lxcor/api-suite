#!/bin/bash
set -e

SESSION="web-sophia.lxcor.com"

cd "$(dirname "$0")"

if [ ! -d sandbox/venv ]; then
    echo "Creating sandbox venv..."
    python3 -m venv sandbox/venv
    (cd sandbox && venv/bin/pip install -q -r requirements.txt)
    echo "Done."
fi

if [ ! -f .env ]; then
    echo "Warning: .env not found — copy .env.example to .env and set DJANGO_DEBUG=1"
fi

tmux kill-session -t "$SESSION" 2>/dev/null || true

tmux new-session -d -s "$SESSION" -c "$(pwd)/sandbox" \
    "source venv/bin/activate && python manage.py runserver 0.0.0.0:8020"

echo "Started in tmux session '$SESSION' (attach: tmux attach -t $SESSION)"
