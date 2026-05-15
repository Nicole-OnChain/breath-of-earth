# 🍳 Kitchen — Daily Operations

_What to check, when, and how._

## Heartbeat Checks (2-4x/day)
- Portfolio value + 24h changes
- Weinstein stage transitions → alert Nicole
- Pruning immunity alerts (<25%)
- Ghost flag status
- Email (urgent only)
- Weather (if Nicole might go out)

## Active Cron Jobs
- HYPE under $35 alert (daily 2 PM ET)
- GOOGL under $350 check (daily)
- COIN under $180 check (daily)
- SMH pullback check (daily)
- CC monitor (every 4h)
- Scanner (every 2h)
- Git dev activity (every 6h)
- On-chain wallet tracker (every 4h)

## Dashboard
- **Public URL:** http://187.124.242.195:9090 (nicole/miacfo2026)
- **Server:** `scripts/dashboard-server.py` on port 8080
- **Caddy proxy:** port 9090 → 8080

## Biweekly Reallocation
- **1st and 15th of each month**
- Claim Root emissions + check subnet emissions + add DCA (~1τ)
- Redistribute by Weinstein stage
- Requires Nicole's explicit approval for every move