# Bittensor Subnet Weinstein Stage Analysis

**Data pulled:** Live from Bittensor Finney chain
**Total subnets:** 128 (+ Root)
**Total emission:** 36952.54 TAO

## Stage Distribution

| Stage | Count | % |
|-------|-------|---|
| ADVANCING | 68 | 53.1% |
| BASING | 50 | 39.1% |
| DECLINING | 10 | 7.8% |

## Top 20 Subnets by Composite Score

| UID | Price (τ/α) | TAO Reserve | MktCap (τ) | Emission% | Score | Stage | Confidence |
|-----|-------------|------------|------------|-----------|--------|-------|------------|
| 4 | 0.05642988 | 128516.7 | 152651.7 | 0.801% | 76.3 | ADVANCING | MEDIUM |
| 120 | 0.07596383 | 89494.7 | 145050.2 | 0.801% | 76.0 | ADVANCING | MEDIUM |
| 44 | 0.03591493 | 56651.6 | 114922.8 | 0.801% | 74.1 | ADVANCING | MEDIUM |
| 3 | 0.02381026 | 70528.6 | 45729.0 | 0.801% | 73.4 | ADVANCING | MEDIUM |
| 9 | 0.02369282 | 48977.9 | 68583.0 | 0.801% | 72.5 | ADVANCING | MEDIUM |
| 5 | 0.02276582 | 41553.1 | 65409.2 | 0.801% | 71.8 | ADVANCING | MEDIUM |
| 95 | 0.02420821 | 15058.1 | 44278.2 | 0.801% | 68.6 | ADVANCING | LOW |
| 19 | 0.01404607 | 37323.1 | 30618.2 | 0.801% | 68.4 | ADVANCING | LOW |
| 17 | 0.01423675 | 30361.4 | 37898.7 | 0.801% | 68.4 | ADVANCING | LOW |
| 64 | 0.08437409 | 213939.1 | 209699.0 | 0.801% | 68.3 | ADVANCING | LOW |
| 24 | 0.01632097 | 16109.3 | 61768.4 | 0.801% | 67.7 | ADVANCING | LOW |
| 11 | 0.01366957 | 25536.1 | 40081.4 | 0.801% | 67.2 | ADVANCING | LOW |
| 51 | 0.05290806 | 111212.9 | 145321.0 | 0.801% | 67.1 | ADVANCING | LOW |
| 8 | 0.03897041 | 91360.4 | 98925.6 | 0.801% | 66.4 | ADVANCING | LOW |
| 29 | 0.01411956 | 18508.2 | 50256.8 | 0.801% | 66.2 | ADVANCING | LOW |
| 66 | 0.01538059 | 13779.0 | 59109.2 | 0.801% | 65.8 | ADVANCING | LOW |
| 62 | 0.02726309 | 46865.3 | 79319.2 | 0.801% | 64.6 | ADVANCING | LOW |
| 14 | 0.00920867 | 23679.1 | 21596.1 | 0.801% | 64.0 | ADVANCING | LOW |
| 56 | 0.02194434 | 58480.1 | 47935.6 | 0.801% | 63.6 | ADVANCING | LOW |
| 81 | 0.00901128 | 20970.6 | 17473.1 | 0.801% | 63.3 | ADVANCING | LOW |

## ⚠️ Important Limitations

This is a **snapshot analysis** — single point in time, no 30WMA history.
Weinstein's method requires price trend relative to the 30-week moving average.
Without historical data, stages are approximated using:
- Alpha price ranking (35% weight)
- Emission share ranking (40% weight)
- TAO reserve ranking (25% weight)

**To improve accuracy, we need:**
1. Historical alpha price data (30 weeks minimum) for proper 30WMA calculation
2. Net TAO flow trends over time (staking vs unstaking direction)
3. Volume data from taostats Pro API

**Next step:** Set up weekly data snapshots to build the time series needed for proper 30WMA calculation.
