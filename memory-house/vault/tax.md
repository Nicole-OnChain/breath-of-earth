# 🔒 Vault — Tax & Compliance

_Tax engine status, filing deadlines, key numbers._

## 2026 Tax Status
- **Net capital loss YTD:** ($166.06), all short-term
- **Open lots:** $7,469.04 cost basis across 20 assets
- **Tax engine:** FIFO engine v1.0 operational (`tax/engine/fifo_engine.py`)
- **DB:** `data/tax_engine.db`
- **Export:** `data/form_8949_export.csv` — IRS Form 8949 ready
- **Pipeline:** `scripts/tax_pipeline.sh` — sync + rebuild + on-chain tracking

## Key Tax Treatments
- **lcETH:** ETH→lcETH conversion = non-taxable. lcETH appreciation in ETH terms = ordinary income (cToken model)
- **SUI staking rewards:** Ordinary income at receipt
- **Bittensor staking rewards:** Ordinary income at receipt
- **Self-transfers** (Ledger/Nufi/Crucible) = NOT taxable

## Filing Deadlines (2026)
- Q2 estimated payments: June 15, 2026
- Annual filing: April 15, 2027

## Key Lesson
- Negative-sign data from Coinbase/Kraken must be normalized per source
- Dust dispositions <0.5 units get zero-cost lot (conservative approach)