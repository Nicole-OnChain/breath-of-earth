#!/usr/bin/env python3
"""
Deep introspection of Bittensor subtensor pallet storage.
We need to find the correct parameter types for pool data queries.
"""

from substrateinterface import SubstrateInterface

RPC = "wss://entrypoint-finney.opentensor.ai:443"
substrate = SubstrateInterface(url=RPC, auto_reconnect=True)

# Try to get the actual pallet metadata
print("=== Pallet Discovery ===")
try:
    # Use the runtime API to get metadata
    runtime_metadata = substrate.metadata
    
    # Iterate through pallets
    if hasattr(runtime_metadata, 'pallets'):
        for pallet_name, pallet in runtime_metadata.pallets.items():
            if 'subtensor' in pallet_name.lower() or 'Subtensor' in pallet_name:
                print(f"\nPallet: {pallet_name}")
                if hasattr(pallet, 'storage'):
                    for sname, sfunc in pallet.storage.items():
                        print(f"  Storage: {sname}")
                        if hasattr(sfunc, 'type_key'):
                            print(f"    Key type: {sfunc.type_key}")
                        if hasattr(sfunc, 'params'):
                            print(f"    Params: {sfunc.params}")
                        if hasattr(sfunc, 'type_value'):
                            print(f"    Value type: {sfunc.type_value}")
except Exception as e:
    print(f"Method 1 failed: {e}")

# Try querying with different approaches
print("\n=== Trying specific queries with u16 netuid type ===")
for netuid in [0, 1, 2, 3, 9, 14, 19, 20, 21]:
    for func_name in ["SubnetTao", "SubnetAlphaIn", "SubnetAlphaOut", "NetworkName", "NetworkN"]:
        try:
            # Try with ScaleType parameter
            from scalecodec import U16
            result = substrate.query(
                module="SubtensorModule",
                storage_function=func_name,
                params=[netuid],
            )
            val = result.value if result else None
            if val and val != 0:
                print(f"  Subnet {netuid}: {func_name} = {val}")
        except Exception as e:
            if 'not found' not in str(e).lower() and 'not exist' not in str(e).lower():
                pass  # Function exists but different error

# Try getting the subnet data via RPC calls
print("\n=== Trying RPC state_getStorage ===")
import hashlib

# Build storage keys manually
# SubtensorModule + SubnetTao + netuid
def storage_key(pallet, storage, params=None):
    """Build a Substrate storage key."""
    # Method name hash
    m = hashlib.blake2b(digest_size=16)
    m.update(pallet.encode())
    pallet_hash = m.hexdigest()
    
    m = hashlib.blake2b(digest_size=16)
    m.update(storage.encode())
    storage_hash = m.hexdigest()
    
    key = "0x" + pallet_hash + storage_hash
    if params is not None:
        # Encode params as SCALE
        for p in params:
            if isinstance(p, int):
                # SCALE encode as u16
                key += format(p & 0xffff, '04x')
    return key

for netuid in [0, 1, 2, 3, 9, 14]:
    key = storage_key("SubtensorModule", "SubnetTao", [netuid])
    try:
        result = substrate.rpc_request("state_getStorage", [key])
        if result.get('result'):
            print(f"  Subnet {netuid} SubnetTao raw: {result['result'][:40]}...")
        else:
            print(f"  Subnet {netuid} SubnetTao: null")
    except Exception as e:
        print(f"  Subnet {netuid} SubnetTao: {e}")

# Try using btcli equivalent approach — query subtensor with proper SCALE encoding
print("\n=== Trying query_map for SubnetTao ===")
try:
    result = substrate.query_map("SubtensorModule", "SubnetTao", [0])
    count = 0
    for record in result:
        print(f"  SubnetTao record: key={record[0].value if hasattr(record[0], 'value') else record[0]}, value={record[1].value if hasattr(record[1], 'value') else record[1]}")
        count += 1
        if count > 10:
            break
except Exception as e:
    print(f"  query_map SubnetTao: {e}")

# Try querying the Emission data more carefully — we know it works
print("\n=== Re-checking Emission data for specific subnets ===")
for netuid in [1, 2, 3, 9, 14, 19, 20, 21]:
    try:
        result = substrate.query("SubtensorModule", "Emission", [netuid])
        if result:
            val = result.value
            print(f"  Subnet {netuid} Emission: {val}")
    except Exception as e:
        print(f"  Subnet {netuid} Emission error: {e}")

# Try getting the NetworkName more carefully
print("\n=== Checking NetworkName ===")
for netuid in [0, 1, 2, 3, 4, 8, 9, 14, 19, 20, 21]:
    try:
        result = substrate.query("SubtensorModule", "NetworkName", [netuid])
        if result:
            val = result.value
            print(f"  Subnet {netuid} Name: {val}")
    except Exception as e:
        print(f"  Subnet {netuid} Name error: {e}")

# Try getting NetworkN
print("\n=== Checking NetworkN (neuron counts) ===")
for netuid in [0, 1, 2, 3, 9, 14, 19, 20, 21]:
    try:
        result = substrate.query("SubtensorModule", "NetworkN", [netuid])
        if result:
            val = result.value
            print(f"  Subnet {netuid} Neurons: {val}")
    except Exception as e:
        print(f"  Subnet {netuid} NetworkN error: {e}")

print("\nDone.")