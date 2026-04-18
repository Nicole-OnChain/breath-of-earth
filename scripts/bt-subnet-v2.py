#!/usr/bin/env python3
"""
Bittensor Subnet Data Puller v2 — Uses correct Dynamic TAO storage function names.
Pulls pool reserves, computes prices, and classifies subnets.
"""

import json
from substrateinterface import SubstrateInterface

RPC = "wss://entrypoint-finney.opentensor.ai:443"

RAO_PER_TAO = 1e9  # 1 TAO = 1,000,000,000 RAO

def connect():
    print(f"Connecting to {RPC}...")
    substrate = SubstrateInterface(url=RPC, auto_reconnect=True)
    print("Connected.\n")
    return substrate

def rao_to_tao(rao):
    """Convert RAO to TAO."""
    if isinstance(rao, (int, float)):
        return rao / RAO_PER_TAO
    return rao

def get_subnet_data(substrate, netuid):
    """Pull all available data for a subnet."""
    data = {"netuid": netuid}

    # Check if subnet exists
    try:
        exists = substrate.query("SubtensorModule", "NetworksAdded", [netuid])
        if not exists or not exists.value:
            return None
    except:
        return None

    # Subnet name
    try:
        name = substrate.query("SubtensorModule", "NetworkName", [netuid])
        data["name"] = name.value if name else f"SN{netuid}"
    except:
        data["name"] = f"SN{netuid}"

    # TAO reserve (SubnetTao = TAO staked into the subnet pool)
    try:
        tao_reserve = substrate.query("SubtensorModule", "SubnetTao", [netuid])
        data["tao_reserve_rao"] = tao_reserve.value if tao_reserve else 0
        data["tao_reserve_tao"] = rao_to_tao(data["tao_reserve_rao"])
    except:
        data["tao_reserve_rao"] = 0
        data["tao_reserve_tao"] = 0

    # Alpha in reserve (SubnetAlphaIn = alpha available in the pool)
    try:
        alpha_in = substrate.query("SubtensorModule", "SubnetAlphaIn", [netuid])
        data["alpha_reserve"] = alpha_in.value if alpha_in else 0
    except:
        data["alpha_reserve"] = 0

    # Alpha outstanding (SubnetAlphaOut = alpha held by participants)
    try:
        alpha_out = substrate.query("SubtensorModule", "SubnetAlphaOut", [netuid])
        data["alpha_outstanding"] = alpha_out.value if alpha_out else 0
    except:
        data["alpha_outstanding"] = 0

    # Emission
    try:
        emission = substrate.query("SubtensorModule", "Emission", [netuid])
        data["emission_rao"] = emission.value if emission else 0
        # Emission is a list — total emission for this subnet
        if isinstance(data["emission_rao"], list):
            data["emission_rao"] = sum(x for x in data["emission_rao"] if isinstance(x, (int, float)))
        data["emission_tao"] = rao_to_tao(data["emission_rao"])
    except:
        data["emission_rao"] = 0
        data["emission_tao"] = 0

    # Subnet owner
    try:
        owner = substrate.query("SubtensorModule", "SubnetOwner", [netuid])
        data["owner"] = owner.value if owner else "N/A"
    except:
        data["owner"] = "N/A"

    # Neuron count (NetworkN)
    try:
        n = substrate.query("SubtensorModule", "NetworkN", [netuid])
        data["neuron_count"] = n.value if n else 0
    except:
        data["neuron_count"] = 0

    # Compute alpha price (TAO per alpha) = tao_reserve / alpha_reserve
    if data["alpha_reserve"] and data["alpha_reserve"] > 0:
        data["alpha_price_tao"] = data["tao_reserve_rao"] / data["alpha_reserve"]
    else:
        data["alpha_price_tao"] = 0

    # Compute market cap (alpha_outstanding * price in TAO)
    data["market_cap_tao"] = data["alpha_outstanding"] * data["alpha_price_tao"]

    # Total alpha supply = alpha_reserve + alpha_outstanding
    data["total_alpha_supply"] = data["alpha_reserve"] + data["alpha_outstanding"]

    return data

def classify_weinstein_stage(data, all_data):
    """
    Classify a subnet into Weinstein Stage 1-4 based on available data.
    
    Since we only have a snapshot (no time-series for 30WMA), we use:
    - Alpha price relative to other subnets (relative valuation)
    - Net TAO flow indicators (emission share as proxy)
    - Neuron count (participation trend proxy)
    - Market cap relative position
    
    Returns: dict with stage, confidence, and reasoning
    """
    netuid = data["netuid"]
    name = data["name"]
    price = data.get("alpha_price_tao", 0)
    mcap = data.get("market_cap_tao", 0)
    neurons = data.get("neuron_count", 0)
    emission = data.get("emission_tao", 0)
    tao_reserve = data.get("tao_reserve_tao", 0)

    # Special case: Root subnet (netuid 0)
    if netuid == 0:
        return {
            "stage": "N/A",
            "confidence": "HIGH",
            "reasoning": "Root subnet — no alpha token, no stage classification applicable"
        }

    # Calculate ranking metrics across all subnets
    active_subnets = [s for s in all_data if s["netuid"] != 0 and s.get("alpha_price_tao", 0) > 0]
    if not active_subnets:
        return {"stage": "UNKNOWN", "confidence": "LOW", "reasoning": "No comparable data"}

    prices = [s["alpha_price_tao"] for s in active_subnets]
    mcaps = [s["market_cap_tao"] for s in active_subnets]
    emissions = [s["emission_tao"] for s in active_subnets]
    total_emission = sum(emissions) if emissions else 1

    # Price rank (percentile)
    price_rank = sum(1 for p in prices if p < price) / len(prices) if prices else 0

    # Emission share
    emission_share = emission / total_emission if total_emission > 0 else 0

    # Emission rank
    emission_rank = sum(1 for e in emissions if e < emission) / len(emissions) if emissions else 0

    # Market cap rank
    mcap_rank = sum(1 for m in mcaps if m < mcap) / len(mcaps) if mcaps else 0

    # Classification logic (snapshot-based approximation)
    # High price + high emission share + high neuron count = Stage 2
    # High price + declining emissions = Stage 3
    # Low price + low emissions + low neurons = Stage 4 or 1
    # Low price + rising emission share = Stage 1 (accumulation)

    if emission_share > 0.03 and price_rank > 0.5 and neurons > 50:
        # High emissions, decent price, good participation → Advancing
        stage = 2
        confidence = "MEDIUM"
        reasoning = f"High emission share ({emission_share:.1%}), price in top {int((1-price_rank)*100)}%, {neurons} neurons active"
    elif emission_share > 0.02 and price_rank > 0.3:
        # Moderate emissions, moderate price → could be Stage 2 or late Stage 1
        if neurons > 30:
            stage = 2
            confidence = "LOW"
            reasoning = f"Moderate emission share ({emission_share:.1%}), decent participation ({neurons} neurons). Could be early Stage 2 or late Stage 1 — need 30WMA trend to confirm"
        else:
            stage = 1
            confidence = "LOW"
            reasoning = f"Some emission share ({emission_share:.1%}) but low participation ({neurons} neurons). Likely accumulation/basing"
    elif emission_share < 0.01 and price_rank < 0.3:
        if neurons < 20:
            # Very low everything → Stage 4 (declining) or dead
            stage = 4
            confidence = "LOW"
            reasoning = f"Near-zero emissions ({emission_share:.2%}), low price (bottom {int(price_rank*100)}%), minimal participation ({neurons} neurons). Likely declining or dormant"
        else:
            # Low price, some neurons still → Stage 1 (basing)
            stage = 1
            confidence = "LOW"
            reasoning = f"Low emissions ({emission_share:.2%}), low price, but {neurons} neurons still active. Possibly basing/accumulation"
    elif price_rank > 0.5 and emission_share < 0.02:
        # Price still high but emissions dropping → Stage 3 (topping)
        stage = 3
        confidence = "LOW"
        reasoning = f"Price elevated (top {int((1-price_rank)*100)}%) but emission share declining ({emission_share:.1%}). Distribution/topping pattern"
    else:
        # Default: Stage 1
        stage = 1
        confidence = "LOW"
        reasoning = f"Marginal activity — emission share {emission_share:.2%}, price rank {price_rank:.1%}, {neurons} neurons. Insufficient data for strong classification"

    return {
        "stage": stage,
        "stage_name": {1: "BASING", 2: "ADVANCING", 3: "TOPPING", 4: "DECLINING"}.get(stage, "UNKNOWN"),
        "confidence": confidence,
        "reasoning": reasoning,
        "emission_share": f"{emission_share:.2%}",
        "price_rank": f"{price_rank:.1%}",
        "mcap_rank": f"{mcap_rank:.1%}",
    }

def main():
    substrate = connect()

    # Get total subnets
    total = substrate.query("SubtensorModule", "TotalNetworks", [])
    total = total.value if total else 0
    print(f"Total subnets: {total}\n")

    # Pull data for all subnets
    all_data = []
    for netuid in range(total + 1):
        print(f"  Subnet {netuid:>3}...", end=" ", flush=True)
        data = get_subnet_data(substrate, netuid)
        if data:
            name = data.get('name', '?')[:20]
            price = data.get('alpha_price_tao', 0)
            print(f"  {name:<20} Price: {price:.6f} τ/α  TAO: {data.get('tao_reserve_tao', 0):>10.2f}  Neurons: {data.get('neuron_count', 0)}")
            all_data.append(data)
        else:
            print("  (not registered)")

    print(f"\nFound {len(all_data)} active subnets\n")

    # Classify each subnet
    results = []
    for data in all_data:
        classification = classify_weinstein_stage(data, all_data)
        data["weinstein_stage"] = classification
        results.append(data)

    # Sort by emission (descending) — top subnets first
    results.sort(key=lambda x: x.get("emission_tao", 0), reverse=True)

    # Save full results
    output_path = "/root/.openclaw/workspace/research/subnet-analysis-full.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Full data saved to {output_path}\n")

    # Print summary table
    print("=" * 140)
    print(f"{'UID':>4} {'Name':<20} {'Price(τ/α)':<12} {'TAO Reserve':<14} {'MktCap(τ)':<14} {'Emission(τ)':<14} {'Neurons':<8} {'Stage':<10} {'Conf':<7} Reason")
    print("-" * 140)
    for r in results:
        netuid = r["netuid"]
        name = str(r.get("name", "?"))[:20]
        price = r.get("alpha_price_tao", 0)
        tao_res = r.get("tao_reserve_tao", 0)
        mcap = r.get("market_cap_tao", 0)
        emission = r.get("emission_tao", 0)
        neurons = r.get("neuron_count", 0)
        stage_info = r.get("weinstein_stage", {})
        stage = stage_info.get("stage_name", "?")
        conf = stage_info.get("confidence", "?")
        reason = stage_info.get("reasoning", "")[:70]
        print(f"{netuid:>4} {name:<20} {price:<12.6f} {tao_res:<14.2f} {mcap:<14.2f} {emission:<14.6f} {neurons:<8} {stage:<10} {conf:<7} {reason}")

    # Stage summary
    stage_counts = {}
    for r in results:
        s = r.get("weinstein_stage", {}).get("stage_name", "UNKNOWN")
        stage_counts[s] = stage_counts.get(s, 0) + 1

    print(f"\n--- Stage Distribution ---")
    for stage, count in sorted(stage_counts.items()):
        print(f"  {stage}: {count} subnets")

if __name__ == "__main__":
    main()