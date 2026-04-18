#!/usr/bin/env python3
"""
Find SubnetTao equivalent — try all possible storage function name patterns.
"""

from substrateinterface import SubstrateInterface

RPC = "wss://entrypoint-finney.opentensor.ai:443"
substrate = SubstrateInterface(url=RPC, auto_reconnect=True)

# Try every plausible name for TAO reserve storage
tao_names = [
    "SubnetTao", "TaoReserve", "SubnetTaoReserve", 
    "TaoPool", "PoolTao", "NetTao",
    "SubnetPoolTao", "PoolReserve",
    # Dynamic TAO specific
    "TaoReserveIn", "ReserveTao",
    "SubnetTaoIn", "SubnetTaoReserveIn",
    "TaoIn", "TAOIn",
    "TaoInReserve", "InReserveTao",
    # Maybe it's part of a struct
    "SubnetPool", "Pool",
    "SubnetData", "SubnetInfo",
    "SubnetState", "SubnetEmissionState",
    # Check for combined storage
    "AlphaTaoReserves", "Reserves",
    "SubnetReserves", "PoolState",
    # Maybe under different naming
    "TaoStaked", "StakedTao",
    "SubnetStaked", "NetStakedTao",
    # Try variations with underscore
    "subnet_tao", "tao_reserve",
    # CamelCase variants
    "SubnetTAO", "TAOReserve",
    # Check SubnetPoolXXX pattern  
    "SubnetPoolAlphaIn", "SubnetPoolAlphaOut",
    "SubnetPoolTaoReserve",
    # Maybe it's EmissionValues that contains the data
    "EmissionValues",
    # Could be named after the liquidity pool
    "LiquidityPool", "AMMReserve",
    "TaoAMMReserve",
    # From subtensor source code
    "SubnetTAOIn", "SubnetTAOPool",
    "TaoInPool", "PoolTaoIn",
    # Dynamic TAO new naming
    "DynamicTAO", "DynamicTao",
    "SubnetDynamicTao",
    "TokenPrice", "SubnetTokenPrice",
    # Check if AlphaIn already IS the TAO reserve (different scale)
]

print("Testing TAO reserve storage function names...")
for name in tao_names:
    try:
        result = substrate.query("SubtensorModule", name, [1])
        if result is not None:
            val = result.value
            val_str = str(val)[:120]
            print(f"  ✓ {name}([1]) = {val_str}")
    except Exception as e:
        err = str(e)
        if 'not found' in err.lower() or 'not exist' in err.lower():
            continue
        elif 'parameter' in err.lower() or 'param' in err.lower():
            print(f"  ~ {name} EXISTS (different params): {err[:100]}")
        elif 'type' in err.lower():
            print(f"  ~ {name} EXISTS (type error): {err[:100]}")
        else:
            print(f"  ? {name}: {err[:100]}")

# Try query_map for SubnetPool or Pool
print("\nTrying query_map for pool-like structures...")
for name in ["SubnetPool", "Pool", "Reserves", "SubnetReserves", "SubnetInfo", "SubnetData", "SubnetState"]:
    try:
        result = substrate.query_map("SubtensorModule", name, [])
        count = 0
        for record in result:
            key = record[0].value if hasattr(record[0], 'value') else record[0]
            val = record[1].value if hasattr(record[1], 'value') else record[1]
            if count < 2:
                print(f"  {name} query_map item: key={key}, val={str(val)[:100]}")
            count += 1
            if count >= 3:
                break
        print(f"  {name} query_map: {count}+ items found")
    except Exception as e:
        err = str(e)
        if 'not found' in err.lower():
            continue
        print(f"  {name} query_map: {err[:100]}")

# IMPORTANT: Check if the Alpha values ARE the pool data
# In Dynamic TAO, SubnetAlphaIn = alpha in the pool (reserve)
# SubnetAlphaOut = alpha outstanding (held by participants)
# The TAO reserve should be tracked separately
# Let me check if there's a way to get it from stake data

print("\n=== Checking TotalStake per subnet ===")
# TotalStake with 0 params gave a number
# Let me try with different params
try:
    ts = substrate.query("SubtensorModule", "TotalStake", [])
    print(f"TotalStake() = {ts.value}")
except Exception as e:
    print(f"TotalStake(): {e}")

# Maybe we need to look at the blockchain state for pool reserves
# using raw RPC calls with proper encoding
print("\n=== Raw RPC: state_getKeysPaged ===")
import hashlib

def make_storage_key(pallet_name, storage_name, netuid=None):
    """Generate Substrate storage key with proper SCALE encoding."""
    m = hashlib.blake2b(digest_size=16)
    m.update(pallet_name.encode('utf-8'))
    pallet_hash = "0x" + m.hexdigest()
    
    m = hashlib.blake2b(digest_size=16)
    m.update(storage_name.encode('utf-8'))
    storage_hash = "0x" + m.hexdigest()
    
    key = pallet_hash + storage_hash
    if netuid is not None:
        # SCALE encode u16
        key += format(netuid & 0xFFFF, '04x')
    return key

# Try getting keys for SubnetAlphaIn to verify our key generation works
key = make_storage_key("SubtensorModule", "SubnetAlphaIn", 1)
try:
    result = substrate.rpc_request("state_getStorage", [key])
    if result.get('result'):
        print(f"  SubnetAlphaIn(1) via raw RPC: {result['result'][:40]}... (SUCCESS)")
    else:
        print(f"  SubnetAlphaIn(1) via raw RPC: null")
except Exception as e:
    print(f"  SubnetAlphaIn(1) raw RPC: {e}")

# Now try SubnetTao
for name in ["SubnetTao", "TaoReserve", "SubnetPool"]:
    key = make_storage_key("SubtensorModule", name, 1)
    try:
        result = substrate.rpc_request("state_getStorage", [key])
        if result.get('result'):
            val_hex = result['result']
            # Decode the SCALE value
            # For u64 values, it's little-endian 8 bytes
            val_bytes = bytes.fromhex(val_hex[2:10])  # First 8 bytes
            import struct
            val = struct.unpack('<Q', val_bytes)[0]
            print(f"  {name}(1) raw: hex={val_hex}, decoded_u64={val}, tao={val/1e9}")
        else:
            print(f"  {name}(1) raw: null (key doesn't exist)")
    except Exception as e:
        print(f"  {name}(1) raw: {e}")

print("\nDone.")