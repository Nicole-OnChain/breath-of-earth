# 📚 Library — Bittensor Research

_Subnet data, scanner results, dev activity._

## Scanner
- **Script:** `scripts/scanner_v3.py` (primary, rate-limit aware)
- **Cache:** `memory/scanner_cache/` (pool 24h, subnet/pruning 2h)
- **Output:** `memory/scanner_output/`
- **Cron:** Every 2 hours

## Git Dev Activity
- **Script:** `scripts/git_crawl_scanner.py`
- **Venv:** `.venv/bin/python3`
- **Output:** `data/git-crawl/`
- **Cron:** Every 6 hours
- **Covers:** SN0, 8, 13, 44, 51, 68, 74, 93 (portfolio) + SN64, 120 (watchlist)

## Key Findings (as of 2026-05-08)
- **lium.io (SN51):** #1 position, real DEV 27/wk MODERATE, flow positive
- **Vanta (SN8):** DEV=42 HIGH (elite), 23 repos active, flow positive
- **NOVA (SN68):** ADVANCING, DEV 16.8/wk MODERATE, +2.3% above 30WMA
- **Data Universe (SN13):** Stage 3 ⚠️, -7.3% below 150WMA, watch for exit
- **Score (SN44):** Extended +53% above 150WMA, don't add
- **Gittensor (SN74):** DEV 105/wk ELITE but +28.5% above 30WMA, reduced position

## Exited Subnets — Why
- **SN93 Bitcast:** DEV dead (4.7/wk), price -9.2% below 30WMA, declining
- **SN11 TrajectoryRL:** DEV=10, 30d flow -13%
- **SN1 Apex:** DEV=12, aGap=43 lowest