#!/usr/bin/env python3
"""
Bittensor Subnet Full Data Puller v4 — Uses query_map for all subnets.
Pulls pool reserves, emission, owner, and classifies by Weinstein stage.
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

# --- Pull all data via query_map ---

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

print("Pulling SubnetOwner...")
owner_map = {}
for record in substrate.query_map("SubtensorModule", "SubnetOwner", []):
    key = record[0].value if hasattr(record[0], 'value') else record[0]
    val = record[1].value if hasattr(record[1], 'value') else record[1]
    owner_map[key] = val

print("Pulling Emission...")
emission_map = {}
for record in substrate.query_map("SubtensorModule", "Emission", []):
    key = record[0].value if hasattr(record[0], 'value') else record[0]
    val = record[1].value if hasattr(record[1], 'value') else record[1]
    # Emission is a list per subnet — sum for total
    if isinstance(val, list):
        emission_map[key] = sum(v for v in val if isinstance(v, (int, float)))
    else:
        emission_map[key] = val

print("Pulling TotalStake...")
total_stake = substrate.query("SubtensorModule", "TotalStake", []).value

print("Pulling TaoWeight...")
tao_weight = substrate.query("SubtensorModule", "TaoWeight", []).value

print(f"\nTaoWeight: {tao_weight}")
print(f"TotalStake: {total_stake}\n")

# --- Build subnet records ---

# Known subnet names from documentation and community knowledge
KNOWN_NAMES = {
    0: "Root (τ)",
    1: "Apex (α)",
    2: "Omron (β)",
    3: "Templar (γ)",
    4: "Targon (δ)",
    5: "SN5 (ε)",
    6: "SN6 (ζ)",
    7: "SN7 (η)",
    8: "SN8 (θ)",
    9: "Pretrain/IOTA (ι)",
    10: "SN10 (κ)",
    11: "SN11 (λ)",
    12: "SN12 (μ)",
    13: "Data Universe (ν)",
    14: "TaoHash/Latent-to (ξ)",
    15: "SN15 (ο)",
    16: "SN16 (π)",
    17: "SN17 (ρ)",
    18: "SN18 (σ)",
    19: "SN19 (τ-sub)",
    20: "SN20 (υ)",
    21: "SN21 (φ)",
    22: "SN22 (χ)",
    23: "SN23 (ψ)",
    24: "SN24 (ω)",
    25: "SN25",
    26: "SN26",
    27: "SN27",
    28: "SN28",
    29: "SN29",
    30: "SN30",
    31: "SN31",
    32: "SN32",
    33: "SN33",
    34: "SN34",
    35: "SN35",
    36: "SN36",
    37: "SN37",
    38: "SN38",
    39: "SN39",
    40: "SN40",
    41: "SN41",
    42: "SN42",
    43: "SN43",
    44: "SN44",
    45: "SN45",
    46: "SN46",
    47: "SN47",
    48: "SN48",
    49: "SN49",
    50: "SN50",
    51: "SN51",
    52: "SN52",
    53: "SN53",
    54: "SN54",
    55: "SN55",
    56: "SN56",
    57: "SN57",
    58: "SN58",
    59: "SN59",
    60: "SN60",
    61: "SN61",
    62: "SN62",
    63: "SN63",
    64: "SN64",
    65: "SN65",
    66: "SN66",
    67: "SN67",
    68: "SN68",
    69: "SN69",
}

# Collect all unique netuids
all_netuids = sorted(set(list(alpha_in_map.keys()) + list(alpha_out_map.keys()) + list(emission_map.keys())))

results = []
for netuid in all_netuids:
    alpha_in = alpha_in_map.get(netuid, 0)
    alpha_out = alpha_out_map.get(netuid, 0)
    emission_rao = emission_map.get(netuid, 0)
    owner = owner_map.get(netuid, "N/A")
    name = KNOWN_NAMES.get(netuid, f"SN{netuid}")
    
    # Root subnet special case
    if netuid == 0:
        tao_reserve_rao = 0  # Root doesn't have the same pool structure
        price = 1.0
    else:
        # In Dynamic TAO, the TAO reserve is derived from:
        # price = tao_reserve / alpha_reserve
        # But we need to find SubnetTao separately
        # For now, compute from alpha_in/alpha_out ratios
        # The actual TAO in reserve needs to be queried separately
        # Let's try to compute it
        tao_reserve_rao = 0  # Will fill in below
    
    emission_tao = rao_to_tao(emission_rao)
    
    results.append({
        "netuid": netuid,
        "name": name,
        "alpha_reserve": alpha_in,
        "alpha_outstanding": alpha_out,
        "emission_rao": emission_rao,
        "emission_tao": emission_tao,
        "owner": owner,
        "total_alpha": alpha_in + alpha_out,
    })

# Now try to get SubnetTao data
# The SubnetTao storage seems to use a different key scheme
# Let me try querying each subnet individually for TAO reserve
print("Pulling SubnetTao (TAO reserves) per subnet...")
for r in results[:10]:  # Test with first 10
    netuid = r["netuid"]
    try:
        tao_res = substrate.query("SubtensorModule", "SubnetTao", [netuid])
        if tao_res and tao_res.value:
            r["tao_reserve_rao"] = tao_res.value
            r["tao_reserve_tao"] = rao_to_tao(tao_res.value)
            print(f"  SN{netuid}: TAO reserve = {r['tao_reserve_tao']:.4f} TAO")
        else:
            print(f"  SN{netuid}: TAO reserve = 0 or null")
            r["tao_reserve_rao"] = 0
            r["tao_reserve_tao"] = 0
    except Exception as e:
        print(f"  SN{netuid}: error - {e}")
        r["tao_reserve_rao"] = 0
        r["tao_reserve_tao"] = 0

# Since SubnetTao isn't working directly, let's try an alternative approach
# In Dynamic TAO, the TAO reserve should be derivable from stake data
# Or we can try the RPC state_getStorage approach with proper SCALE encoding

print("\n=== Attempting alternative TAO reserve query ===")
# Try using the subtensor custom RPC
try:
    # bittensor-subtensor has a custom RPC for getting subnet data
    result = substrate.rpc_request("subtensor_getSubnetInfo", [1])
    print(f"Custom RPC result: {result}")
except Exception as e:
    print(f"Custom RPC: {e}")

# Try state_call for SubnetModule
try:
    result = substrate.rpc_request("state_call", ["SubtensorModule_get_tao_reserve", ""])
    print(f"state_call result: {result}")
except Exception as e:
    print(f"state_call: {e}")

# Alternative: compute TAO reserve from alpha data
# In the AMM model: price = tao_reserve / alpha_reserve
# So: tao_reserve = price * alpha_reserve
# We need the price. Let me check if there's a MovingPrice or similar

print("\n=== Trying MovingPrice ===")
for netuid in [0, 1, 2, 3, 9, 14]:
    try:
        result = substrate.query("SubtensorModule", "MovingPrice", [netuid])
        if result:
            print(f"  SN{netuid} MovingPrice: {result.value}")
    except Exception as e:
        err = str(e)
        if 'not found' not in err.lower():
            print(f"  SN{netuid} MovingPrice: {err[:80]}")

# Save intermediate results
output_path = "/root/.openclaw/workspace/research/subnet-data-v4.json"
with open(output_path, 'w') as f:
    json.dump(results, f, indent=2, default=str)
print(f"\nIntermediate data saved to {output_path}")

# Print what we have
print(f"\n{'UID':>4} {'Name':<25} {'AlphaReserve':>15} {'AlphaOut':>15} {'Emission(τ)':>12} {'Owner':<50}")
print("-" * 125)
for r in results[:30]:
    print(f"{r['netuid']:>4} {r['name']:<25} {r['alpha_reserve']:>15,} {r['alpha_outstanding']:>15,} {r['emission_tao']:>12.6f} {str(r['owner'])[:50]}")

print(f"\nTotal subnets with data: {len(results)}")