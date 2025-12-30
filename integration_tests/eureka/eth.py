"""
Ethereum-related utilities for Eureka IBC tests.
"""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Optional, TypedDict

from eth_account import Account
from eth_utils import keccak as eth_keccak256
from eth_utils import to_checksum_address
from web3 import Web3
from web3._utils.transactions import fill_nonce, fill_transaction_defaults

# Import utilities needed for funding
from integration_tests.utils import fund_acc, get_contract, send_transaction

if TYPE_CHECKING:
    from typing import Any

    # Forward reference to avoid circular import
    EurekaTestContext = dict[str, Any]


class EurekaContracts(TypedDict):
    """Deployed IBC Eureka contract addresses"""

    verifierPlonk: str
    verifierGroth16: str
    verifierMock: str
    ics26Router: str
    ics20Transfer: str
    ics27Gmp: str
    erc20: str


def get_eth_contracts_from_deploy_output(stdout: str) -> EurekaContracts:
    """
    Extract deployed contract addresses from forge script output.

    This function follows the same pattern as the Go implementation:
    - Finds the "== Return ==" marker
    - Extracts the JSON part using regex
    - Parses and validates the contract addresses

    Args:
        stdout: The stdout output from the forge script

    Returns:
        EurekaContracts: Dictionary containing all deployed contract addresses

    Raises:
        ValueError: If the output format is invalid or required contracts are missing
    """
    # Remove everything above the JSON part
    cut_off = "== Return =="
    cutoff_index = stdout.find(cut_off)
    if cutoff_index == -1:
        raise ValueError(f"Could not find '{cut_off}' marker in output")
    stdout = stdout[cutoff_index + len(cut_off) :]

    # Extract the JSON part using regex
    json_match = re.search(r"\{.*\}", stdout, re.DOTALL)
    if not json_match:
        raise ValueError("Could not find JSON in output")
    json_part = json_match.group(0)

    # Replace escaped quotes and trim surrounding quotes
    json_part = json_part.replace('\\"', '"')
    json_part = json_part.strip('"')

    # Parse JSON
    try:
        embedded_contracts = json.loads(json_part)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {e}") from e

    # Validate all required contracts are present
    required_fields = [
        "erc20",
        "ics20Transfer",
        "ics27Gmp",
        "verifierPlonk",
        "verifierGroth16",
        "verifierMock",
        "ics26Router",
    ]

    missing_fields = [
        field for field in required_fields if not embedded_contracts.get(field)
    ]
    if missing_fields:
        raise ValueError(
            f"One or more contracts missing: {missing_fields}. "
            f"Found contracts: {list(embedded_contracts.keys())}"
        )

    # Convert to EurekaContracts TypedDict with checksum addresses
    return EurekaContracts(
        verifierPlonk=to_checksum_address(embedded_contracts["verifierPlonk"]),
        verifierGroth16=to_checksum_address(embedded_contracts["verifierGroth16"]),
        verifierMock=to_checksum_address(embedded_contracts["verifierMock"]),
        ics26Router=to_checksum_address(embedded_contracts["ics26Router"]),
        ics20Transfer=to_checksum_address(embedded_contracts["ics20Transfer"]),
        ics27Gmp=to_checksum_address(embedded_contracts["ics27Gmp"]),
        erc20=to_checksum_address(embedded_contracts["erc20"]),
    )


def deploy_ibc_contracts_to_eth(
    context: "EurekaTestContext",
    eureka_dir: Path,
    keys: dict,
    addrs: dict,
) -> None:
    """
    Deploy IBC Eureka contracts to Ethereum using forge script.

    Args:
        context: The test context dictionary that will be updated with
            deployed contracts
        eureka_dir: Path to the solidity-ibc-eureka directory
        keys: Dictionary containing validator keys (needs "validator" key)
        addrs: Dictionary containing validator addresses (needs "validator" key)
    """
    geth = context["geth"]
    geth_rpc_url = geth.w3.provider.endpoint_uri
    deployer_key = keys["validator"]
    faucet_address = addrs["validator"]

    script_path = eureka_dir / "scripts/E2ETestDeploy.s.sol"

    # Run the forge script
    cmd = [
        "forge",
        "script",
        "--rpc-url",
        geth_rpc_url,
        "--private-key",
        deployer_key.hex(),
        "--broadcast",
        "--non-interactive",
        "--with-gas-price",
        "1000000000",
        "-vvvv",
        str(script_path),
    ]

    env = os.environ.copy()
    env["E2E_FAUCET_ADDRESS"] = faucet_address

    print(f"Running forge script: {' '.join(cmd)}...")
    result = subprocess.run(
        cmd,
        cwd=eureka_dir,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Forge script failed: {result.stderr}"
    contracts = get_eth_contracts_from_deploy_output(result.stdout)
    print(f"Deployed contracts: {contracts}")
    context["contracts"] = contracts


def broadcast_tx(
    w3: Web3,
    user_key: bytes,
    gas_limit: int,
    to_address: Optional[str],
    tx_bytes: bytes,
) -> dict:
    account = Account.from_key(user_key)
    tx = {
        "from": account.address,
        "to": to_address,
        "value": 0,
        "gas": gas_limit,
        "data": tx_bytes,
    }

    # Fill transaction defaults (chainId, gasPrice, etc.)
    tx = fill_transaction_defaults(w3, tx)

    # Fill nonce
    tx = fill_nonce(w3, tx)

    # Sign transaction
    signed_tx = account.sign_transaction(tx)

    # Send transaction
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    # Wait for receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    # Check transaction status (1 = success, 0 = failure)
    if receipt.status == 0:
        # Try to get revert reason if available
        try:
            # Call the transaction to get revert reason
            tx = w3.eth.get_transaction(tx_hash)
            result = w3.eth.call(
                {
                    "from": tx["from"],
                    "to": tx["to"],
                    "data": tx["input"],
                    "gas": tx["gas"],
                    "gasPrice": tx.get("gasPrice") or tx.get("maxFeePerGas"),
                },
                block_identifier=receipt.blockNumber - 1,
            )
        except Exception as e:
            error_msg = f"tx failed: {receipt}. Could not get revert reason: {e}"
        else:
            error_msg = f"tx failed: {receipt}"

        # Try to get trace for more details
        try:
            trace = w3.provider.make_request("debug_traceTransaction", [tx_hash.hex()])
            if trace and "result" in trace:
                error_msg += f"\nTrace: {trace['result']}"
        except Exception:
            pass

        assert False, error_msg

    return receipt


def fund_user_account_with_erc20(
    w3: Web3,
    user_account: Account,
    erc20_contract_address: str,
    contract_abi_path: Path,
    validator_address: str,
    validator_key: bytes,
    amount: int = 100000000000000000000000000,
):

    # Get ERC20 contract
    erc20_contract = get_contract(w3, erc20_contract_address, contract_abi_path)
    assert erc20_contract is not None

    # Fund account with native tokens (for gas)
    fund_acc(w3, user_account)

    # Transfer ERC20 tokens from validator to user account
    transfer_tx = erc20_contract.functions.transfer(
        user_account.address, amount
    ).build_transaction({"from": validator_address})
    tx_receipt = send_transaction(w3, transfer_tx, key=validator_key)
    assert tx_receipt.status == 1

    # Verify the user account has received the ERC20 tokens
    user_balance = erc20_contract.caller.balanceOf(user_account.address)
    assert user_balance == amount, f"Expected balance {amount}, got {user_balance}"

    return tx_receipt


def add_client_and_counterparty(
    context: "EurekaTestContext",
    eureka_dir: Path,
    client_id: str,
    counterparty_client_id: str,
    sp1_ics07_address: str,
    validator_key: bytes,
    validator_address: str,
) -> None:
    """
    Add client and counterparty on EVM via ICS26Router.

    This function calls the AddClient function on the ICS26Router contract
    to register a client with its counterparty information.

    Args:
        context: The test context dictionary containing contracts and geth instance
        eureka_dir: Path to the solidity-ibc-eureka directory (for ABI file)
        client_id: The client ID to register (e.g., "solidity-0")
        counterparty_client_id: The counterparty client ID (e.g., "08-wasm-0")
        sp1_ics07_address: The address of the SP1 ICS07 light client contract
        validator_key: The private key of the validator/deployer
        validator_address: The address of the validator/deployer

    Raises:
        AssertionError: If the transaction fails or event validation fails
    """
    geth = context["geth"]
    w3 = geth.w3
    contracts = context["contracts"]
    assert contracts is not None

    # Get ICS26Router contract
    ics26_abi_path = eureka_dir / "abi" / "ICS26Router.json"
    # The ABI file is just an array, not a dict with "abi" key
    abi_data = json.loads(ics26_abi_path.read_text())
    if isinstance(abi_data, list):
        # It's just the ABI array
        abi = abi_data
    else:
        # It's a dict with "abi" key
        abi = abi_data["abi"]
    ics26_contract = w3.eth.contract(address=contracts["ics26Router"], abi=abi)

    # Prepare counterparty info
    # Merkle prefix: [b"ibc", b""] - matching ibcexported.StoreKey
    merkle_prefix = [b"ibc", b""]
    counterparty_info = (counterparty_client_id, merkle_prefix)

    # Call addClient function
    print("=== Add client and counterparty on EVM ===")
    print(f"Client ID: {client_id}")
    print(f"Counterparty Client ID: {counterparty_client_id}")
    print(f"SP1 ICS07 Address: {sp1_ics07_address}")

    add_client_tx = ics26_contract.functions.addClient(
        client_id, counterparty_info, sp1_ics07_address
    ).build_transaction({"from": validator_address})

    tx_receipt = send_transaction(w3, add_client_tx, key=validator_key)
    assert tx_receipt.status == 1, f"Transaction failed: {tx_receipt}"

    # Parse ICS02ClientAdded event from receipt
    events = ics26_contract.events.ICS02ClientAdded().process_receipt(tx_receipt)
    assert len(events) > 0, "ICS02ClientAdded event not found in receipt"

    event = events[0]
    event_args = event["args"]

    # Verify event values
    assert (
        event_args["clientId"] == client_id
    ), f"Expected clientId {client_id}, got {event_args['clientId']}"
    # counterpartyInfo is a tuple struct decoded as AttributeDict with named fields
    counterparty_info = event_args["counterpartyInfo"]
    assert counterparty_info["clientId"] == counterparty_client_id, (
        f"Expected counterparty clientId {counterparty_client_id}, "
        f"got {counterparty_info['clientId']}"
    )

    print(
        f"Successfully added client {client_id} with counterparty "
        f"{counterparty_client_id}"
    )


def approve_and_send_transfer_from_ethereum(
    w3: Web3,
    eureka_dir: Path,
    contracts: EurekaContracts,
    ibc_erc20_address: str,
    ethereum_user_address: str,
    cosmos_user_address: str,
    transfer_amount: int,
    source_client_id: str,
    user_key: bytes,
    timeout_timestamp: int,
    memo: str = "",
) -> bytes:
    """
    Approve ICS20Transfer contract and send transfer from Ethereum to Cosmos.

    This function:
    1. Approves the ICS20Transfer contract to spend IBCERC20 tokens
    2. Sends a transfer packet from Ethereum to Cosmos
    3. Verifies balances on Ethereum are zero after transfer

    Args:
        w3: Web3 instance
        eureka_dir: Path to the eureka directory containing ABIs
        contracts: Dictionary of deployed contract addresses
        ibc_erc20_address: The IBCERC20 contract address
        ethereum_user_address: The Ethereum user address
        cosmos_user_address: The Cosmos receiver address (bech32 format)
        transfer_amount: The amount to transfer
        source_client_id: The source client ID (e.g., "solidity-0")
        user_key: The private key for signing transactions
        timeout_timestamp: Timeout timestamp in unix seconds
        memo: Optional memo string (default: "")

    Returns:
        The transaction hash as bytes

    Raises:
        AssertionError: If approval or transfer fails, or if balances are incorrect
    """
    from integration_tests.utils import send_transaction

    # Get IBCERC20 contract
    ibc_erc20_abi_path = eureka_dir / "abi" / "IBCERC20.json"
    ibc_erc20_abi_data = json.loads(ibc_erc20_abi_path.read_text())
    if isinstance(ibc_erc20_abi_data, list):
        ibc_erc20_abi = ibc_erc20_abi_data
    else:
        ibc_erc20_abi = ibc_erc20_abi_data["abi"]
    ibc_erc20_contract = w3.eth.contract(address=ibc_erc20_address, abi=ibc_erc20_abi)

    # Get ICS20Transfer contract
    ics20_abi_path = eureka_dir / "abi" / "ICS20Transfer.json"
    ics20_abi_data = json.loads(ics20_abi_path.read_text())
    if isinstance(ics20_abi_data, list):
        ics20_abi = ics20_abi_data
    else:
        ics20_abi = ics20_abi_data["abi"]
    ics20_contract = w3.eth.contract(address=contracts["ics20Transfer"], abi=ics20_abi)

    # Approve the ICS20Transfer contract to spend IBCERC20 tokens
    print("=== Approve ICS20Transfer contract to spend IBCERC20 tokens ===")
    approve_tx = ibc_erc20_contract.functions.approve(
        contracts["ics20Transfer"], transfer_amount
    ).build_transaction({"from": ethereum_user_address})
    approve_receipt = send_transaction(w3, approve_tx, key=user_key)
    assert approve_receipt.status == 1, "Approve transaction failed"

    # Verify allowance
    allowance = ibc_erc20_contract.functions.allowance(
        ethereum_user_address, contracts["ics20Transfer"]
    ).call()
    assert (
        allowance == transfer_amount
    ), f"Expected allowance {transfer_amount}, got {allowance}"

    # Send transfer from Ethereum to Cosmos
    print("=== Send transfer from Ethereum to Cosmos ===")
    # SendTransfer takes a struct with: denom, amount, receiver, sourceClient, destPort, timeoutTimestamp, memo
    dest_port = "transfer"  # Standard IBC transfer port
    send_transfer_tx = ics20_contract.functions.sendTransfer(
        (
            ibc_erc20_address,  # denom (address)
            transfer_amount,  # amount (uint256)
            cosmos_user_address,  # receiver (string)
            source_client_id,  # sourceClient (string)
            dest_port,  # destPort (string)
            timeout_timestamp,  # timeoutTimestamp (uint64)
            memo,  # memo (string)
        )
    ).build_transaction({"from": ethereum_user_address})
    send_receipt = send_transaction(w3, send_transfer_tx, key=user_key)
    assert send_receipt.status == 1, "SendTransfer transaction failed"

    # Get transaction hash as bytes
    tx_hash = send_receipt["transactionHash"]
    if hasattr(tx_hash, "hex"):
        tx_hash_hex = tx_hash.hex()
    else:
        tx_hash_hex = tx_hash if isinstance(tx_hash, str) else tx_hash.hex()
    eth_send_tx_hash = bytes.fromhex(
        tx_hash_hex[2:] if tx_hash_hex.startswith("0x") else tx_hash_hex
    )

    # Verify balances on Ethereum (should be zero after transfer)
    print("=== Verify balances on Ethereum ===")
    user_balance = ibc_erc20_contract.functions.balanceOf(ethereum_user_address).call()
    assert user_balance == 0, f"Expected user balance 0, got {user_balance}"

    # The whole balance should have been burned/transferred
    ics20_transfer_balance = ibc_erc20_contract.functions.balanceOf(
        contracts["ics20Transfer"]
    ).call()
    assert (
        ics20_transfer_balance == 0
    ), f"Expected ICS20 contract balance 0, got {ics20_transfer_balance}"

    print("Successfully sent transfer from Ethereum to Cosmos")
    return eth_send_tx_hash


def compute_packet_commitment_path(client_id: str, sequence: int) -> bytes:
    """
    Compute the packet commitment path for Ethereum.

    The path is: clientId + uint8(1) + uint64ToBigEndian(sequence)
    This matches the Solidity ICS24Host.packetCommitmentPathCalldata function.

    Args:
        client_id: The client ID (e.g., "solidity-0")
        sequence: The packet sequence number

    Returns:
        The packet commitment path as bytes
    """
    # Convert sequence to uint64 big-endian bytes
    sequence_bytes = sequence.to_bytes(8, byteorder="big")
    # Path is: clientId (string) + uint8(1) + sequence (uint64 big-endian)
    path = client_id.encode("utf-8") + bytes([1]) + sequence_bytes
    return path


def verify_packet_commitment_exists_on_ethereum(
    w3: Web3,
    ics26_contract: "Any",
    client_id: str,
    sequence: int,
) -> None:
    """
    Verify that a packet commitment exists on Ethereum.

    Args:
        w3: Web3 instance
        ics26_contract: The ICS26Router contract instance
        client_id: The client ID (e.g., "solidity-0")
        sequence: The packet sequence number

    Raises:
        AssertionError: If the commitment doesn't exist or is zero
    """
    # Compute packet commitment path
    packet_commitment_path = compute_packet_commitment_path(client_id, sequence)
    # Hash with Keccak256 to get Ethereum path
    eth_path_bytes = eth_keccak256(packet_commitment_path)
    # Convert to bytes32 (32 bytes)
    eth_path = bytes(eth_path_bytes[:32])

    # Call GetCommitment on the contract
    commitment = ics26_contract.functions.getCommitment(eth_path).call()
    assert commitment != bytes(32), (
        f"Packet commitment should exist but is zero for "
        f"client_id={client_id}, sequence={sequence}"
    )


def verify_packet_commitment_removed_on_ethereum(
    w3: Web3,
    ics26_contract: "Any",
    client_id: str,
    sequence: int,
) -> None:
    """
    Verify that a packet commitment has been removed on Ethereum.

    Args:
        w3: Web3 instance
        ics26_contract: The ICS26Router contract instance
        client_id: The client ID (e.g., "solidity-0")
        sequence: The packet sequence number

    Raises:
        AssertionError: If the commitment still exists (is not zero)
    """
    # Compute packet commitment path
    packet_commitment_path = compute_packet_commitment_path(client_id, sequence)
    # Hash with Keccak256 to get Ethereum path
    eth_path_bytes = eth_keccak256(packet_commitment_path)
    # Convert to bytes32 (32 bytes)
    eth_path = bytes(eth_path_bytes[:32])

    # Call GetCommitment on the contract
    commitment = ics26_contract.functions.getCommitment(eth_path).call()
    assert commitment == bytes(32), (
        f"Packet commitment should be removed (zero) but is not: "
        f"{commitment.hex()} for client_id={client_id}, sequence={sequence}"
    )
