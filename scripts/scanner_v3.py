#!/usr/bin/env python3
"""
Mia's Bittensor Subnet Scanner v3 — Rate-Limit Aware
Fetches data slowly across multiple runs, caches everything, resumes from where it left off.

Usage:
  python3 scanner_v3.py              # Continue/resume scan
  python3 scanner_v3.py --fresh       # Start fresh
  python3 scanner_v3.py --score-only  # Score using cached data only
  python3 scanner_v3.py --top 20      # Show top 20
  python3 scanner_v3.py --netuid 8    # Deep dive
  python3 scanner_v3.py --chart 8     # Chart
"""

import requests
import json
import time
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

API_KEY = "tao-52f985f8-94c7-4963-82c1-d1e6876b5142:0b44ec02"
BASE_URL = "https://api.taostats.io"
HEADERS = {"Authorization": API_KEY, "Accept": "application/json"}
WORK_DIR = Path("/root/.openclaw/workspace/memory/scanner_cache")
WORK_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR = Path("/root/.openclaw/workspace/memory/scanner_output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR = Path("/root/.openclaw/workspace/memory/chart")
CHART_DIR.mkdir(parents=True, exist_ok=True)

# Conservative rate: 1 request every 2 seconds = 0.5 req/s
# This ensures we stay well under the 5 req/s limit and don't burn credits
CALL_INTERVAL = 2.0


def slow_get(endpoint, params=None):
    """Single API request with built-in rate limiting and retry."""
    url = f"{BASE_URL}{endpoint}"
    p = (params or {}).copy()
    p.setdefault("limit", 100)
    p.setdefault("page", 1)

    for attempt in range(5):
        try:
            resp = requests.get(url, headers=HEADERS, params=p, timeout=30)
            if resp.status_code == 429:
                wait = 10 * (attempt + 1)
                print(f"    429 rate limited, waiting {wait}s... (attempt {attempt+1}/5)", file=sys.stderr)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"    Error: {e}", file=sys.stderr)
            time.sleep(5)
    return None


def fetch_subnets():
    """Fetch all subnet data (2 pages, ~129 subnets)."""
    cache = WORK_DIR / "subnets.json"
    if cache.exists():
        age = time.time() - cache.stat().st_mtime
        if age < 7200:  # less than 2 hours old
            with open(cache) as f:
                data = json.load(f)
            print(f"📦 Loaded {len(data)} subnets from cache ({age/60:.0f} min old)")
            return data

    print("📡 Fetching subnet data...")
    all_data = []
    for page in [1, 2]:
        time.sleep(CALL_INTERVAL)
        body = slow_get("/api/subnet/latest/v1", {"page": page, "limit": 100})
        if body and body.get("data"):
            all_data.extend(body["data"])
        else:
            print(f"  Page {page} failed or empty")

    print(f"  Got {len(all_data)} subnets")
    with open(cache, 'w') as f:
        json.dump(all_data, f, default=str)
    return all_data


def fetch_pruning():
    """Fetch pruning data."""
    cache = WORK_DIR / "pruning.json"
    if cache.exists():
        age = time.time() - cache.stat().st_mtime
        if age < 7200:
            with open(cache) as f:
                data = json.load(f)
            print(f"📦 Loaded pruning data from cache ({age/60:.0f} min old)")
            return data

    print("📡 Fetching pruning data...")
    time.sleep(CALL_INTERVAL)
    body = slow_get("/api/subnet/pruning/latest/v1", {"page": 1, "limit": 200})
    data = body.get("data", []) if body else []
    print(f"  Got {len(data)} pruning records")
    with open(cache, 'w') as f:
        json.dump(data, f, default=str)
    return data


def fetch_pool_history(netuid):
    """Fetch pool history for a single subnet (2 pages = ~200 days)."""
    cache = WORK_DIR / f"pool_{netuid}.json"
    if cache.exists():
        age = time.time() - cache.stat().st_mtime
        if age < 86400:  # less than 1 day old
            with open(cache) as f:
                data = json.load(f)
            return data

    all_data = []
    for page in [1, 2]:
        time.sleep(CALL_INTERVAL)
        body = slow_get("/api/dtao/pool/history/v1", {
            "netuid": netuid, "frequency": "by_day", "page": page, "limit": 100
        })
        if body and body.get("data"):
            all_data.extend(body["data"])
        else:
            break  # no more pages

    if all_data:
        with open(cache, 'w') as f:
            json.dump(all_data, f, default=str)
    return all_data


def fetch_all_pools(netuids, fresh=False):
    """Fetch pool histories for all subnets, one at a time, caching each."""
    if fresh:
        for f in WORK_DIR.glob("pool_*.json"):
            f.unlink()

    got = 0
    skipped = 0
    for i, netuid in enumerate(netuids):
        cache = WORK_DIR / f"pool_{netuid}.json"
        if cache.exists():
            skipped += 1
            continue

        if i > 0 and i % 5 == 0:
            print(f"  Progress: {i}/{len(netuids)} (fetched: {got}, cached: {skipped})")

        data = fetch_pool_history(netuid)
        if data:
            got += 1

    print(f"  Pool histories: {got} fetched, {skipped} cached")


# ============================================================
# SCORING (same as v2)
# ============================================================

def safe_float(val, default=0.0):
    if val is None: return default
    try: return float(val)
    except: return default

def safe_int(val, default=0):
    if val is None: return default
    try: return int(val)
    except: return default

def score_a1(p):
    if p > 10: return 100
    elif p > 0: return 70
    elif p > -5: return 40
    elif p > -15: return 20
    else: return 0

def score_a2(above, sl150, sl50):
    if above and sl150 > 0 and sl50 > 0: return 100
    elif above and sl150 >= 0: return 70
    elif above: return 60
    elif not above and sl50 > 0: return 40
    elif not above and sl150 < 0: return 0
    else: return 20

def score_a3(hh, hl):
    if hh and hl: return 100
    elif hh: return 70
    elif hl: return 50
    else: return 30

def score_a4(pos):
    if pos > 0.95: return 100
    elif pos > 0.85: return 60
    elif pos > 0.4: return 30
    elif pos > 0.15: return 10
    else: return 0

def score_a5(s):
    if s > 2: return 100
    elif s > 0: return 70
    elif s > -0.5: return 30
    elif s > -2: return 10
    else: return 0

def score_flow(p):
    if p > 0.5: return 100
    elif p > 0.1: return 70
    elif p > 0: return 40
    elif p > -0.1: return 20
    else: return 0

def score_b4(v):
    if v is None: return 40
    v = v / 1e12 if abs(v) > 1e9 else v
    if v > 100: return 100
    elif v > 10: return 70
    elif v > 0: return 50
    elif v > -10: return 30
    elif v > -100: return 20
    else: return 0

def score_b5(r):
    if r is None or r == 0: return 20
    return 50

def score_c1(m):
    if m > 50: return 100
    elif m > 30: return 80
    elif m > 15: return 60
    elif m > 5: return 30
    else: return 10

def score_c2(g):
    if g > 10: return 100
    elif g > 0: return 70
    elif g > -2: return 40
    elif g > -10: return 20
    else: return 0

def score_c3(v):
    if v > 10: return 100
    elif v > 5: return 70
    elif v > 2: return 40
    elif v == 1: return 10
    else: return 0

def score_c4(u):
    if u > 0.8: return 100
    elif u > 0.5: return 70
    elif u > 0.3: return 40
    elif u > 0.1: return 20
    else: return 5

def score_c5(d):
    if d > 10: return 100
    elif d > 0: return 70
    elif d > -5: return 40
    else: return 10

def score_dpct(p):
    if p > 0.75: return 100
    elif p > 0.50: return 70
    elif p > 0.25: return 40
    else: return 10

def score_d3f(p):
    inv = 1.0 - p
    return score_dpct(inv)

def score_d4(r):
    if r > 0.8: return 100
    elif r > 0.6: return 70
    elif r > 0.4: return 40
    elif r > 0.2: return 20
    else: return 5

def score_d5(r):
    if r > 0.5: return 100
    elif r > 0.25: return 70
    elif r > 0.10: return 40
    elif r > 0.05: return 20
    else: return 5

def score_e1(rank, total=129):
    # rank 1 = lowest moving_price = MOST at risk
    # rank 128 = highest moving_price = SAFEST
    if rank is None: return 50
    safe_pct = rank / total if total > 0 else 0  # higher rank = safer
    if safe_pct > 0.75: return 100
    elif safe_pct > 0.40: return 70
    elif safe_pct > 0.15: return 40
    elif safe_pct > 0.08: return 20
    else: return 0

def score_e2(p):
    if p is None: return 0
    if p > 0.75: return 100
    elif p > 0.50: return 70
    elif p > 0.25: return 40
    elif p > 0: return 10
    else: return 0

def score_e4(e):
    return 100 if e else 20


def calc_mas(prices, short=50, long=150):
    n = len(prices)
    if n < long:
        return None, None, None, None
    ms = sum(prices[-short:]) / short
    ml = sum(prices[-long:]) / long
    off = 10
    if n > long + off:
        pms = sum(prices[-(short+off):-off]) / short
        pml = sum(prices[-(long+off):-off]) / long
    else:
        pms, pml = ms, ml
    return ms, ml, pms, pml


def analyze_pattern(prices):
    n = len(prices)
    if n < 10: return False, False, 0.5
    t = n // 3
    chunks = [prices[:t], prices[t:2*t], prices[2*t:]]
    if not all(chunks): return False, False, 0.5
    highs = [max(c) for c in chunks]
    lows = [min(c) for c in chunks]
    hh = highs[2] > highs[1] >= highs[0] or (highs[1] > highs[0] and highs[2] >= highs[1])
    hl = lows[2] > lows[1] >= lows[0] or (lows[1] > lows[0] and lows[2] >= lows[1])
    if lows[2] < lows[1] < lows[0]: hl = False
    if highs[2] < highs[1] < highs[0]: hh = False
    cur = prices[-1]
    span = max(prices) - min(prices)
    pos = (cur - min(prices)) / span if span > 0 else 0.5
    return hh, hl, pos


def score_subnet(sub, pool, hist, pruning, em_pct, fee_pct, rc_pct):
    uid = safe_int(sub.get("netuid"), -1)
    name = pool.get("name", "") or f"Subnet {uid}"
    sym = pool.get("symbol", "")

    # Subnet-level
    nf1 = safe_float(sub.get("net_flow_1_day"))
    nf7 = safe_float(sub.get("net_flow_7_days"))
    nf30 = safe_float(sub.get("net_flow_30_days"))
    tf = safe_float(sub.get("tao_flow"))
    rec = safe_float(sub.get("recycled_24_hours"))
    miners = safe_int(sub.get("active_keys"))
    validators = safe_int(sub.get("active_validators"))
    max_n = safe_int(sub.get("max_neurons"), 1)
    diff = safe_float(sub.get("difficulty"))
    max_diff = safe_float(sub.get("max_difficulty"), 1)
    sub_en = sub.get("subtoken_enabled", False)

    # Pool-level
    price = safe_float(pool.get("price"))
    mcap = safe_float(pool.get("market_cap"))
    total_tao = safe_float(pool.get("total_tao"))
    total_alpha = safe_float(pool.get("total_alpha"), 1)
    alpha_staked = safe_float(pool.get("alpha_staked"))
    root_prop = safe_float(pool.get("root_prop"))
    rank = safe_int(pool.get("rank"))
    liquidity = safe_float(pool.get("liquidity"))

    # Category A
    a1=a2=a3=a4=a5=30; pvs=0; msl=0; stage="No Data ❓"
    if hist and len(hist) >= 50:
        ps = []
        for e in hist:
            ts_s = e.get("timestamp", "")
            p = safe_float(e.get("price"))
            if ts_s and p > 0:
                ps.append(p)
        ps.reverse()  # oldest first
        cp = ps[-1] if ps else price

        if len(ps) >= 150:
            ms, ml, pms, pml = calc_mas(ps)
        elif len(ps) >= 50:
            ms = sum(ps[-50:]) / 50; ml = None; pms = ms; pml = 0
        else:
            ms = ml = pms = pml = None

        if ml and ml > 0:
            pvs = ((cp - ml) / ml) * 100; a1 = score_a1(pvs)
        if ms is not None and ml is not None:
            above = ms > ml
            if pml > 0: msl = ((ml - pml) / pml) * 100 * 3
            ms50 = ((ms - pms) / pms) * 100 * 3 if pms > 0 else 0
            a2 = score_a2(above, msl, ms50)
        r30 = ps[-30:] if len(ps) >= 30 else ps
        hh, hl, pos = analyze_pattern(r30)
        a3 = score_a3(hh, hl)
        a4 = score_a4(pos)
        a5 = score_a5(msl)

        raw_a = a1*0.25+a2*0.25+a3*0.20+a4*0.15+a5*0.15
        if raw_a >= 70: stage = "Stage 2 📈"
        elif raw_a >= 40: stage = "Stage 1 ➡️"
        elif raw_a >= 20: stage = "Stage 3 ⚠️"
        else: stage = "Stage 4 🔻"

    cat_a = a1*0.25+a2*0.25+a3*0.20+a4*0.15+a5*0.15

    # Category B
    f1 = (nf1/mcap*100) if mcap > 0 else 0
    f7 = (nf7/mcap*100) if mcap > 0 else 0
    f30 = (nf30/mcap*100) if mcap > 0 else 0
    b1=score_flow(f1); b2=score_flow(f7); b3=score_flow(f30)
    b4=score_b4(tf); b5=score_b5(rec)
    cat_b = b1*0.15+b2*0.25+b3*0.35+b4*0.15+b5*0.10

    # Category C
    c1=score_c1(miners); c2=score_c2(f7*2); c3=score_c3(validators)
    util = miners/max_n if max_n > 0 else 0
    c4=score_c4(util)
    dr = diff/max_diff if max_diff > 0 else 0
    c5=score_c5(dr*50)
    cat_c = c1*0.20+c2*0.25+c3*0.15+c4*0.25+c5*0.15

    # Category D
    sr = alpha_staked/total_alpha if total_alpha > 0 else 0
    d1=score_dpct(em_pct); d2=score_dpct(em_pct); d3=score_d3f(fee_pct)
    d4=score_d4(sr); d5=score_d5(root_prop)
    cat_d = d1*0.25+d2*0.25+d3*0.15+d4*0.20+d5*0.15

    # Category E
    pi = pruning.get(uid, {})
    prank = pi.get("pruning_rank")
    imm = pi.get("immunity_pct")
    e1=score_e1(prank); e2=score_e2(imm)
    e3=score_dpct(rc_pct); e4=score_e4(sub_en)
    cat_e = e1*0.35+e2*0.25+e3*0.25+e4*0.15

    composite = cat_a*0.35+cat_b*0.25+cat_c*0.20+cat_d*0.10+cat_e*0.10
    if composite >= 80: sig = "🟢 STRONG BUY"
    elif composite >= 60: sig = "🟡 WATCHLIST"
    elif composite >= 40: sig = "⚪ NEUTRAL"
    elif composite >= 20: sig = "🟠 WARNING"
    else: sig = "🔴 DANGER"

    low_liq = total_tao < 1e12

    return {
        "netuid": uid, "name": name, "symbol": sym,
        "price": price, "market_cap": mcap, "total_tao": total_tao,
        "rank": rank, "stage": stage,
        "cat_a": round(cat_a,1), "cat_b": round(cat_b,1),
        "cat_c": round(cat_c,1), "cat_d": round(cat_d,1),
        "cat_e": round(cat_e,1), "composite": round(composite,1),
        "signal": sig, "low_liquidity": low_liq,
        "detail": {
            "a1":round(a1),"a2":round(a2),"a3":round(a3),"a4":round(a4),"a5":round(a5),
            "b1":round(b1),"b2":round(b2),"b3":round(b3),"b4":round(b4),"b5":round(b5),
            "c1":round(c1),"c2":round(c2),"c3":round(c3),"c4":round(c4),"c5":round(c5),
            "d1":round(d1),"d2":round(d2),"d3":round(d3),"d4":round(d4),"d5":round(d5),
            "e1":round(e1),"e2":round(e2),"e3":round(e3),"e4":round(e4),
            "price_vs_ma150": round(pvs,2), "ma150_slope": round(msl,2),
            "flow_1d_pct": round(f1,4), "flow_7d_pct": round(f7,4),
            "flow_30d_pct": round(f30,4),
            "active_miners": miners, "active_validators": validators,
            "capacity_util": round(util*100,1), "staking_ratio": round(sr*100,1),
            "pruning_rank": prank, "root_prop": round(root_prop,4),
        }
    }


def pct_rank(items, field):
    vals = [(i, safe_float(i.get(field))) for i in items if safe_float(i.get(field)) != 0]
    if not vals: return {}
    vals.sort(key=lambda x: x[1])
    n = len(vals)
    return {safe_int(v.get("netuid")): (r+1)/n for r, (v, _) in enumerate(vals)}


def build_pmap(pruning):
    m = {}
    for e in pruning:
        uid = safe_int(e.get("netuid"), -1)
        if uid < 0: continue
        rank = safe_int(e.get("pruning_rank"))
        immune = e.get("is_immune", False)
        ib = safe_int(e.get("immunity_blocks_remaining"), 0)
        ti = safe_int(e.get("immunity_period"), 4096)
        ip = ib/ti if immune and ti > 0 else 0
        m[uid] = {"pruning_rank": rank, "immunity_pct": ip, "is_immune": immune}
    return m


def ascii_bar(s, w=20):
    f = int(s/100*w)
    ch = "█▓▒░·"[min(4, max(0, 4 - int(s/20)))]
    return ch*f + "░"*(w-f)


def fmt_table(results, top=None):
    items = results[:top] if top else results
    lines = [f"{'#':<4} {'UID':<5} {'Name':<25} {'Price':<10} {'Stage':<14} {'A':>5} {'B':>5} {'C':>5} {'D':>5} {'E':>5} {'Score':>7} {'Signal'}",
             "─"*115]
    for i, r in enumerate(items):
        nm = (r['name'] or f"Subnet {r['netuid']}")[:23]
        liq = " ⚠" if r['low_liquidity'] else ""
        pr = f"{r['price']:.4f}" if r['price'] > 0 else "N/A"
        lines.append(f"{i+1:<4} {r['netuid']:<5} {nm:<25}{liq} {pr:<10} {r['stage']:<14} "
                     f"{r['cat_a']:>5.1f} {r['cat_b']:>5.1f} {r['cat_c']:>5.1f} "
                     f"{r['cat_d']:>5.1f} {r['cat_e']:>5.1f} {r['composite']:>6.1f}% {r['signal']}")
    return "\n".join(lines)


def fmt_detail(r):
    d = r['detail']
    return f"""
{"═"*55}
  SUBNET {r['netuid']}: {r['name']} ({r['symbol']})
  COMPOSITE: {r['composite']}% {r['signal']}
  STAGE: {r['stage']}   Rank: #{r.get('rank','N/A')}
{"═"*55}

  A — PRICE TREND & STAGE  [{r['cat_a']}%]  {ascii_bar(r['cat_a'])}
    A1. Price vs 150d MA:    {d['a1']:>3}  ({d['price_vs_ma150']:+.1f}%)
    A2. 50d vs 150d MA:      {d['a2']:>3}
    A3. 30d Pattern:         {d['a3']:>3}
    A4. Breakout Signal:     {d['a4']:>3}
    A5. 150d MA Slope:       {d['a5']:>3}  ({d['ma150_slope']:.2f}%/mo)

  B — FLOW CONFIRMATION     [{r['cat_b']}%]  {ascii_bar(r['cat_b'])}
    B1. Net Flow 1d:         {d['b1']:>3}  ({d['flow_1d_pct']:+.3f}%)
    B2. Net Flow 7d:         {d['b2']:>3}  ({d['flow_7d_pct']:+.3f}%)
    B3. Net Flow 30d:        {d['b3']:>3}  ({d['flow_30d_pct']:+.3f}%)
    B4. Tao Flow:            {d['b4']:>3}
    B5. Recycling:           {d['b5']:>3}

  C — NETWORK ACTIVITY      [{r['cat_c']}%]  {ascii_bar(r['cat_c'])}
    C1. Active Miners:       {d['c1']:>3}  ({d['active_miners']})
    C2. Miner Growth:        {d['c2']:>3}
    C3. Active Validators:   {d['c3']:>3}  ({d['active_validators']})
    C4. Capacity Util:       {d['c4']:>3}  ({d['capacity_util']}%)
    C5. Difficulty:          {d['c5']:>3}

  D — EMISSIONS & YIELD     [{r['cat_d']}%]  {ascii_bar(r['cat_d'])}
    D1. Emission Rank:       {d['d1']:>3}
    D2. Proj Emission:       {d['d2']:>3}
    D3. Fee Rate Rank:       {d['d3']:>3}
    D4. Staking Ratio:       {d['d4']:>3}  ({d['staking_ratio']}%)
    D5. Root Proportion:     {d['d5']:>3}  ({d['root_prop']})

  E — SURVIVAL & RISK       [{r['cat_e']}%]  {ascii_bar(r['cat_e'])}
    E1. Pruning Rank:        {d['e1']:>3}  (rank: {d.get('pruning_rank','N/A')})
    E2. Immunity:            {d['e2']:>3}
    E3. Reg Cost Rank:       {d['e3']:>3}
    E4. Subtoken Enabled:    {d['e4']:>3}
{"═"*55}"""


def gen_chart(netuid, hist, result=None):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except ImportError:
        return None

    if not hist or len(hist) < 10: return None

    entries = []
    for e in hist:
        ts = e.get("timestamp", "")
        p = safe_float(e.get("price"))
        if ts and p > 0:
            try:
                t = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                entries.append((t, p))
            except: pass
    if len(entries) < 10: return None

    entries.sort(key=lambda x: x[0])
    dates = [e[0] for e in entries]
    prices = [e[1] for e in entries]

    ma50 = [sum(prices[max(0,i-49):i+1])/min(i+1,50) for i in range(len(prices))]
    ma150 = [sum(prices[max(0,i-149):i+1])/min(i+1,150) for i in range(len(prices))]
    # Only show MAs where they have enough data
    ma50_show = [(d,v) for i,(d,v) in enumerate(zip(dates,ma50)) if i >= 49]
    ma150_show = [(d,v) for i,(d,v) in enumerate(zip(dates,ma150)) if i >= 149]

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(dates, prices, color='#00D4AA', linewidth=1.5, label='Alpha Price')
    if ma50_show:
        ax.plot([d for d,_ in ma50_show], [v for _,v in ma50_show],
                color='#FFA500', linewidth=1, linestyle='--', label='50-day MA')
    if ma150_show:
        ax.plot([d for d,_ in ma150_show], [v for _,v in ma150_show],
                color='#FF4444', linewidth=1, linestyle='-', label='150-day MA')

    ax.set_facecolor('#1a1a2e')
    fig.set_facecolor('#1a1a2e')
    ax.tick_params(colors='white')
    for s in ax.spines.values(): s.set_color('#333')
    ax.title.set_color('white')
    ax.yaxis.label.set_color('white')

    n = result['name'] if result else f"Subnet {netuid}"
    sc = result['composite'] if result else 0
    sg = result['signal'] if result else ""
    # Strip emojis from title for matplotlib
    import re
    n_clean = re.sub(r'[^\x00-\x7F]+', '', n).strip()
    sg_clean = re.sub(r'[^\x00-\x7F]+', '', sg).strip()
    ax.set_title(f"{n_clean} (UID {netuid}) - {sc}% {sg_clean}", fontsize=14, fontweight='bold')
    ax.set_ylabel("Price (TAO)")
    ax.legend(loc='upper left', facecolor='#2a2a4e', edgecolor='#444', labelcolor='white')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax.grid(True, alpha=0.2, color='#555')
    plt.tight_layout()

    path = CHART_DIR / f"subnet_{netuid}_chart.png"
    plt.savefig(path, dpi=150, facecolor='#1a1a2e')
    plt.close()
    return str(path)


def run(fresh=False, score_only=False, top_n=None, netuid_filter=None, chart_uid=None):
    print(f"🚀 Mia's Scanner v3")
    print(f"   {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n")

    # Fetch base data
    subnets = fetch_subnets()
    pruning = fetch_pruning()
    pmap = build_pmap(pruning)

    if not subnets:
        print("❌ No subnet data available. Wait for rate limit and retry.")
        return

    # Pool data
    if not score_only:
        netuids = [safe_int(s.get("netuid")) for s in subnets if safe_int(s.get("netuid")) >= 0]
        if netuid_filter is not None:
            netuids = [n for n in netuids if n == netuid_filter]
        fetch_all_pools(netuids, fresh=fresh)

    # Load all pool data from cache
    pool_histories = {}
    pool_latest = {}
    for cf in WORK_DIR.glob("pool_*.json"):
        nuid = int(cf.stem.split("_")[1])
        with open(cf) as f:
            data = json.load(f)
        pool_histories[nuid] = data
        if data:
            pool_latest[nuid] = data[0]

    # Percentile ranks
    em_pct = pct_rank(subnets, "emission")
    fee_pct = pct_rank(subnets, "fee_rate")
    rc_pct = pct_rank(subnets, "neuron_registration_cost")

    # Score
    print("🧮 Scoring subnets...")
    results = []
    for sub in subnets:
        uid = safe_int(sub.get("netuid"), -1)
        if uid < 0: continue
        if netuid_filter is not None and uid != netuid_filter: continue
        hist = pool_histories.get(uid, [])
        latest = pool_latest.get(uid, {})
        r = score_subnet(sub, latest, hist, pmap,
                        em_pct.get(uid, 0.5), fee_pct.get(uid, 0.5), rc_pct.get(uid, 0.5))
        results.append(r)

    results.sort(key=lambda x: x['composite'], reverse=True)

    print()
    print(fmt_table(results, top_n))
    print()

    # Distribution
    sigs = {}
    for r in results:
        sigs[r['signal']] = sigs.get(r['signal'], 0) + 1
    print("📊 SIGNAL DISTRIBUTION:")
    for s in ["🟢 STRONG BUY","🟡 WATCHLIST","⚪ NEUTRAL","🟠 WARNING","🔴 DANGER"]:
        c = sigs.get(s, 0)
        p = c/len(results)*100 if results else 0
        print(f"  {s}: {c:>3} ({p:>5.1f}%)")

    # Low liquidity
    ll = [r for r in results if r['low_liquidity']]
    if ll:
        print(f"\n⚠️  {len(ll)} subnets: LOW LIQUIDITY")

    # Detail
    if netuid_filter is not None:
        m = [r for r in results if r['netuid'] == netuid_filter]
        if m: print(fmt_detail(m[0]))

    # Chart
    if chart_uid is not None:
        hist = pool_histories.get(chart_uid, [])
        res = next((r for r in results if r['netuid'] == chart_uid), None)
        p = gen_chart(chart_uid, hist, res)
        if p: print(f"\n📈 Chart: {p}")

    if not chart_uid and not netuid_filter:
        print("\n📈 Charts for top 5...")
        for r in results[:5]:
            p = gen_chart(r['netuid'], pool_histories.get(r['netuid'], []), r)
            if p: print(f"  UID {r['netuid']}: {p}")

    # Save
    rp = OUTPUT_DIR / f"results_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.json"
    with open(rp, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n💾 Results: {rp}")

    return results


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--fresh", action="store_true")
    p.add_argument("--score-only", action="store_true")
    p.add_argument("--top", type=int)
    p.add_argument("--netuid", type=int)
    p.add_argument("--chart", type=int)
    a = p.parse_args()
    run(fresh=a.fresh, score_only=a.score_only, top_n=a.top,
        netuid_filter=a.netuid, chart_uid=a.chart)