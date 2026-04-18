#!/usr/bin/env python3
"""
Bittensor Subnet Data Puller v3 — Correct storage function names.
"""

import json
from substrateinterface import SubstrateInterface

RPC = "wss://entrypoint-finney.opentensor.ai:443"
RAO_PER_TAO = 1e9

substrate = SubstrateInterface(url=RPC, auto_reconnect=True)
print("Connected to Bittensor Finney\n")

total = substrate.query("SubtensorModule", "TotalNetworks", []).value
print(f"Total subnets: {total}\n")

# Discover storage functions by trying many patterns
print("=== Discovering storage functions ===")
func_tests = [
    # Pool data (we know these work)
    "SubnetAlphaIn", "SubnetAlphaOut",
    # TAO reserve - try various names
    "SubnetTao", "TaoReserve", "SubnetTaoReserve", "TaoPool",
    # Network info
    "NetworkName", "SubnetName", "NetworkN", "SubnetN", "N", "SubnetNCount",
    "Neurons", "SubnetNeurons", "NetworkRegistered", "IsNetwork",
    # Emission
    "Emission", "SubnetEmission",
    # Price/flow
    "MovingPrice", "SubnetPrice", "AlphaPrice",
    "TaoInflow", "TaoOutflow", "NetFlow",
    # Owner
    "SubnetOwner", "Owner",
    # Subnet hyperparams
    "Hyperparameters", "SubnetHyperparams",
    # Tempo
    "Tempo", "SubnetTempo",
    # Weights
    "Weights", "SubnetWeights",
    # Stake
    "Stake", "TotalStake", "SubnetStake",
    # Registration
    "NetworksAdded", "Registered",
    # Other Dynamic TAO
    "AlphaOutstanding", "MovingAlphaPrice",
    "TaoWeight", "SubnetTaoIn",
]

working = {}
for func in func_tests:
    try:
        result = substrate.query("SubtensorModule", func, [0])
        val = result.value if result else None
        working[func] = val
        val_str = str(val)[:80] if val is not None else "None"
        print(f"  ✓ {func}([0]) = {val_str}")
    except Exception as e:
        err = str(e)
        if 'not found' in err.lower() or 'not exist' in err.lower():
            pass  # Doesn't exist, skip silently
        elif 'parameter' in err.lower() or 'param' in err.lower():
            print(f"  ~ {func} exists but needs different params: {err[:80]}")
        else:
            print(f"  ? {func}: {err[:80]}")

# Try query_map for some functions
print("\n=== Trying query_map for pool data ===")
for func in ["SubnetAlphaIn", "SubnetAlphaOut", "Emission", "SubnetOwner"]:
    try:
        result = substrate.query_map("SubtensorModule", func, [])
        count = 0
        items = []
        for record in result:
            key = record[0].value if hasattr(record[0], 'value') else record[0]
            val = record[1].value if hasattr(record[1], 'value') else record[1]
            items.append((key, val))
            count += 1
            if count >= 5:
                break
        print(f"  {func} query_map: {count}+ items, sample: {items[:3]}")
    except Exception as e:
        print(f"  {func} query_map: {str(e)[:80]}")

# Try query_map with [0] param
for func in ["SubnetAlphaIn", "SubnetAlphaOut"]:
    try:
        result = substrate.query_map("SubtensorModule", func, [0])
        count = 0
        for record in result:
            count += 1
            if count >= 3:
                break
        print(f"  {func} query_map([0]): {count} items")
    except Exception as e:
        print(f"  {func} query_map([0]): {str(e)[:80]}")

print("\nDone discovering.")