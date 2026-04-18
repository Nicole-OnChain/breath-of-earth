#!/usr/bin/env python3
"""
Mia's Bittensor Subnet Scanner — Scoring Framework v2
Weinstein Stage Analysis + VirtualBacon Crypto Methodology
Adapted for Bittensor dTAO Alpha Token AMM ecosystem

Data sources:
  - /api/subnet/latest/v1 → flow, miners, validators, difficulty, emission, fees, recycling
  - /api/dtao/pool/history/v1?netuid=X&frequency=by_day → price, mcap, MAs, total_tao, staking ratio
  - /api/subnet/pruning/latest/v1 → pruning rank, immunity

Usage:
  python3 subnet_scanner.py              # Full scan
  python3 subnet_scanner.py --quick      # Quick scan (subnet data + cached pool)
  python3 subnet_scanner.py --top 10     # Top 10
  python3 subnet_scanner.py --netuid 8   # Deep dive
  python3 subnet_scanner.py --chart 8    # Chart for subnet 8
  python3 subnet_scanner.py --export csv # Export CSV
"""

import requests
import json
import time
import sys
import os
import argparse
from datetime import datetime, timezone
from pathlib import Path

# --- Config ---
API_KEY = os.environ.get("TAOSTATS_API_KEY", "tao-52f985f8-94c7-4963-82c1-d1e6876b5142:0b44ec02")
BASE_URL = "https://api.taostats.io"
HEADERS = {"Authorization": API_KEY, "Accept": "application/json"}
CACHE_DIR = Path("/root/.openclaw/workspace/memory/scanner_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR = Path("/root/.openclaw/workspace/memory/scanner_output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR = Path("/root/.openclaw/workspace/memory/chart")
CHART_DIR.mkdir(parents=True, exist_ok=True)
SUBNET_NAMES_FILE = Path("/root/.openclaw/workspace/memory/subnet_names.json")

REQUEST_INTERVAL = 0.35  # ~3 req/s, safe margin
RETRY_INTERVAL = 3.0  # wait longer on 429s
POOL_INTERVAL = 3.0  # 3s between pool history calls (heavy endpoint)
POOL_MAX_PAGES = 2  # 200 entries ~ 200 days, enough for 150d MA
BATCH_SIZE = 20  # subnets per batch, with longer pause between batches
BATCH_PAUSE = 30  # seconds between batches


def api_get(endpoint, params=None, max_pages=None):
    """Paginated TAO Stats API request."""
    url = f"{BASE_URL}{endpoint}"
    all_data = []
    page = 1
    while True:
        p = (params or {}).copy()
        p["page"] = page
        p["limit"] = 100
        retries = 5
        while retries > 0:
            try:
                resp = requests.get(url, headers=HEADERS, params=p, timeout=30)
                if resp.status_code == 429:
                    wait = RETRY_INTERVAL * (6 - retries) * 1.5
                    print(f"  Rate limited, waiting {wait:.1f}s... (retries left: {retries-1})", file=sys.stderr)
                    time.sleep(wait)
                    retries -= 1
                    continue
                resp.raise_for_status()
                body = resp.json()
                break
            except Exception as e:
                print(f"  API error {endpoint} p{page}: {e}", file=sys.stderr)
                break
        else:
            print(f"  Giving up on {endpoint} p{page} after retries", file=sys.stderr)
            break
        data = body.get("data", [])
        if not data:
            break
        all_data.extend(data)
        pagination = body.get("pagination", {})
        total_pages = pagination.get("total_pages", 1)
        if page >= total_pages:
            break
        if max_pages and page >= max_pages:
            break
        page += 1
        time.sleep(REQUEST_INTERVAL)
    return all_data


def safe_float(val, default=0.0):
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def safe_int(val, default=0):
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


# ============================================================
# SCORING FUNCTIONS (each returns 0-100)
# ============================================================

def score_a1(pct_above_ma150):
    """Price vs. 150-day MA"""
    if pct_above_ma150 > 10: return 100
    elif pct_above_ma150 > 0: return 70
    elif pct_above_ma150 > -5: return 40
    elif pct_above_ma150 > -15: return 20
    else: return 0

def score_a2(ma50_above, ma150_slope, ma50_slope):
    """50d vs 150d MA alignment"""
    if ma50_above and ma150_slope > 0 and ma50_slope > 0: return 100
    elif ma50_above and ma150_slope >= 0: return 70
    elif ma50_above and ma150_slope < 0: return 60
    elif not ma50_above and ma50_slope > 0: return 40
    elif not ma50_above and ma150_slope < 0: return 0
    else: return 20

def score_a3(higher_highs, higher_lows):
    """30-day price pattern"""
    if higher_highs and higher_lows: return 100
    elif higher_highs: return 70
    elif higher_lows: return 50
    else: return 30  # flat or lower

def score_a4(position_in_range):
    """Breakout signal — position in recent range (0=low, 1=high)"""
    if position_in_range > 0.95: return 100
    elif position_in_range > 0.85: return 60
    elif position_in_range > 0.4: return 30
    elif position_in_range > 0.15: return 10
    else: return 0

def score_a5(slope_pct_month):
    """150-day MA slope (% per month)"""
    if slope_pct_month > 2: return 100
    elif slope_pct_month > 0: return 70
    elif slope_pct_month > -0.5: return 30
    elif slope_pct_month > -2: return 10
    else: return 0

def score_flow(pct_of_mcap):
    """Generic flow score (% of market cap)"""
    if pct_of_mcap > 0.5: return 100
    elif pct_of_mcap > 0.1: return 70
    elif pct_of_mcap > 0: return 40
    elif pct_of_mcap > -0.1: return 20
    else: return 0

def score_b4(tao_flow_val):
    """Tao flow direction"""
    if tao_flow_val is None: return 40
    if tao_flow_val > 100: return 100
    elif tao_flow_val > 10: return 70
    elif tao_flow_val > 0: return 50
    elif tao_flow_val > -10: return 30
    elif tao_flow_val > -100: return 20
    else: return 0

def score_b5(recycling, recycling_prev=None):
    """Recycling score"""
    if recycling is None or recycling == 0: return 20
    if recycling_prev is not None and recycling > recycling_prev: return 100
    elif recycling > 0: return 50
    else: return 20

def score_c1(miners):
    if miners > 50: return 100
    elif miners > 30: return 80
    elif miners > 15: return 60
    elif miners > 5: return 30
    else: return 10

def score_c2(growth_pct):
    if growth_pct > 10: return 100
    elif growth_pct > 0: return 70
    elif growth_pct > -2: return 40
    elif growth_pct > -10: return 20
    else: return 0

def score_c3(validators):
    if validators > 10: return 100
    elif validators > 5: return 70
    elif validators > 2: return 40
    elif validators == 1: return 10
    else: return 0

def score_c4(util):
    """Capacity utilization (0-1)"""
    if util > 0.8: return 100
    elif util > 0.5: return 70
    elif util > 0.3: return 40
    elif util > 0.1: return 20
    else: return 5

def score_c5(diff_change_pct):
    if diff_change_pct > 10: return 100
    elif diff_change_pct > 0: return 70
    elif diff_change_pct > -5: return 40
    else: return 10

def score_d_percentile(pct):
    if pct > 0.75: return 100
    elif pct > 0.50: return 70
    elif pct > 0.25: return 40
    else: return 10

def score_d3_fee(pct):
    """Fee rate — LOW fees good, so invert"""
    inv = 1.0 - pct
    if inv > 0.75: return 100
    elif inv > 0.50: return 70
    elif inv > 0.25: return 40
    else: return 10

def score_d4(ratio):
    if ratio > 0.8: return 100
    elif ratio > 0.6: return 70
    elif ratio > 0.4: return 40
    elif ratio > 0.2: return 20
    else: return 5

def score_d5(root_prop):
    if root_prop > 0.5: return 100
    elif root_prop > 0.25: return 70
    elif root_prop > 0.10: return 40
    elif root_prop > 0.05: return 20
    else: return 5

def score_e1(pruning_rank, total=129):
    # pruning_rank: 1 = lowest moving_price = MOST at risk, total = safest
    if pruning_rank is None: return 50
    safe_pct = pruning_rank / total if total > 0 else 0
    if safe_pct > 0.75: return 100
    elif safe_pct > 0.40: return 70
    elif safe_pct > 0.15: return 40
    elif safe_pct > 0.08: return 20
    else: return 0

def score_e2(immunity_pct):
    if immunity_pct is None: return 0
    if immunity_pct > 0.75: return 100
    elif immunity_pct > 0.50: return 70
    elif immunity_pct > 0.25: return 40
    elif immunity_pct > 0: return 10
    else: return 0

def score_e3(pct):
    """Registration cost — HIGH cost = HIGH demand = good"""
    if pct > 0.75: return 100
    elif pct > 0.50: return 70
    elif pct > 0.25: return 40
    else: return 10

def score_e4(enabled):
    return 100 if enabled else 20


# ============================================================
# ANALYSIS
# ============================================================

def calculate_moving_averages(prices, short=50, long=150):
    """Calculate MAs from price list (oldest first)."""
    n = len(prices)
    if n < long:
        return None, None, None, None
    ma_short = sum(prices[-short:]) / short
    ma_long = sum(prices[-long:]) / long
    # 10-day-ago MAs for slope
    slope_offset = 10
    if n > long + slope_offset:
        prev_ma_short = sum(prices[-(short + slope_offset):-slope_offset]) / short
        prev_ma_long = sum(prices[-(long + slope_offset):-slope_offset]) / long
    else:
        prev_ma_short = ma_short
        prev_ma_long = ma_long
    return ma_short, ma_long, prev_ma_short, prev_ma_long


def analyze_price_pattern(prices_30d):
    """Analyze higher highs / higher lows from price list."""
    n = len(prices_30d)
    if n < 10:
        return False, False, 0.5

    third = n // 3
    chunks = [prices_30d[:third], prices_30d[third:2*third], prices_30d[2*third:]]

    highs = [max(c) for c in chunks if c]
    lows = [min(c) for c in chunks if c]

    higher_highs = len(highs) >= 3 and highs[2] > highs[1] >= highs[0]
    higher_lows = len(lows) >= 3 and lows[2] > lows[1] >= lows[0]

    # Also accept: 2 of 3 trending up
    if len(highs) >= 3:
        if highs[1] > highs[0] and highs[2] >= highs[1]:
            higher_highs = True
        if highs[2] > highs[1]:
            higher_highs = True
    if len(lows) >= 3:
        if lows[1] > lows[0] and lows[2] >= lows[1]:
            higher_lows = True
        if lows[2] > lows[1]:
            higher_lows = True

    # Lower lows override
    if len(lows) >= 3 and lows[2] < lows[1] < lows[0]:
        higher_lows = False
    if len(highs) >= 3 and highs[2] < highs[1] < highs[0]:
        higher_highs = False

    # Position in range
    current = prices_30d[-1]
    range_lo = min(prices_30d)
    range_hi = max(prices_30d)
    span = range_hi - range_lo
    position = (current - range_lo) / span if span > 0 else 0.5

    return higher_highs, higher_lows, position


def compute_subnet_score(subnet_data, pool_latest, pool_history, pruning_info,
                          emission_pct, fee_pct, reg_cost_pct):
    """Score a single subnet. Returns dict with all categories and composite."""

    netuid = safe_int(subnet_data.get("netuid"), -1)
    name = pool_latest.get("name", "") or f"Subnet {netuid}"
    symbol = pool_latest.get("symbol", "")

    # --- Extract subnet-level data ---
    net_flow_1d = safe_float(subnet_data.get("net_flow_1_day"))
    net_flow_7d = safe_float(subnet_data.get("net_flow_7_days"))
    net_flow_30d = safe_float(subnet_data.get("net_flow_30_days"))
    tao_flow_raw = safe_float(subnet_data.get("tao_flow"))
    recycling_24h = safe_float(subnet_data.get("recycled_24_hours"))
    active_miners = safe_int(subnet_data.get("active_keys"))  # active_keys = total active
    miners_only = safe_int(subnet_data.get("active_miners"))
    active_validators = safe_int(subnet_data.get("active_validators"))
    max_neurons = safe_int(subnet_data.get("max_neurons"), 1)
    difficulty = safe_float(subnet_data.get("difficulty"))
    max_difficulty = safe_float(subnet_data.get("max_difficulty"), 1)
    emission = safe_float(subnet_data.get("emission"))
    projected_emission = safe_float(subnet_data.get("projected_emission"))
    fee_rate = safe_float(subnet_data.get("fee_rate"))
    subtoken_enabled = subnet_data.get("subtoken_enabled", False)
    recycled_lifetime = safe_float(subnet_data.get("recycled_lifetime"))
    immunity_period_blocks = safe_int(subnet_data.get("immunity_period"))

    # --- Extract pool-level data ---
    price = safe_float(pool_latest.get("price"))
    market_cap = safe_float(pool_latest.get("market_cap"))
    total_tao = safe_float(pool_latest.get("total_tao"))
    total_alpha = safe_float(pool_latest.get("total_alpha"), 1)
    alpha_in_pool = safe_float(pool_latest.get("alpha_in_pool"))
    alpha_staked = safe_float(pool_latest.get("alpha_staked"))
    root_prop = safe_float(pool_latest.get("root_prop"))
    rank = safe_int(pool_latest.get("rank"))
    liquidity = safe_float(pool_latest.get("liquidity"))

    # ========== CATEGORY A: PRICE TREND & STAGE ==========
    a1 = a2 = a3 = a4 = a5 = 0
    price_vs_ma150_pct = 0
    ma150_slope = 0
    stage_label = "Unknown"

    if pool_history and len(pool_history) >= 50:
        # Sort by timestamp, extract prices
        price_series = []
        for entry in pool_history:
            ts = safe_float(entry.get("timestamp"))
            p = safe_float(entry.get("price"))
            # Convert ISO timestamp to unix if needed
            if ts == 0 and entry.get("timestamp"):
                try:
                    from datetime import datetime as dt
                    ts_str = entry["timestamp"].replace("Z", "+00:00")
                    ts = dt.fromisoformat(ts_str).timestamp()
                except:
                    continue
            if ts > 0 and p > 0:
                price_series.append((ts, p))
        price_series.sort(key=lambda x: x[0])
        price_list = [p[1] for p in price_series]

        current_price = price_list[-1] if price_list else price

        if len(price_list) >= 150:
            ma_short, ma_long, prev_ma_short, prev_ma_long = calculate_moving_averages(price_list)
        elif len(price_list) >= 50:
            ma_short = sum(price_list[-50:]) / 50
            ma_long = None
            prev_ma_short = ma_short
            prev_ma_long = 0
        else:
            ma_short = ma_long = None
            prev_ma_short = prev_ma_long = None

        # A1: Price vs. 150d MA
        if ma_long and ma_long > 0:
            price_vs_ma150_pct = ((current_price - ma_long) / ma_long) * 100
            a1 = score_a1(price_vs_ma150_pct)
        else:
            a1 = 40  # insufficient data

        # A2: 50d vs 150d MA
        if ma_short is not None and ma_long is not None:
            ma50_above = ma_short > ma_long
            if prev_ma_long > 0:
                ma150_slope = ((ma_long - prev_ma_long) / prev_ma_long) * 100 * 3
            else:
                ma150_slope = 0
            ma50_slope = ((ma_short - prev_ma_short) / prev_ma_short) * 100 * 3 if prev_ma_short > 0 else 0
            a2 = score_a2(ma50_above, ma150_slope, ma50_slope)
        else:
            a2 = 40

        # A3: 30d pattern
        recent_30 = price_list[-30:] if len(price_list) >= 30 else price_list
        hh, hl, pos = analyze_price_pattern(recent_30)
        a3 = score_a3(hh, hl)

        # A4: Breakout
        a4 = score_a4(pos)

        # A5: MA slope
        a5 = score_a5(ma150_slope)

        # Stage label
        cat_a_raw = a1*0.25 + a2*0.25 + a3*0.20 + a4*0.15 + a5*0.15
        if cat_a_raw >= 70: stage_label = "Stage 2 📈"
        elif cat_a_raw >= 40: stage_label = "Stage 1 ➡️"
        elif cat_a_raw >= 20: stage_label = "Stage 3 ⚠️"
        else: stage_label = "Stage 4 🔻"
    else:
        a1 = a2 = a3 = a4 = a5 = 30
        stage_label = "No Data ❓"

    cat_a = a1*0.25 + a2*0.25 + a3*0.20 + a4*0.15 + a5*0.15

    # ========== CATEGORY B: FLOW CONFIRMATION ==========
    flow_1d_pct = (net_flow_1d / market_cap * 100) if market_cap > 0 else 0
    flow_7d_pct = (net_flow_7d / market_cap * 100) if market_cap > 0 else 0
    flow_30d_pct = (net_flow_30d / market_cap * 100) if market_cap > 0 else 0

    b1 = score_flow(flow_1d_pct)
    b2 = score_flow(flow_7d_pct)
    b3 = score_flow(flow_30d_pct)
    # Normalize tao_flow (raw values are in rau, 1e-9 TAO roughly)
    tao_flow_normalized = tao_flow_raw / 1e12 if abs(tao_flow_raw) > 1e9 else tao_flow_raw
    b4 = score_b4(tao_flow_normalized)
    b5 = score_b5(recycling_24h)

    cat_b = b1*0.15 + b2*0.25 + b3*0.35 + b4*0.15 + b5*0.10

    # ========== CATEGORY C: NETWORK ACTIVITY ==========
    c1 = score_c1(active_miners)
    # Miner growth proxy: if net flow positive, miners likely growing
    miner_growth_proxy = flow_7d_pct * 2
    c2 = score_c2(miner_growth_proxy)
    c3 = score_c3(active_validators)
    capacity_util = active_miners / max_neurons if max_neurons > 0 else 0
    c4 = score_c4(capacity_util)
    diff_ratio = difficulty / max_difficulty if max_difficulty > 0 else 0
    c5 = score_c5(diff_ratio * 50)

    cat_c = c1*0.20 + c2*0.25 + c3*0.15 + c4*0.25 + c5*0.15

    # ========== CATEGORY D: EMISSIONS & YIELD ==========
    d1 = score_d_percentile(emission_pct)
    d2 = score_d_percentile(emission_pct)  # projected ≈ current for now
    d3 = score_d3_fee(fee_pct)
    staking_ratio = alpha_staked / total_alpha if total_alpha > 0 else 0
    d4 = score_d4(staking_ratio)
    d5 = score_d5(root_prop)

    cat_d = d1*0.25 + d2*0.25 + d3*0.15 + d4*0.20 + d5*0.15

    # ========== CATEGORY E: SURVIVAL & RISK ==========
    p_info = pruning_info.get(netuid, {})
    pruning_rank = p_info.get("pruning_rank")
    immunity_pct = p_info.get("immunity_pct")

    e1 = score_e1(pruning_rank)
    e2 = score_e2(immunity_pct)
    e3 = score_e3(reg_cost_pct)
    e4 = score_e4(subtoken_enabled)

    cat_e = e1*0.35 + e2*0.25 + e3*0.25 + e4*0.15

    # ========== COMPOSITE ==========
    composite = cat_a*0.35 + cat_b*0.25 + cat_c*0.20 + cat_d*0.10 + cat_e*0.10

    if composite >= 80: signal = "🟢 STRONG BUY"
    elif composite >= 60: signal = "🟡 WATCHLIST"
    elif composite >= 40: signal = "⚪ NEUTRAL"
    elif composite >= 20: signal = "🟠 WARNING"
    else: signal = "🔴 DANGER"

    low_liquidity = total_tao < 1e12  # < ~1,000 TAO in pool (values in RAO: 1 TAO = 1e9 RAO, but actuals seem ~1e12 scale)

    return {
        "netuid": netuid, "name": name, "symbol": symbol,
        "price": price, "market_cap": market_cap, "total_tao": total_tao,
        "rank": rank, "stage": stage_label,
        "cat_a": round(cat_a, 1), "cat_b": round(cat_b, 1),
        "cat_c": round(cat_c, 1), "cat_d": round(cat_d, 1),
        "cat_e": round(cat_e, 1), "composite": round(composite, 1),
        "signal": signal, "low_liquidity": low_liquidity,
        "detail": {
            "a1": round(a1), "a2": round(a2), "a3": round(a3),
            "a4": round(a4), "a5": round(a5),
            "b1": round(b1), "b2": round(b2), "b3": round(b3),
            "b4": round(b4), "b5": round(b5),
            "c1": round(c1), "c2": round(c2), "c3": round(c3),
            "c4": round(c4), "c5": round(c5),
            "d1": round(d1), "d2": round(d2), "d3": round(d3),
            "d4": round(d4), "d5": round(d5),
            "e1": round(e1), "e2": round(e2), "e3": round(e3), "e4": round(e4),
            "price_vs_ma150": round(price_vs_ma150_pct, 2),
            "ma150_slope": round(ma150_slope, 2),
            "flow_1d_pct": round(flow_1d_pct, 4),
            "flow_7d_pct": round(flow_7d_pct, 4),
            "flow_30d_pct": round(flow_30d_pct, 4),
            "active_miners": active_miners, "active_validators": active_validators,
            "capacity_util": round(capacity_util*100, 1),
            "staking_ratio": round(staking_ratio*100, 1),
            "pruning_rank": pruning_rank,
            "root_prop": round(root_prop, 4),
        }
    }


def compute_percentile_ranks(items, field):
    """Rank items by field value, return {id: percentile}."""
    vals = [(i, safe_float(v)) for i, v in enumerate(items) if safe_float(v) != 0]
    if not vals:
        return {}
    vals.sort(key=lambda x: x[1])
    n = len(vals)
    return {items[i].get("netuid", i): (rank+1)/n for rank, (i, _) in enumerate(vals)}


def build_pruning_map(pruning_data):
    pmap = {}
    for entry in pruning_data:
        netuid = safe_int(entry.get("netuid"), -1)
        if netuid < 0: continue
        rank = safe_int(entry.get("pruning_rank"))
        is_immune = entry.get("is_immune", False)
        immunity_blocks = safe_int(entry.get("immunity_blocks_remaining"), 0)
        total_immunity = safe_int(entry.get("immunity_period"))
        if total_immunity is None or total_immunity == 0:
            # Use a default if not provided
            total_immunity = 4096  # common default
        immunity_pct = immunity_blocks / total_immunity if is_immune and total_immunity > 0 else 0
        pmap[netuid] = {"pruning_rank": rank, "immunity_pct": immunity_pct, "is_immune": is_immune}
    return pmap


def ascii_bar(score, width=20):
    filled = int(score / 100 * width)
    empty = width - filled
    if score >= 80: ch = "█"
    elif score >= 60: ch = "▓"
    elif score >= 40: ch = "▒"
    elif score >= 20: ch = "░"
    else: ch = "·"
    return ch * filled + "░" * empty


def format_table(results, top_n=None):
    items = results[:top_n] if top_n else results
    lines = []
    lines.append(f"{'#':<4} {'UID':<5} {'Name':<25} {'Price':<10} {'Stage':<14} {'A':>5} {'B':>5} {'C':>5} {'D':>5} {'E':>5} {'Score':>7} {'Signal'}")
    lines.append("─" * 115)
    for i, r in enumerate(items):
        nm = r['name'][:23] if r['name'] else f"Subnet {r['netuid']}"
        liq = " ⚠" if r['low_liquidity'] else ""
        price_str = f"{r['price']:.4f}" if r['price'] > 0 else "N/A"
        lines.append(
            f"{i+1:<4} {r['netuid']:<5} {nm:<25}{liq} {price_str:<10} {r['stage']:<14} "
            f"{r['cat_a']:>5.1f} {r['cat_b']:>5.1f} {r['cat_c']:>5.1f} "
            f"{r['cat_d']:>5.1f} {r['cat_e']:>5.1f} {r['composite']:>6.1f}% {r['signal']}"
        )
    return "\n".join(lines)


def format_detail(r):
    d = r['detail']
    lines = [
        "═" * 55,
        f"  SUBNET {r['netuid']}: {r['name']} ({r['symbol']})",
        f"  COMPOSITE: {r['composite']}% {r['signal']}",
        f"  STAGE: {r['stage']}   Rank: #{r.get('rank', 'N/A')}",
    ]
    if r['low_liquidity']:
        lines.append("  ⚠️ LOW LIQUIDITY — price signals unreliable")
    lines.append("═" * 55)
    lines.append(f"")
    lines.append(f"  A — PRICE TREND & STAGE  [{r['cat_a']}%]  {ascii_bar(r['cat_a'])}")
    lines.append(f"    A1. Price vs 150d MA:    {d['a1']:>3}  ({d['price_vs_ma150']:+.1f}%)")
    lines.append(f"    A2. 50d vs 150d MA:      {d['a2']:>3}")
    lines.append(f"    A3. 30d Pattern:         {d['a3']:>3}")
    lines.append(f"    A4. Breakout Signal:     {d['a4']:>3}")
    lines.append(f"    A5. 150d MA Slope:       {d['a5']:>3}  ({d['ma150_slope']:.2f}%/mo)")
    lines.append(f"")
    lines.append(f"  B — FLOW CONFIRMATION     [{r['cat_b']}%]  {ascii_bar(r['cat_b'])}")
    lines.append(f"    B1. Net Flow 1d:         {d['b1']:>3}  ({d['flow_1d_pct']:+.3f}%)")
    lines.append(f"    B2. Net Flow 7d:         {d['b2']:>3}  ({d['flow_7d_pct']:+.3f}%)")
    lines.append(f"    B3. Net Flow 30d:        {d['b3']:>3}  ({d['flow_30d_pct']:+.3f}%)")
    lines.append(f"    B4. Tao Flow:            {d['b4']:>3}")
    lines.append(f"    B5. Recycling:           {d['b5']:>3}")
    lines.append(f"")
    lines.append(f"  C — NETWORK ACTIVITY      [{r['cat_c']}%]  {ascii_bar(r['cat_c'])}")
    lines.append(f"    C1. Active Miners:       {d['c1']:>3}  ({d['active_miners']})")
    lines.append(f"    C2. Miner Growth:        {d['c2']:>3}")
    lines.append(f"    C3. Active Validators:   {d['c3']:>3}  ({d['active_validators']})")
    lines.append(f"    C4. Capacity Util:       {d['c4']:>3}  ({d['capacity_util']}%)")
    lines.append(f"    C5. Difficulty:          {d['c5']:>3}")
    lines.append(f"")
    lines.append(f"  D — EMISSIONS & YIELD     [{r['cat_d']}%]  {ascii_bar(r['cat_d'])}")
    lines.append(f"    D1. Emission Rank:       {d['d1']:>3}")
    lines.append(f"    D2. Proj Emission:       {d['d2']:>3}")
    lines.append(f"    D3. Fee Rate Rank:       {d['d3']:>3}")
    lines.append(f"    D4. Staking Ratio:       {d['d4']:>3}  ({d['staking_ratio']}%)")
    lines.append(f"    D5. Root Proportion:     {d['d5']:>3}  ({d['root_prop']})")
    lines.append(f"")
    lines.append(f"  E — SURVIVAL & RISK       [{r['cat_e']}%]  {ascii_bar(r['cat_e'])}")
    lines.append(f"    E1. Pruning Rank:        {d['e1']:>3}  (rank: {d.get('pruning_rank', 'N/A')})")
    lines.append(f"    E2. Immunity:            {d['e2']:>3}")
    lines.append(f"    E3. Reg Cost Rank:       {d['e3']:>3}")
    lines.append(f"    E4. Subtoken Enabled:    {d['e4']:>3}")
    lines.append(f"")
    lines.append(f"═" * 55)
    return "\n".join(lines)


def generate_chart(netuid, pool_history, result=None):
    """Generate matplotlib price chart."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except ImportError:
        print("  matplotlib not available")
        return None

    if not pool_history or len(pool_history) < 10:
        return None

    # Parse
    entries = []
    for e in pool_history:
        ts_str = e.get("timestamp", "")
        p = safe_float(e.get("price"))
        if ts_str and p > 0:
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                entries.append((ts, p))
            except:
                continue

    if len(entries) < 10:
        return None

    entries.sort(key=lambda x: x[0])
    dates = [e[0] for e in entries]
    prices = [e[1] for e in entries]

    # MAs
    ma50_vals = []
    ma150_vals = []
    for i in range(len(prices)):
        if i >= 49:
            ma50_vals.append(sum(prices[i-49:i+1]) / 50)
        else:
            ma50_vals.append(None)
        if i >= 149:
            ma150_vals.append(sum(prices[i-149:i+1]) / 150)
        else:
            ma150_vals.append(None)

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(dates, prices, color='#00D4AA', linewidth=1.5, label='Alpha Price')
    valid_ma50 = [(d, v) for d, v in zip(dates, ma50_vals) if v is not None]
    if valid_ma50:
        ax.plot([d for d, _ in valid_ma50], [v for _, v in valid_ma50],
                color='#FFA500', linewidth=1, linestyle='--', label='50-day MA')
    valid_ma150 = [(d, v) for d, v in zip(dates, ma150_vals) if v is not None]
    if valid_ma150:
        ax.plot([d for d, _ in valid_ma150], [v for _, v in valid_ma150],
                color='#FF4444', linewidth=1, linestyle='-', label='150-day MA')

    ax.set_facecolor('#1a1a2e')
    fig.set_facecolor('#1a1a2e')
    ax.tick_params(colors='white')
    for spine in ax.spines.values():
        spine.set_color('#333')
    ax.title.set_color('white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')

    name = result['name'] if result else f"Subnet {netuid}"
    score = result['composite'] if result else 0
    signal = result['signal'] if result else ""
    ax.set_title(f"{name} (UID {netuid}) — {score}% {signal}", fontsize=14, fontweight='bold')
    ax.set_ylabel("Price (TAO)")
    ax.legend(loc='upper left', facecolor='#2a2a4e', edgecolor='#444', labelcolor='white')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax.grid(True, alpha=0.2, color='#555')
    plt.tight_layout()

    path = CHART_DIR / f"subnet_{netuid}_chart.png"
    plt.savefig(path, dpi=150, facecolor='#1a1a2e')
    plt.close()
    return str(path)


def run_scan(quick=False, top_n=None, netuid_filter=None, chart_netuid=None, export=None):
    print(f"🚀 Mia's Subnet Scanner v2 — {'Quick' if quick else 'Full'} Scan")
    print(f"   {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n")

    # 1. Subnet data
    print("📡 Fetching subnet data...")
    subnets = api_get("/api/subnet/latest/v1")
    print(f"  Got {len(subnets)} subnets")

    # 2. Pruning data
    print("📡 Fetching pruning data...")
    pruning_raw = api_get("/api/subnet/pruning/latest/v1")
    pruning_map = build_pruning_map(pruning_raw)
    print(f"  Got {len(pruning_raw)} pruning records")

    # 3. Pool histories
    pool_histories = {}
    pool_latest = {}  # netuid -> latest pool entry (for price, mcap, etc.)

    if not quick:
        netuids = [safe_int(s.get("netuid")) for s in subnets if safe_int(s.get("netuid")) >= 0]
        if netuid_filter is not None:
            netuids = [n for n in netuids if n == netuid_filter]
        print(f"📡 Fetching pool history for {len(netuids)} subnets (batches of {BATCH_SIZE})...")
        for batch_start in range(0, len(netuids), BATCH_SIZE):
            batch = netuids[batch_start:batch_start + BATCH_SIZE]
            if batch_start > 0:
                print(f"  ⏳ Batch pause ({BATCH_PAUSE}s)...")
                time.sleep(BATCH_PAUSE)
            for i, netuid in enumerate(batch):
                global_i = batch_start + i
                if global_i > 0 and global_i % 5 == 0:
                    print(f"  Progress: {global_i}/{len(netuids)} subnets...")
                data = api_get("/api/dtao/pool/history/v1", params={"netuid": netuid, "frequency": "by_day"}, max_pages=POOL_MAX_PAGES)
                if data:
                    pool_histories[netuid] = data
                    pool_latest[netuid] = data[0]  # first entry = most recent
                time.sleep(POOL_INTERVAL)
        print(f"  Got history for {len(pool_histories)} subnets")
    else:
        # Load cached
        cache_file = CACHE_DIR / "pool_cache.json"
        if cache_file.exists():
            with open(cache_file) as f:
                cached = json.load(f)
            for k, v in cached.items():
                nuid = int(k)
                pool_histories[nuid] = v
                if v:
                    pool_latest[nuid] = v[0]
            print(f"📦 Loaded {len(pool_histories)} cached pool histories")
        else:
            print("⚠️ No cached pool data — run a full scan first")

    # 4. Percentile ranks
    emission_pct = compute_percentile_ranks(subnets, "emission")
    fee_pct = compute_percentile_ranks(subnets, "fee_rate")
    reg_cost_pct = compute_percentile_ranks(subnets, "neuron_registration_cost")

    # 5. Score all subnets
    print("🧮 Scoring subnets...")
    results = []
    for subnet in subnets:
        netuid = safe_int(subnet.get("netuid"), -1)
        if netuid < 0: continue
        if netuid_filter is not None and netuid != netuid_filter: continue

        hist = pool_histories.get(netuid, [])
        latest = pool_latest.get(netuid, {})
        p_info = pruning_map.get(netuid, {})

        result = compute_subnet_score(
            subnet, latest, hist, p_info,
            emission_pct.get(netuid, 0.5),
            fee_pct.get(netuid, 0.5),
            reg_cost_pct.get(netuid, 0.5)
        )
        results.append(result)

    results.sort(key=lambda x: x['composite'], reverse=True)

    # 6. Output
    print()
    print(format_table(results, top_n))
    print()

    # Signal distribution
    signals = {}
    for r in results:
        sig = r['signal']
        signals[sig] = signals.get(sig, 0) + 1

    print("📊 SIGNAL DISTRIBUTION:")
    for sig in ["🟢 STRONG BUY", "🟡 WATCHLIST", "⚪ NEUTRAL", "🟠 WARNING", "🔴 DANGER"]:
        cnt = signals.get(sig, 0)
        pct = cnt / len(results) * 100 if results else 0
        bar = "█" * int(pct / 2) + "░" * (50 - int(pct / 2))
        print(f"  {sig}: {cnt:>3} ({pct:>5.1f}%) {bar}")

    # Low liquidity
    low_liq = [r for r in results if r['low_liquidity']]
    if low_liq:
        print(f"\n⚠️  {len(low_liq)} subnets flagged LOW LIQUIDITY")

    # Detail view
    if netuid_filter is not None:
        matching = [r for r in results if r['netuid'] == netuid_filter]
        if matching:
            print(format_detail(matching[0]))

    # Charts
    if chart_netuid is not None:
        hist = pool_histories.get(chart_netuid, [])
        res = next((r for r in results if r['netuid'] == chart_netuid), None)
        path = generate_chart(chart_netuid, hist, res)
        if path:
            print(f"\n📈 Chart: {path}")

    if not quick and not chart_netuid and not netuid_filter:
        print("\n📈 Generating charts for top 5...")
        for r in results[:5]:
            path = generate_chart(r['netuid'], pool_histories.get(r['netuid'], []), r)
            if path:
                print(f"  UID {r['netuid']}: {path}")

    # Export
    if export == "csv":
        import csv
        csv_path = OUTPUT_DIR / f"scan_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.csv"
        with open(csv_path, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['netuid','name','price','mcap','stage','a','b','c','d','e','score','signal'])
            for r in results:
                w.writerow([r['netuid'],r['name'],r['price'],r['market_cap'],r['stage'],
                           r['cat_a'],r['cat_b'],r['cat_c'],r['cat_d'],r['cat_e'],r['composite'],r['signal']])
        print(f"📁 CSV: {csv_path}")
    elif export == "json":
        json_path = OUTPUT_DIR / f"scan_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.json"
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"📁 JSON: {json_path}")

    # Cache
    if not quick:
        cache_file = CACHE_DIR / "pool_cache.json"
        cache_data = {str(k): v for k, v in pool_histories.items()}
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, default=str)
        print("💾 Cached pool histories")

    # Save results
    results_path = OUTPUT_DIR / f"results_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"💾 Results: {results_path}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mia's Bittensor Subnet Scanner")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--top", type=int)
    parser.add_argument("--netuid", type=int)
    parser.add_argument("--chart", type=int)
    parser.add_argument("--export", choices=["csv", "json"])
    args = parser.parse_args()

    run_scan(quick=args.quick, top_n=args.top, netuid_filter=args.netuid,
             chart_netuid=args.chart, export=args.export)