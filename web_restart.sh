#!/bin/bash
set -e

cd "$(dirname "$0")"

bash web_stop.sh
bash web_start.sh
