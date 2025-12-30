"""
Relayer-related utilities for Eureka IBC tests.
"""

import json
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING

import grpc

if TYPE_CHECKING:
    from typing import Any

    # Forward reference to avoid circular import
    EurekaTestContext = dict[str, Any]


def generate_relayer_config(
    context: "EurekaTestContext",
    base_path: Path,
    eureka_dir: Path,
    signer_eth_address: str,
    eth_chain_id: str = "31337",
    cosmos_chain_id: str | None = None,
) -> Path:
    """
    Generate a relayer config JSON file.

    Args:
        context: The test context dictionary containing cronos, geth, and contracts
        base_path: Base path where the relayer folder will be created
        eureka_dir: Path to the solidity-ibc-eureka directory
        signer_eth_address: Ethereum address of the signer (will be converted to
            Cosmos bech32 format)
        eth_chain_id: Ethereum chain ID (default: "31337")
        cosmos_chain_id: Cosmos chain ID (if None, will be fetched from cronos)

    Returns:
        Path to the generated config file
    """
    from pystarport import ports

    from integration_tests.utils import CRONOS_ADDRESS_PREFIX, eth_to_bech32

    cronos = context["cronos"]
    geth = context["geth"]
    contracts = context["contracts"]

    # Convert Ethereum address to Cosmos bech32 address
    signer_address = eth_to_bech32(signer_eth_address, CRONOS_ADDRESS_PREFIX)

    # Get chain IDs and ensure they are strings
    eth_chain_id_str = str(eth_chain_id)
    if cosmos_chain_id is None:
        cosmos_chain_id = cronos.cosmos_cli(0).chain_id
    cosmos_chain_id_str = str(cosmos_chain_id)

    # Get RPC URLs
    tm_rpc_port = ports.rpc_port(cronos.base_port(0))
    tm_rpc_url = f"http://0.0.0.0:{tm_rpc_port}"

    eth_rpc_url = geth.w3.provider.endpoint_uri

    # Get ICS26 router address
    ics26_address = contracts["ics26Router"]

    # SP1 programs paths (relative to eureka_dir)
    sp1_programs_base = (
        eureka_dir
        / "programs/sp1-programs/target/elf-compilation"
        / "riscv32im-succinct-zkvm-elf/release"
    )

    config = {
        "modules": [
            {
                "name": "eth_to_cosmos_compat",
                "src_chain": eth_chain_id_str,
                "dst_chain": cosmos_chain_id_str,
                "config": {
                    "tm_rpc_url": tm_rpc_url,
                    "ics26_address": ics26_address,
                    "eth_rpc_url": eth_rpc_url,
                    "eth_beacon_api_url": "",
                    "signer_address": signer_address,
                    "mock": True,
                },
            },
            {
                "name": "cosmos_to_eth",
                "src_chain": cosmos_chain_id_str,
                "dst_chain": eth_chain_id_str,
                "config": {
                    "tm_rpc_url": tm_rpc_url,
                    "ics26_address": ics26_address,
                    "eth_rpc_url": eth_rpc_url,
                    "sp1_prover": {
                        "type": "mock",
                    },
                    "sp1_programs": {
                        "update_client": str(
                            sp1_programs_base / "sp1-ics07-tendermint-update-client"
                        ),
                        "membership": str(
                            sp1_programs_base / "sp1-ics07-tendermint-membership"
                        ),
                        "update_client_and_membership": str(
                            sp1_programs_base / "sp1-ics07-tendermint-uc-and-membership"
                        ),
                        "misbehaviour": str(
                            sp1_programs_base / "sp1-ics07-tendermint-misbehaviour"
                        ),
                    },
                },
            },
        ],
        "server": {
            "address": "127.0.0.1",
            "port": 3000,
        },
        "observability": {
            "level": "info",
            "use_otel": False,
            "service_name": "ibc-eureka-relayer",
        },
    }

    # Create relayer directory
    relayer_dir = base_path / "relayer"
    relayer_dir.mkdir(parents=True, exist_ok=True)

    # Write config file
    config_path = relayer_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    return config_path


def start_relayer(config_path: Path, binary_path: str) -> subprocess.Popen:
    """
    Start the relayer with the given config file.

    Args:
        config_path: Path to the relayer config JSON file
        binary_path: Path to the relayer binary (default: ~/.cargo/bin/relayer)

    Returns:
        subprocess.Popen: The process object for the started relayer

    Raises:
        FileNotFoundError: If the config file or binary doesn't exist
        subprocess.SubprocessError: If the relayer fails to start
    """
    import sys

    # Read and print config
    config_content = config_path.read_text()
    print(f"Starting relayer with config:\n{config_content}")

    # Start the relayer command in the background
    # Redirect stdout and stderr to console (matching Go behavior)
    cmd = subprocess.Popen(
        [binary_path, "start", "--config", str(config_path)],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    # Wait for the relayer to start
    time.sleep(9)

    return cmd


def get_grpc_client(addr: str):
    """
    Create a gRPC client for the relayer service.

    Args:
        addr: The gRPC server address (e.g., "127.0.0.1:3000")

    Returns:
        RelayerServiceStub: The gRPC client stub for the relayer service

    Raises:
        Exception: If the connection fails
    """
    import importlib.util
    import sys
    from pathlib import Path

    # Import the generated gRPC stub directly from the relayer directory
    # We need to import it as a module to avoid conflicts with this file name
    relayer_dir = Path(__file__).parent / "relayer"
    relayer_pb2_grpc_path = relayer_dir / "relayer_pb2_grpc.py"
    relayer_pb2_path = relayer_dir / "relayer_pb2.py"

    # Load relayer_pb2 first since relayer_pb2_grpc imports it
    spec_pb2 = importlib.util.spec_from_file_location("relayer_pb2", relayer_pb2_path)
    if spec_pb2 is None or spec_pb2.loader is None:
        raise ImportError(f"Failed to load relayer_pb2 from {relayer_pb2_path}")

    relayer_pb2 = importlib.util.module_from_spec(spec_pb2)

    # Create a fake 'relayer' package in sys.modules so the import works
    # The generated files use 'from relayer import relayer_pb2'
    if "relayer" not in sys.modules:
        # Create a module object for the 'relayer' package
        relayer_pkg = type(sys)("relayer")
        sys.modules["relayer"] = relayer_pkg

    # Add relayer_pb2 to the relayer package
    sys.modules["relayer.relayer_pb2"] = relayer_pb2
    spec_pb2.loader.exec_module(relayer_pb2)

    # Now load relayer_pb2_grpc
    spec_grpc = importlib.util.spec_from_file_location(
        "relayer_pb2_grpc", relayer_pb2_grpc_path
    )
    if spec_grpc is None or spec_grpc.loader is None:
        raise ImportError(
            f"Failed to load relayer_pb2_grpc from {relayer_pb2_grpc_path}"
        )

    relayer_pb2_grpc = importlib.util.module_from_spec(spec_grpc)
    spec_grpc.loader.exec_module(relayer_pb2_grpc)

    # Create an insecure channel (no TLS, matching Go's
    # insecure.NewCredentials())
    channel = grpc.insecure_channel(addr)

    # Create and return the client stub
    return relayer_pb2_grpc.RelayerServiceStub(channel)


def get_relayer_pb2():
    """
    Get the relayer_pb2 module for creating request objects.

    Returns:
        The relayer_pb2 module containing message definitions

    Raises:
        ImportError: If the module cannot be loaded
    """
    import importlib.util
    import sys
    from pathlib import Path

    # Import relayer_pb2 to get CreateClientRequest
    relayer_dir = Path(__file__).parent / "relayer"
    relayer_pb2_path = relayer_dir / "relayer_pb2.py"

    spec_pb2 = importlib.util.spec_from_file_location("relayer_pb2", relayer_pb2_path)
    if spec_pb2 is None or spec_pb2.loader is None:
        raise ImportError(f"Failed to load relayer_pb2 from {relayer_pb2_path}")

    relayer_pb2 = importlib.util.module_from_spec(spec_pb2)
    if "relayer" not in sys.modules:
        sys.modules["relayer"] = type(sys)("relayer")
    sys.modules["relayer.relayer_pb2"] = relayer_pb2
    spec_pb2.loader.exec_module(relayer_pb2)

    return relayer_pb2


def create_client(
    relayer_client,
    cosmos_chain_id: str,
    eth_chain_id: str,
    verifier_address: str,
    zk_algorithm: str = "groth16",
):
    """
    Call CreateClient on the relayer service.

    Args:
        relayer_client: The gRPC client stub (from get_grpc_client)
        cosmos_chain_id: Source chain ID (Cosmos)
        eth_chain_id: Destination chain ID (Ethereum)
        verifier_address: SP1 verifier address
        zk_algorithm: ZK algorithm to use (default: "groth16")

    Returns:
        The CreateClient response from the relayer

    Raises:
        Exception: If the CreateClient call fails
    """
    relayer_pb2 = get_relayer_pb2()

    # Prepare CreateClient request
    create_client_request = relayer_pb2.CreateClientRequest(
        src_chain=cosmos_chain_id,
        dst_chain=eth_chain_id,
        parameters={
            "sp1_verifier": verifier_address,
            "zk_algorithm": zk_algorithm,
        },
    )

    # Call CreateClient
    print("\n=== Calling CreateClient ===")
    print(f"Request: src_chain={cosmos_chain_id}, dst_chain={eth_chain_id}")
    print(f"Parameters: {create_client_request.parameters}")

    response = relayer_client.CreateClient(create_client_request)

    print("\n=== CreateClient Response ===")
    print(f"Tx length: {len(response.tx)} bytes")

    assert len(response.tx) > 0, "CreateClient response tx should not be empty"
    assert (
        response.address == ""
    ), f"CreateClient response address should be empty, got: {response.address}"

    return response


def relay_by_tx(
    relayer_client,
    src_chain: str,
    dst_chain: str,
    source_tx_ids: list[bytes],
    src_client_id: str,
    dst_client_id: str,
):
    """
    Call RelayByTx on the relayer service.

    Args:
        relayer_client: The gRPC client stub (from get_grpc_client)
        src_chain: Source chain ID
        dst_chain: Destination chain ID
        source_tx_ids: List of source transaction hash bytes
        src_client_id: Source client ID
        dst_client_id: Destination client ID

    Returns:
        The RelayByTx response from the relayer

    Raises:
        Exception: If the RelayByTx call fails
    """
    relayer_pb2 = get_relayer_pb2()

    # Prepare RelayByTx request
    relay_request = relayer_pb2.RelayByTxRequest(
        src_chain=src_chain,
        dst_chain=dst_chain,
        source_tx_ids=source_tx_ids,
        timeout_tx_ids=[],
        src_client_id=src_client_id,
        dst_client_id=dst_client_id,
        src_packet_sequences=[],
        dst_packet_sequences=[],
    )

    # Call RelayByTx
    print("\n=== Calling RelayByTx ===")
    print(f"Request: src_chain={src_chain}, dst_chain={dst_chain}")
    print(f"Source tx IDs: {[tx_id.hex() for tx_id in source_tx_ids]}")
    print(f"Client IDs: {src_client_id} -> {dst_client_id}")

    response = relayer_client.RelayByTx(relay_request)

    print("\n=== RelayByTx Response ===")
    print(f"Tx length: {len(response.tx)} bytes")
    print(f"Address: {response.address}")

    assert len(response.tx) > 0, "RelayByTx response tx should not be empty"
    # Note: address is empty for acknowledgement relays to Cosmos,
    # but non-empty for packet relays to Ethereum

    return response
