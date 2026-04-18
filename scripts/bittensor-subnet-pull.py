#!/usr/bin/env python3
"""
Bittensor Subnet Data Puller — Queries subtensor RPC for live subnet pool data.
Pulls alpha/TAO reserves, computes prices, emission shares, and net flow indicators.
"""

import json
import time
from substrateinterface import SubstrateInterface

# Known Bittensor RPC endpoints
RPC_ENDPOINTS = [
    "wss://entrypoint-finney.opentensor.ai:443",
    "wss://finney.opentensor.ai:443",
]

def connect_subtensor():
    """Connect to Bittensor blockchain via RPC."""
    for endpoint in RPC_ENDPOINTS:
        try:
            print(f"Trying {endpoint}...")
            substrate = SubstrateInterface(
                url=endpoint,
                auto_reconnect=True,
            )
            print(f"Connected to {endpoint}")
            return substrate
        except Exception as e:
            print(f"Failed: {e}")
            continue
    raise RuntimeError("Could not connect to any Bittensor RPC endpoint")

def get_total_subnets(substrate):
    """Get the total number of subnets."""
    try:
        result = substrate.query(
            module="SubtensorModule",
            storage_function="TotalNetworks",
        )
        return result.value if result else 0
    except Exception as e:
        print(f"Error getting total subnets: {e}")
        return 0

def get_subnet_info(substrate, netuid):
    """Get subnet pool data for a given netuid."""
    try:
        # Get subnet name
        name_result = substrate.query(
            module="SubtensorModule",
            storage_function="NetworkName",
            params=[netuid],
        )
        name = name_result.value if name_result else f"Unknown-{netuid}"

        # Get TAO reserves (tau_in)
        tao_reserve_result = substrate.query(
            module="SubtensorModule",
            storage_function="EmissionValues",  # fallback
            params=[netuid],
        )

        # Try getting pool data via SubnetEmission
        # Alpha outstanding
        alpha_outstanding_result = substrate.query(
            module="SubtensorModule",
            storage_function="AlphaOutstanding",
            params=[netuid],
        )

        # Try different storage functions for pool reserves
        # These are the Dynamic TAO pool storage items
        pool_data = {}

        # Try to get subnet state from SubnetInfo or similar
        try:
            subnet_data = substrate.query(
                module="SubtensorModule",
                storage_function="SubnetInfo",
                params=[netuid],
            )
            if subnet_data:
                pool_data['subnet_info'] = str(subnet_data.value)
        except:
            pass

        # Try getting the subnet's dynamic pool data
        try:
            tao_reserve = substrate.query(
                module="SubtensorModule",
                storage_function="TaoReserve",
                params=[netuid],
            )
            pool_data['tao_reserve'] = tao_reserve.value if tao_reserve else 0
        except:
            pool_data['tao_reserve'] = 'N/A'

        try:
            alpha_reserve = substrate.query(
                module="SubtensorModule",
                storage_function="AlphaReserve",
                params=[netuid],
            )
            pool_data['alpha_reserve'] = alpha_reserve.value if alpha_reserve else 0
        except:
            pool_data['alpha_reserve'] = 'N/A'

        # Get emission for this subnet
        try:
            emission_result = substrate.query(
                module="SubtensorModule",
                storage_function="EmissionValues",
                params=[netuid],
            )
            pool_data['emission'] = emission_result.value if emission_result else 0
        except:
            pool_data['emission'] = 'N/A'

        # Get subnet owner
        try:
            owner_result = substrate.query(
                module="SubtensorModule",
                storage_function="SubnetOwner",
                params=[netuid],
            )
            pool_data['owner'] = owner_result.value if owner_result else 'N/A'
        except:
            pool_data['owner'] = 'N/A'

        # Get neuron counts (miners + validators)
        try:
            n_result = substrate.query(
                module="SubtensorModule",
                storage_function="NetworkN",
                params=[netuid],
            )
            pool_data['neuron_count'] = n_result.value if n_result else 0
        except:
            pool_data['neuron_count'] = 'N/A'

        # Get subnet moving price (used in old emission model, still tracked)
        try:
            moving_price = substrate.query(
                module="SubtensorModule",
                storage_function="MovingPrice",
                params=[netuid],
            )
            pool_data['moving_price'] = moving_price.value if moving_price else 0
        except:
            pool_data['moving_price'] = 'N/A'

        # Alpha outstanding
        if alpha_outstanding_result:
            pool_data['alpha_outstanding'] = alpha_outstanding_result.value
        else:
            pool_data['alpha_outstanding'] = 'N/A'

        pool_data['netuid'] = netuid
        pool_data['name'] = name

        return pool_data

    except Exception as e:
        return {'netuid': netuid, 'name': f'Error-{netuid}', 'error': str(e)}

def get_subnet_list(substrate):
    """Get list of all registered subnets."""
    try:
        result = substrate.query(
            module="SubtensorModule",
            storage_function="NetworksAdded",
        )
        if result:
            # This returns a map, iterate to find which netuids are registered
            return result
        return None
    except Exception as e:
        print(f"Error getting subnet list: {e}")
        return None

def main():
    print("=" * 60)
    print("BITTENSOR SUBNET DATA PULLER")
    print("=" * 60)

    substrate = connect_subtensor()

    # First, discover what storage functions are available
    print("\n--- Querying available SubtensorModule storage functions ---")
    try:
        metadata = substrate.get_metadata()
        modules = metadata.get('metadata', {})
        # Just list what we can
    except Exception as e:
        print(f"Metadata query: {e}")

    # Get total number of subnets
    total = get_total_subnets(substrate)
    print(f"\nTotal registered subnets: {total}")

    # Try to get the subnet list
    print("\nQuerying subnet registrations...")
    subnet_list = get_subnet_list(substrate)
    if subnet_list:
        print(f"Subnet list type: {type(subnet_list)}")
        print(f"Subnet list value: {subnet_list}")

    # Query each subnet individually (0 to max expected)
    # In practice there are ~60-100+ subnets
    MAX_NETUID = 80

    results = []
    print(f"\n--- Querying subnets 0-{MAX_NETUID} ---")
    for netuid in range(MAX_NETUID + 1):
        print(f"Querying subnet {netuid}...", end=" ")
        info = get_subnet_info(substrate, netuid)
        if info.get('name') and 'Error' not in str(info.get('name', '')):
            print(f"Name: {info.get('name')}")
            results.append(info)
        else:
            print("not found or error")

    # Save raw results
    output_path = "/root/.openclaw/workspace/research/subnet-raw-data.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nRaw data saved to {output_path}")

    # Print summary table
    print("\n" + "=" * 120)
    print(f"{'Netuid':<8} {'Name':<20} {'TAO Reserve':<15} {'Alpha Reserve':<15} {'Alpha Outstanding':<18} {'Emission':<12} {'Neurons':<10}")
    print("-" * 120)
    for r in results:
        netuid = r.get('netuid', '?')
        name = r.get('name', '?')
        tao = r.get('tao_reserve', 'N/A')
        alpha = r.get('alpha_reserve', 'N/A')
        alpha_out = r.get('alpha_outstanding', 'N/A')
        emission = r.get('emission', 'N/A')
        neurons = r.get('neuron_count', 'N/A')
        print(f"{netuid:<8} {name:<20} {str(tao):<15} {str(alpha):<15} {str(alpha_out):<18} {str(emission):<12} {str(neurons):<10}")

if __name__ == "__main__":
    main()