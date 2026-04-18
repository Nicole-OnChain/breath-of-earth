#!/usr/bin/env python3
"""
Bittensor Subnet Full Analysis v5 — Complete data pull + Weinstein Stage Classification.
"""

import json
from substrateinterface import SubstrateInterface

RPC = "wss://entrypoint-finney.opentensor.ai:443"
RAO_PER_TAO = 1e9

def rao_to_tao(rao):
    return rao / RAO_PER_TAO if isinstance(rao, (int, float)) else 0

print("Connecting to Bittensor Finney...")
substrate = SubstrateInterface(url=RPC, auto_reconnect=True)
print("Connected.\n")

# --- Pull all data ---

print("Pulling SubnetTAO (TAO reserves)...")
tao_map = {}
for record in substrate.query_map("SubtensorModule", "SubnetTAO", []):
    key = record[0].value if hasattr(record[0], 'value') else record[0]
    val = record[1].value if hasattr(record[1], 'value') else record[1]
    tao_map[key] = val

print("Pulling SubnetAlphaIn (alpha reserves)...")
alpha_in_map = {}
for record in substrate.query_map("SubtensorModule", "SubnetAlphaIn", []):
    key = record[0].value if hasattr(record[0], 'value') else record[0]
    val = record[1].value if hasattr(record[1], 'value') else record[1]
    alpha_in_map[key] = val

print("Pulling SubnetAlphaOut (alpha outstanding)...")
alpha_out_map = {}
for record in substrate.query_map("SubtensorModule", "SubnetAlphaOut", []):
    key = record[0].value if hasattr(record[0], 'value') else record[0]
    val = record[1].value if hasattr(record[1], 'value') else record[1]
    alpha_out_map[key] = val

print("Pulling Emission...")
emission_map = {}
for record in substrate.query_map("SubtensorModule", "Emission", []):
    key = record[0].value if hasattr(record[0], 'value') else record[0]
    val = record[1].value if hasattr(record[1], 'value') else record[1]
    if isinstance(val, list):
        emission_map[key] = sum(v for v in val if isinstance(v, (int, float)))
    else:
        emission_map[key] = val

print("Pulling SubnetOwner...")
owner_map = {}
for record in substrate.query_map("SubtensorModule", "SubnetOwner", []):
    key = record[0].value if hasattr(record[0], 'value') else record[0]
    val = record[1].value if hasattr(record[1], 'value') else record[1]
    owner_map[key] = val

print("Pulling NetworksAdded...")
registered = set()
for netuid in range(130):
    try:
        result = substrate.query("SubtensorModule", "NetworksAdded", [netuid])
        if result and result.value:
            registered.add(netuid)
    except:
        pass

print(f"Found {len(registered)} registered subnets\n")

# --- Build subnet records ---

all_netuids = sorted(registered)
total_emission = sum(emission_map.values())

results = []
for netuid in all_netuids:
    tao_reserve_rao = tao_map.get(netuid, 0)
    alpha_in = alpha_in_map.get(netuid, 0)
    alpha_out = alpha_out_map.get(netuid, 0)
    emission_rao = emission_map.get(netuid, 0)
    owner = owner_map.get(netuid, "N/A")
    
    tao_reserve_tao = rao_to_tao(tao_reserve_rao)
    emission_tao = rao_to_tao(emission_rao)
    
    # Compute alpha price
    if alpha_in > 0:
        alpha_price = tao_reserve_rao / alpha_in
    else:
        alpha_price = 0
    
    # Market cap in TAO
    mcap_tao = alpha_out * alpha_price / RAO_PER_TAO
    
    # Total alpha supply
    total_alpha = alpha_in + alpha_out
    
    # Emission share
    emission_share = emission_rao / total_emission if total_emission > 0 else 0
    
    # Owner stake weight (simplified: how much TAO is in the pool relative to alpha outstanding)
    pool_depth_ratio = tao_reserve_rao / alpha_out if alpha_out > 0 else 0
    
    results.append({
        "netuid": netuid,
        "tao_reserve_tao": round(tao_reserve_tao, 4),
        "alpha_reserve": alpha_in,
        "alpha_outstanding": alpha_out,
        "total_alpha": total_alpha,
        "alpha_price_tao": round(alpha_price, 8),
        "market_cap_tao": round(mcap_tao, 4),
        "emission_rao": emission_rao,
        "emission_tao": round(emission_tao, 6),
        "emission_share_pct": round(emission_share * 100, 4),
        "owner": str(owner)[:20] if owner != "N/A" else "N/A",
    })

# --- Weinstein Stage Classification ---

# Since we have a single snapshot, we classify based on relative position:
# - Price (alpha_price) ranking across subnets
# - Emission share
# - Pool depth (TAO reserve size) as proxy for participation/confidence
# - Alpha outstanding as proxy for active participants

# Separate root subnet
root = [r for r in results if r["netuid"] == 0]
active = [r for r in results if r["netuid"] != 0 and r["alpha_price_tao"] > 0]

# Compute rankings
prices = sorted([r["alpha_price_tao"] for r in active])
emissions = sorted([r["emission_tao"] for r in active])
reserves = sorted([r["tao_reserve_tao"] for r in active])

for r in active:
    # Price percentile (higher = more valued)
    r["price_pctile"] = sum(1 for p in prices if p < r["alpha_price_tao"]) / len(prices) * 100 if prices else 0
    # Emission percentile (higher = more flow)
    r["emission_pctile"] = sum(1 for e in emissions if e < r["emission_tao"]) / len(emissions) * 100 if emissions else 0
    # Reserve percentile (higher = more staked)
    r["reserve_pctile"] = sum(1 for res in reserves if res < r["tao_reserve_tao"]) / len(reserves) * 100 if reserves else 0
    
    # Composite score (0-100)
    r["composite_score"] = (r["price_pctile"] * 0.35 + r["emission_pctile"] * 0.40 + r["reserve_pctile"] * 0.25)
    
    # Stage classification
    if r["netuid"] == 0:
        r["stage"] = "N/A"
        r["stage_name"] = "ROOT"
        r["confidence"] = "HIGH"
        r["reasoning"] = "Root subnet — no alpha token"
    elif r["composite_score"] > 70:
        r["stage"] = 2
        r["stage_name"] = "ADVANCING"
        r["confidence"] = "MEDIUM"
        r["reasoning"] = f"Top {100-r['composite_score']:.0f}% by composite. High price ({r['alpha_price_tao']:.6f} τ/α), strong emissions ({r['emission_share_pct']:.2f}%), large TAO pool ({r['tao_reserve_tao']:.0f} τ)"
    elif r["composite_score"] > 40:
        r["stage"] = 2
        r["stage_name"] = "ADVANCING"
        r["confidence"] = "LOW"
        r["reasoning"] = f"Mid-range composite. Decent price ({r['alpha_price_tao']:.6f} τ/α), moderate emissions ({r['emission_share_pct']:.2f}%). Could be early Stage 2 or late Stage 1 — need 30WMA trend to confirm"
    elif r["composite_score"] > 20:
        r["stage"] = 1
        r["stage_name"] = "BASING"
        r["confidence"] = "LOW"
        r["reasoning"] = f"Below average. Low emissions ({r['emission_share_pct']:.2f}%), price at {r['alpha_price_tao']:.6f} τ/α. Accumulation/basing phase — watch for flow reversal"
    elif r["composite_score"] > 5:
        r["stage"] = 4
        r["stage_name"] = "DECLINING"
        r["confidence"] = "LOW"
        r["reasoning"] = f"Low composite ({r['composite_score']:.1f}). Minimal emissions ({r['emission_share_pct']:.3f}%), low TAO reserve. At risk of death spiral under flow model"
    else:
        r["stage"] = 4
        r["stage_name"] = "DECLINING"
        r["confidence"] = "MEDIUM"
        r["reasoning"] = f"Very low composite ({r['composite_score']:.1f}). Near-zero emissions, negligible TAO pool. Dormant or dying"

# Sort by composite score (highest first)
active.sort(key=lambda x: x["composite_score"], reverse=True)

# --- Save full results ---
output_path = "/root/.openclaw/workspace/research/subnet-analysis-final.json"
with open(output_path, 'w') as f:
    json.dump({"root": root, "active": active, "total_emission_tao": rao_to_tao(total_emission)}, f, indent=2, default=str)
print(f"Full data saved to {output_path}\n")

# --- Print summary table ---
print(f"{'UID':>3} {'Price(τ/α)':<13} {'TAO Reserve':<13} {'MktCap(τ)':<13} {'Emission%':<10} {'Score':<7} {'Stage':<12} {'Conf':<7} Top Reason")
print("=" * 150)
for r in active[:30]:  # Top 30
    reason_short = r["reasoning"][:60]
    print(f"{r['netuid']:>3} {r['alpha_price_tao']:<13.8f} {r['tao_reserve_tao']:<13.1f} {r['market_cap_tao']:<13.1f} {r['emission_share_pct']:<10.3f} {r['composite_score']:<7.1f} {r['stage_name']:<12} {r['confidence']:<7} {reason_short}")

print(f"\n--- Bottom 10 ---")
for r in active[-10:]:
    reason_short = r["reasoning"][:60]
    print(f"{r['netuid']:>3} {r['alpha_price_tao']:<13.8f} {r['tao_reserve_tao']:<13.1f} {r['market_cap_tao']:<13.1f} {r['emission_share_pct']:<10.3f} {r['composite_score']:<7.1f} {r['stage_name']:<12} {r['confidence']:<7} {reason_short}")

# Stage distribution
stage_counts = {}
for r in active:
    s = r.get("stage_name", "UNKNOWN")
    stage_counts[s] = stage_counts.get(s, 0) + 1

print(f"\n--- Stage Distribution ---")
for stage, count in sorted(stage_counts.items()):
    pct = count / len(active) * 100
    print(f"  {stage}: {count} subnets ({pct:.1f}%)")

print(f"\nTotal active (non-root) subnets: {len(active)}")
print(f"Total network emission: {rao_to_tao(total_emission):.2f} TAO")

# --- Save formatted markdown report ---
md = "# Bittensor Subnet Weinstein Stage Analysis\n\n"
md += f"**Data pulled:** Live from Bittensor Finney chain\n"
md += f"**Total subnets:** {len(active)} (+ Root)\n"
md += f"**Total emission:** {rao_to_tao(total_emission):.2f} TAO\n\n"

md += "## Stage Distribution\n\n"
md += "| Stage | Count | % |\n|-------|-------|---|\n"
for stage, count in sorted(stage_counts.items()):
    md += f"| {stage} | {count} | {count/len(active)*100:.1f}% |\n"

md += "\n## Top 20 Subnets by Composite Score\n\n"
md += "| UID | Price (τ/α) | TAO Reserve | MktCap (τ) | Emission% | Score | Stage | Confidence |\n"
md += "|-----|-------------|------------|------------|-----------|--------|-------|------------|\n"
for r in active[:20]:
    md += f"| {r['netuid']} | {r['alpha_price_tao']:.8f} | {r['tao_reserve_tao']:.1f} | {r['market_cap_tao']:.1f} | {r['emission_share_pct']:.3f}% | {r['composite_score']:.1f} | {r['stage_name']} | {r['confidence']} |\n"

md += "\n## ⚠️ Important Limitations\n\n"
md += "This is a **snapshot analysis** — single point in time, no 30WMA history.\n"
md += "Weinstein's method requires price trend relative to the 30-week moving average.\n"
md += "Without historical data, stages are approximated using:\n"
md += "- Alpha price ranking (35% weight)\n"
md += "- Emission share ranking (40% weight)\n"
md += "- TAO reserve ranking (25% weight)\n\n"
md += "**To improve accuracy, we need:**\n"
md += "1. Historical alpha price data (30 weeks minimum) for proper 30WMA calculation\n"
md += "2. Net TAO flow trends over time (staking vs unstaking direction)\n"
md += "3. Volume data from taostats Pro API\n\n"
md += "**Next step:** Set up weekly data snapshots to build the time series needed for proper 30WMA calculation.\n"

report_path = "/root/.openclaw/workspace/research/bittensor-subnet-stage-analysis.md"
with open(report_path, 'w') as f:
    f.write(md)
print(f"\nMarkdown report saved to {report_path}")