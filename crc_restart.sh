#!/bin/bash
set -e

cd "$(dirname "$0")"

bash crc_stop.sh
bash crc_start.sh
