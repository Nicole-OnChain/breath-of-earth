# TAO Stats API Map

**Base URL:** `https://api.taostats.io`
**Auth:** `Authorization: <full-api-key>` (NOT "Bearer" — just the raw key)
**Rate limit:** 5 req/s, 10,000 credits/month (free tier)
**Key validated:** 2026-04-18, 10,000 credits remaining

---

## Confirmed Endpoints

### Network Stats
| Endpoint | Description | Key Fields |
|---|---|---|
| `/api/stats/latest/v1` | Network-wide statistics | subnets, total staked, accounts, extrinsics, transfers, registration cost |

### Subnets
| Endpoint | Description | Key Fields |
|---|---|---|
| `/api/subnet/latest/v1` | All subnet data (77 fields each) | emission, net_flow (1d/7d/30d), alpha_high/low, fee_rate, active_miners/validators, recycling, tao_flow, difficulty, immunity_period, tempo, owner |
| `/api/subnet/pruning/latest/v1` | Deregistration ranking | pruning_rank, is_immune, immunity_blocks_remaining, moving_price |
| `/api/dtao/subnet_emission/v1` | Historical emission by subnet | netuid param required, pagination |
| `/api/dtao/pool/history/v1` | Subnet pool/price history | price, market_cap, alpha_in_pool, total_tao, total_alpha, current_tick, liquidity, fee_rate, rank |
| `/api/dtao/burned_alpha/v1` | Alpha burned per subnet | netuid + block range |

### Validators
| Endpoint | Description | Key Fields |
|---|---|---|
| `/api/validator/latest/v1` | Validator data (29 fields) | apr, apr_7_day_average, apr_30_day_average, stake, stake_24_hr_change, nominators, nominators_24_hr_change, take, dominance, subnet_dominance, permits, registrations, name |
| `/api/dtao/hotkey_alpha_shares/latest/v1` | Alpha shares per hotkey | alpha_min + netuid filters |

### Staking & Delegation
| Endpoint | Description | Key Fields |
|---|---|---|
| `/api/dtao/stake_balance/latest/v1` | Stake balances by coldkey | coldkey param required |
| `/api/dtao/stake_balance/history/v1` | Stake balance history | coldkey + optional hotkey/netuid |
| `/api/delegation/v1` | Delegation transactions | action (DELEGATE/UNDELEGATE), alpha, amount, alpha_price_in_tao, alpha_price_in_usd, slippage, delegate_name, netuid |

### Price Data
| Endpoint | Description | Key Fields |
|---|---|---|
| `/api/price/ohlc/v1` | OHLC for TAO (not alpha) | asset=tao, period, open/high/low/close, volume_24h |
| `/api/coingecko/asset` | Coingecko asset data | id param |
| `/api/coingecko/events` | Coingecko events | fromBlock param |
| `/api/coingecko/latest-block` | Latest block from Coingecko | — |

### Blockchain Data
| Endpoint | Description | Key Fields |
|---|---|---|
| `/api/block/v1` | Block data | pagination, limit |
| `/api/extrinsic/v1` | Extrinsics | full_name filter (e.g. SubtensorModule.set_weights), timestamp_start/end, block range, limit, page |
| `/api/transfer/v1` | Transfers | network, address, block range |
| `/api/metagraph/root/history/v1` | Root metagraph history | block range, pagination |

### Exchanges
| Endpoint | Description | Key Fields |
|---|---|---|
| `/api/exchange/v1` | Exchange coldkey addresses | name, icon, coldkey |

### Accounting (Requires Paid Plan)
| Endpoint | Description |
|---|---|
| `/api/accounting/v1` | Accounting data (network, date range, coldkey) |
| `/api/accounting/tax/v1` | Tax report |
| `/api/accounting/tax_csv/v1` | Tax report as CSV |
| `/api/accounting/tax_token/v1` | Tokens held report |

---

## Key Patterns

- **Pagination:** All endpoints return `{pagination: {current_page, per_page, total_items, total_pages, next_page, prev_page}}`
- **Data envelope:** All responses are `{pagination: {...}, data: [...]}`
- **Common params:** `limit`, `page`, `timestamp_start`/`timestamp_end` (unix), `block_start`/`block_end`
- **Alpha prices:** Use `/api/dtao/pool/history/v1?netuid=X&frequency=by_day` (NOT the OHLC endpoint, which is TAO-only)
- **Validator APY:** `apr` (current), `apr_7_day_average`, `apr_30_day_average`
- **Flow metrics on subnets:** `net_flow_1_day`, `net_flow_7_days`, `net_flow_30_days`, `tao_flow`

## Notes

- Free tier = 5 req/s, 10,000 credits/month. Need to be strategic about polling frequency.
- `endpointAccess: {standard: false, pro: false, rpc: false}` — accounting endpoints may require upgrade.
- Alpha token OHLC not available via `/api/price/ohlc/v1` — use pool/history instead.
- Subnet emission historical data available but needs netuid parameter.