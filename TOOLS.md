# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## API Keys

### TAO Stats
- API Key: `tao-52f985f8-94c7-4963-82c1-d1e6876b5142:0b44ec02`
- Use for: Bittensor subnet data, emissions, validator APY, etc.
- Auth format: `Authorization: <key>` (NOT "Bearer")
- Base URL: `https://api.taostats.io`
- Management URL: `https://management-api.taostats.io`
- Free tier: 5 req/s, 10,000 credits/month
- Pool history endpoint returns price/mcap/MAs: `/api/dtao/pool/history/v1?netuid=X&frequency=by_day`
- Subnet endpoint returns flow/miners/validators: `/api/subnet/latest/v1`
- Pruning endpoint: `/api/subnet/pruning/latest/v1`
- pruning_rank: 1 = MOST at risk, 128 = SAFEST

### Bittensor Scanner
- Script: `/root/.openclaw/workspace/scripts/scanner_v3.py` (primary, rate-limit aware)
- Script: `/root/.openclaw/workspace/scripts/subnet_scanner.py` (v2, full features)
- Cache dir: `/root/.openclaw/workspace/memory/scanner_cache/`
- Output dir: `/root/.openclaw/workspace/memory/scanner_output/`
- Chart dir: `/root/.openclaw/workspace/memory/chart/`
- Cron: every 2 hours, fetches pool histories + scores
- Pool data cached for 24h, subnet/pruning data cached for 2h

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.
