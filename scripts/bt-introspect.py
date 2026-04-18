#!/usr/bin/env python3
"""
Introspect Bittensor subtensor pallet to find actual storage function names.
"""

from substrateinterface import SubstrateInterface

RPC = "wss://entrypoint-finney.opentensor.ai:443"

substrate = SubstrateInterface(url=RPC, auto_reconnect=True)

# Get pallet metadata
metadata = substrate.metadata

# Find SubtensorModule or equivalent
pallets = metadata.pallets if hasattr(metadata, 'pallets') else {}

# Try to iterate pallets
print("Looking for Bittensor pallets...")

if hasattr(metadata, '__dict__'):
    for key in dir(metadata):
        if not key.startswith('_'):
            try:
                val = getattr(metadata, key)
                if 'subtensor' in str(key).lower() or 'Subtensor' in str(key):
                    print(f"Found: {key} = {type(val)}")
            except:
                pass

# Try direct query approach - list all storage functions in SubtensorModule
print("\n--- Trying to list storage functions ---")
try:
    # substrate.query_module can list storage functions
    for pallet_name in ['SubtensorModule', 'Subtensor', 'SubtensorRuntime']:
        try:
            pallet = substrate.metadata.get_pallet(pallet_name)
            if pallet:
                print(f"\nPallet: {pallet_name}")
                if hasattr(pallet, 'storage_functions'):
                    for name, func in pallet.storage_functions.items():
                        print(f"  {name}: {getattr(func, 'params', 'N/A')}")
                break
        except Exception as e:
            print(f"  {pallet_name}: {e}")
except Exception as e:
    print(f"Error: {e}")

# Alternative: try known storage function patterns from subtensor source
print("\n--- Trying known Dynamic TAO storage functions ---")
known_functions = [
    # Pool reserves
    ("TaoReserve", [0]),
    ("AlphaReserve", [0]),
    ("AlphaOutstanding", [0]),
    # Network info
    ("NetworkName", [0]),
    ("NetworkN", [0]),
    ("NetworksAdded", [0]),
    ("TotalNetworks", []),
    # Dynamic TAO
    ("SubnetTao", [0]),
    ("SubnetAlphaIn", [0]),
    ("SubnetAlphaOut", [0]),
    ("SubnetInfo", [0]),
    ("PoolInfo", [0]),
    # Emission
    ("EmissionValues", [0]),
    ("Emission", [0]),
    ("SubnetEmission", [0]),
    # Price
    ("MovingPrice", [0]),
    ("SubnetPrice", [0]),
    ("AlphaPrice", [0]),
    # Owner
    ("SubnetOwner", [0]),
    ("Owner", [0]),
    # Flow
    ("TaoInflow", [0]),
    ("TaoOutflow", [0]),
    ("NetFlow", [0]),
    # Other
    ("IsNetwork", [0]),
    ("NetworkRegistered", [0]),
    ("N", [0]),
    ("SubnetName", [0]),
]

for func_name, params in known_functions:
    for module in ['SubtensorModule', 'Subtensor']:
        try:
            result = substrate.query(
                module=module,
                storage_function=func_name,
                params=params,
            )
            if result is not None:
                print(f"  FOUND: {module}.{func_name}({params}) = {result.value}")
                break
        except Exception as e:
            err_str = str(e)
            if 'not found' in err_str.lower() or 'not exist' in err_str.lower():
                continue
            else:
                # Different error means the function might exist but params are wrong
                if 'parameter' in err_str.lower() or 'param' in err_str.lower():
                    print(f"  EXISTS (wrong params): {module}.{func_name} -> {err_str[:100]}")
                elif 'type' in err_str.lower():
                    print(f"  EXISTS (type error): {module}.{func_name} -> {err_str[:100]}")

print("\nDone.")