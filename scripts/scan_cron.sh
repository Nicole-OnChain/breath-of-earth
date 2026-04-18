#!/bin/bash
# Mia's Subnet Scanner - Cron wrapper
# Runs v3 scanner with score-only if fresh data exists, 
# or fetches new data if cache is stale
# Outputs to log file

SCRIPT="/root/.openclaw/workspace/scripts/scanner_v3.py"
LOG="/root/.openclaw/workspace/memory/scanner_output/cron.log"
WORKDIR="/root/.openclaw/workspace"

echo "=== Cron scan: $(date -u '+%Y-%m-%d %H:%M UTC') ===" >> "$LOG"

cd "$WORKDIR"
python3 "$SCRIPT" --top 20 --export json >> "$LOG" 2>&1

echo "=== Done: $(date -u '+%Y-%m-%d %H:%M UTC') ===" >> "$LOG"
echo "" >> "$LOG"