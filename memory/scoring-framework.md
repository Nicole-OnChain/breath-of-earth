# Bittensor Subnet Scoring Framework
# Combining Weinstein Stage Analysis + VirtualBacon Crypto Methodology
# Adapted for Bittensor's dTAO Alpha Token Ecosystem

## PART 1: FOUNDATION — What Drives Alpha Prices

Before defining metrics, we need to understand the price mechanism:

In Bittensor dTAO, alpha price = tao_in_pool / alpha_in_pool (constant product AMM).
This means alpha price rises when:
  1. Tao flows IN (people buying alpha — staking tao for alpha)
  2. Alpha flows OUT (burning, recycling — reduces supply)
  3. Both simultaneously = strongest signal

This is fundamentally different from traditional crypto where price = exchange orderbook.
Here, the ON-CHAIN POOL IS the price discovery mechanism.

Key insight: Every metric we score must ultimately answer one question:
"Is capital flowing INTO this subnet faster than it's leaving?"

---

## PART 2: THE TWO FRAMEWORKS

### Stan Weinstein — Stage Analysis (1988)

Weinstein's model divides any asset's lifecycle into 4 stages:

STAGE 1 — BASE/BOTTOM
  - Price flat, moving average flat or declining slowly
  - Volume declining
  - No institutional interest
  - Risk: Can stay here indefinitely (dead money)

STAGE 2 — UPTREND (THE BUY ZONE)
  - Price breaks above resistance on volume
  - Moving average turns upward, price above MA
  - Higher highs, higher lows
  - Increasing volume on up-moves, decreasing on pullbacks
  - This is where Phase 2 begins (your definition matches Stage 2)

STAGE 3 — TOP/DISTRIBUTION
  - Price flattens, fails to make new highs
  - Moving average flattens, price oscillates around MA
  - Volume on sell-offs increases
  - Smart money exiting

STAGE 4 — DOWNTREND
  - Price below declining moving average
  - Lower highs, lower lows
  - Increasing volume on declines
  - Do not buy. Do not average down.

Weinstein's cardinal rules:
  1. Never buy in Stage 3 or 4
  2. Buy only in Stage 2 after breakout confirmation
  3. The 30-week (150-day) moving average is the primary trend indicator
  4. Volume must confirm the move
  5. Never buy a breakout without volume confirmation

### VirtualBacon — Crypto Analysis Framework

Dennis (VirtualBacon) combines technical analysis with crypto-native fundamentals:

TECHNICAL LAYER:
  - Moving average alignment (50/200 day crossover — golden cross)
  - Price vs. 200-day MA (above = bullish, below = bearish)
  - RSI momentum (not overbought on breakout = room to run)
  - Volume trend (increasing = institutional accumulation)
  - Support/resistance zones on higher timeframes

FUNDAMENTAL LAYER (crypto-native):
  - Token economics (emission schedule, supply dynamics)
  - Network activity (users, transactions, TVL growth)
  - Developer activity (commits, contributors)
  - Team conviction (insider buying, stake retention)
  - Narrative/market positioning (does this solve a real problem?)

RISK MANAGEMENT:
  - Position sizing based on conviction
  - Stop losses at technical levels (below support, below MA)
  - Never more than 5-10% in a single alt
  - Take profits in tranches (not all at once)

KEY VIRTUALBACON PRINCIPLE:
"Price follows network growth. If people are using it and building on it,
price will eventually reflect that. The lag is your opportunity."

---

## PART 3: ADAPTING FOR BITTENSOR ALPHA TOKENS

### Why Traditional Metrics Need Modification

1. Alpha tokens trade in an AMM pool, not order books
   → "Volume" = net flow into the pool, not exchange volume

2. Moving averages need to be calculated from pool price history
   → TAO Stats provides daily pool history (price, market_cap, alpha_in_pool)

3. "Developer activity" in Bittensor = miner registration + miner count growth
   → Not GitHub commits, but network participation

4. "Team conviction" = owner stake retention + recycling behavior
   → Owner hotkey activity visible on-chain

5. Emission schedules are on-chain and deterministic
   → Can be calculated precisely, not estimated

### What We CAN Score (API-Verified)

CATEGORY A — PRICE TREND & STAGE (Weinstein Core)
  A1. Price vs. 150-day moving average (above/below, how far)
  A2. 50-day MA vs. 150-day MA alignment (golden/death cross)
  A3. 30-day price momentum (higher highs, higher lows pattern)
  A4. Breakout detection (price crossing above resistance)
  A5. Moving average slope (turning up / flat / turning down)

CATEGORY B — FLOW & VOLUME CONFIRMATION (Weinstein + VB)
  B1. Net flow 1-day (capital in vs. out, yesterday)
  B2. Net flow 7-day (weekly trend)
  B3. Net flow 30-day (monthly trend — primary flow indicator)
  B4. Tao flow direction (real-time capital movement)
  B5. Recycling 24h (alpha being burned = supply reduction)

CATEGORY C — NETWORK ACTIVITY (VirtualBacon Fundamentals)
  C1. Active miners (current participation)
  C2. Miner growth rate (are more miners joining?)
  C3. Active validators (security/infrastructure health)
  C4. Capacity utilization (active / max_neurons — how full)
  C5. Difficulty trend (rising difficulty = competitive mining = value signal)

CATEGORY D — EMISSIONS & YIELD ECONOMICS
  D1. Current emission rate
  D2. Projected emission
  D3. Fee rate (transaction cost — lower = more attractive)
  D4. Alpha staked vs. total alpha (staking ratio — high = conviction)
  D5. Root proportion (root_prop — how much root protocol stake)

CATEGORY E — SURVIVAL & RISK (Bittensor-Specific)
  E1. Pruning rank (how close to deregistration — 1 = most at risk)
  E2. Immunity period remaining
  E3. Registration cost (high cost = high demand to join)
  E4. Subtoken enabled (can alpha be transferred/traded)

---

## PART 4: SCORING MODEL — Percentage Out of 100

Each subnet gets a composite score: 0-100%

### Weight Distribution

  PRICE TREND & STAGE (Category A):    35%
    Reason: Weinstein showed stage determines ~70% of outcome.
    If you're in Stage 4, no amount of good fundamentals saves you.

  FLOW CONFIRMATION (Category B):      25%
    Reason: In AMM pricing, flow IS volume.
    No flow = no price movement regardless of stage signal.

  NETWORK ACTIVITY (Category C):        20%
    Reason: VirtualBacon's "price follows network growth."
    This is the fundamental confirmation layer.

  EMISSIONS & YIELD (Category D):       10%
    Reason: Important for entry timing but doesn't
    determine direction — it determines magnitude.

  SURVIVAL & RISK (Category E):         10%
    Reason: Binary risk (deregistration) can zero out
    a position. Must be screened first, then scored.

### Category Scoring (each 0-100%)

CATEGORY A — PRICE TREND & STAGE (35% of total)

  A1. Price vs. 150-day MA
    Price >10% above MA → 100
    Price 0-10% above MA → 70
    Price 0-5% below MA  → 40
    Price 5-15% below MA → 20
    Price >15% below MA  → 0

  A2. 50-day vs. 150-day MA (Golden Cross)
    50-day > 150-day, both rising → 100
    50-day > 150-day, 150-day flat → 70
    50-day crossing above 150-day → 60
    50-day < 150-day, 50-day rising → 40
    50-day < 150-day, both declining → 0

  A3. 30-day Price Pattern
    Higher highs + higher lows → 100
    Higher highs, flat lows → 70
    Flat highs, higher lows → 50
    Flat (base pattern) → 30
    Lower highs, lower lows → 0

  A4. Breakout Signal
    Price broke above resistance <5 days ago → 100
    Price near resistance (within 5%) → 60
    Price mid-range → 30
    Price near support → 10
    Price below support → 0

  A5. 150-day MA Slope
    Slope >2% per month upward → 100
    Slope 0-2% upward → 70
    Flat (within ±0.5%) → 30
    Slope 0-2% downward → 10
    Slope >2% downward → 0

  Category A score = (A1*0.25 + A2*0.25 + A3*0.20 + A4*0.15 + A5*0.15)

CATEGORY B — FLOW CONFIRMATION (25% of total)

  B1. Net flow 1-day (relative to market cap)
    Flow >0.5% of mcap → 100
    Flow 0.1-0.5% of mcap → 70
    Flow 0-0.1% of mcap → 40
    Flow -0.1-0% of mcap → 20
    Flow <-0.5% of mcap → 0

  B2. Net flow 7-day (same scale as B1)
  B3. Net flow 30-day (same scale as B1)

  B4. Tao flow direction
    Strongly positive → 100
    Mildly positive → 70
    Neutral → 40
    Mildly negative → 20
    Strongly negative → 0

  B5. Recycling 24h
    Recycling >0, increasing → 100
    Recycling >0, stable → 70
    Recycling >0, decreasing → 40
    No recycling → 20

  Category B score = (B1*0.15 + B2*0.25 + B3*0.35 + B4*0.15 + B5*0.10)

CATEGORY C — NETWORK ACTIVITY (20% of total)

  C1. Active miners
    >50 miners → 100
    30-50 → 80
    15-30 → 60
    5-15 → 30
    <5 → 10

  C2. Miner growth (7-day change in active_miners)
    Growing >10% → 100
    Growing 0-10% → 70
    Stable (±2%) → 40
    Declining 0-10% → 20
    Declining >10% → 0

  C3. Active validators
    >10 → 100
    5-10 → 70
    2-5 → 40
    1 → 10
    0 → 0

  C4. Capacity utilization (active / max_neurons)
    >80% → 100 (high demand)
    50-80% → 70
    30-50% → 40
    10-30% → 20
    <10% → 5

  C5. Difficulty trend
    Rising >10% → 100
    Rising 0-10% → 70
    Stable → 40
    Declining → 10

  Category C score = (C1*0.20 + C2*0.25 + C3*0.15 + C4*0.25 + C5*0.15)

CATEGORY D — EMISSIONS & YIELD (10% of total)

  D1. Current emission (relative to other subnets — percentile rank)
    Top 25% → 100
    50-75th percentile → 70
    25-50th percentile → 40
    Bottom 25% → 10

  D2. Projected emission (same percentile approach)

  D3. Fee rate
    Bottom 25% (lowest fees) → 100
    25-50th percentile → 70
    50-75th → 40
    Top 25% (highest fees) → 10

  D4. Staking ratio (alpha_staked / total_alpha)
    >80% → 100
    60-80% → 70
    40-60% → 40
    20-40% → 20
    <20% → 5

  D5. Root proportion (root_prop)
    >50% → 100 (strong root backing)
    25-50% → 70
    10-25% → 40
    5-10% → 20
    <5% → 5

  Category D score = (D1*0.25 + D2*0.25 + D3*0.15 + D4*0.20 + D5*0.15)

CATEGORY E — SURVIVAL & RISK (10% of total)

  E1. Pruning rank (among 128 subnets)
    Rank >100 (safe) → 100
    Rank 50-100 → 70
    Rank 20-50 → 40
    Rank 10-20 → 20
    Rank <10 → 0

  E2. Immunity remaining (blocks)
    Full immunity → 100
    >50% remaining → 70
    25-50% → 40
    <25% → 10
    No immunity → 0

  E3. Registration cost
    Top 25% (highest = most demand) → 100
    50-75th → 70
    25-50th → 40
    Bottom 25% → 10

  E4. Subtoken enabled
    Yes → 100
    No → 20

  Category E score = (E1*0.35 + E2*0.25 + E3*0.25 + E4*0.15)

---

## PART 5: COMPOSITE SCORE

Total Score = (A * 0.35) + (B * 0.25) + (C * 0.20) + (D * 0.10) + (E * 0.10)

### Score Interpretation

  80-100%: STRONG BUY SIGNAL — Stage 2 confirmed, flow confirming,
           network growing. This is the Phase 2 breakout you're looking for.

  60-79%:  WATCHLIST — Positive signals but not fully confirmed.
           May be early Stage 2 or late Stage 1 base.
           Set alerts for breakout confirmation.

  40-59%:  NEUTRAL — Mixed signals. Not a buy, not a sell.
           Stage 1 base or Stage 3 distribution.
           Wait for clarity.

  20-39%:  WARNING — Negative signals. Likely Stage 3 or early Stage 4.
           Do not enter. If holding, set stops.

  0-19%:   DANGER — Stage 4 decline. Capital leaving, network shrinking.
           Avoid. If holding, exit plan needed.

---

## PART 6: STRESS TEST

### Where This Framework Can Fail

1. FALSE BREAKOUTS (Stage 2 signal that fails)
   - Weinstein warned: breakouts fail ~40% of the time
   - Mitigation: Require Category B (flow) to confirm.
     A price breakout without flow confirmation = suspicious.
     Our framework weights flow at 25% for this reason.

2. EMISSION TRAPS (high emission ≠ good investment)
   - A subnet can have high emission but declining price if
     alpha supply is growing faster than tao inflow
   - Mitigation: Emissions only worth 10% of score.
     Flow (net_flow) matters more than raw emission.

3. NEW SUBNET BIAS (high scores from novelty, not quality)
   - New subnets start with small numbers that distort
     growth rates (going from 2 to 4 miners = 100% growth)
   - Mitigation: C4 (capacity utilization) penalizes low-activity subnets.
     C1 (absolute miner count) ensures minimum participation.

4. WHALE MANIPULATION (single large stake distorts flow)
   - One large staker can create a "breakout" signal
   - Mitigation: This is the hardest to detect with API data alone.
     Cross-reference: if flow spike but miners/validators flat →
     suspicious. Flow must be confirmed by network activity (Category C).

5. IMMUNITY PERIOD ARBITRAGE
   - Immune subnets can't be deregistered, so they may have
     inflated scores while immune, then crash when immunity ends
   - Mitigation: E1/E2 handle this, but the 10% weight may not
     be enough for immune subnets near expiry.
     ADD-ON: Flag any subnet with <25% immunity remaining
     with a manual review alert regardless of score.

6. AMM SLIPPAGE DISTORTION
   - Low-liquidity subnets have volatile pool prices that
     look like breakouts but are just slippage from small trades
   - Mitigation: Cross-reference liquidity from pool data.
     Low alpha_in_pool + low total_tao = low liquidity = unreliable price.
     THRESHOLD: If total_tao < 1000 TAO, flag as "low liquidity —
     price signals unreliable"

7. CORRELATION WITH TAO PRICE
   - Alpha prices are denominated in TAO. When TAO rises,
   all alpha prices can appear to rise even if the subnet is weak
   - Mitigation: Normalize alpha price against TAO/USD.
     Track alpha performance in USD terms, not just TAO.
     This requires the TAO OHLC endpoint for conversion.

### Known Gaps (Data We Don't Have)

1. Developer activity (GitHub commits, contributor count)
   → Not available via TAO Stats API
   → Partially proxied by miner growth (C2)

2. Social sentiment / community size
   → Not available
   → Could add Twitter/Discord scraping later

3. Team identity / doxxed status
   → Not available via API
   → Manual research required

4. Volume on external exchanges (if alpha is listed)
   → Not available via TAO Stats
   → Could add CoinGecko API integration

5. Delegation flow by coldkey (who is staking/unstaking)
   → Available via /api/delegation/v1 but very high volume
   → Could add whale tracking as separate module

---

## PART 7: IMPLEMENTATION PLAN

### Phase 1: Core Scanner (build first)
1. Pull all 129 subnets from /api/subnet/latest/v1
2. Pull 150-day pool history for each subnet from /api/dtao/pool/history/v1
3. Calculate moving averages (50-day, 150-day) from pool history
4. Calculate all Category A-E scores
5. Output ranked table with composite score
6. Generate chart per subnet (price + MAs + flow overlay)

### Phase 2: Alert System
1. Alert when subnet crosses from <60 to >60 (entering Phase 2)
2. Alert when subnet crosses from >60 to <40 (potential Stage 3/4)
3. Alert on flow anomalies (sudden large inflow/outflow)
4. Alert on pruning risk (rank <20)
5. Alert on whale moves (large delegation changes)

### Phase 3: Dashboard
1. HTML dashboard with all subnets ranked
2. Color-coded stages (green=Stage 2, yellow=Stage 1, red=Stage 3/4)
3. Click-through to individual subnet detail
4. Auto-updating via cron job (every 30 min)

### API Budget Planning

Per scan (all 129 subnets):
  - /api/subnet/latest/v1: 3 pages × 1 call = 3 credits
  - /api/dtao/pool/history/v1: 129 subnets × 2 pages = 258 credits
  - /api/subnet/pruning/latest/v1: 3 pages = 3 credits
  Total per scan: ~264 credits

At 10,000 credits/month:
  - Every 30 min: 48 scans/day × 264 = 12,672/day → TOO MANY
  - Every 2 hours: 12 scans/day × 264 = 3,168/day → 95,040/month → STILL TOO MANY
  - Every 6 hours: 4 scans/day × 264 = 1,056/day → 31,680/month → STILL OVER
  - Every 12 hours: 2 scans/day × 264 = 528/day → 15,840/month → OVER
  - Daily: 1 scan/day × 264 = 264/day → 7,920/month → WORKS

  VERDICT: Full scan daily. Quick scan (subnets only, no pool history) every 2 hours.
  Pool history only needed for MA calculation — cache and update daily.

  Quick scan = subnet data + pruning = ~6 credits = very cheap.
  Full scan = subnet + pool + pruning = ~264 credits = once daily.