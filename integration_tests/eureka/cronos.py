"""
Cronos-related utilities for Eureka IBC tests.
"""

import base64
import gzip
import hashlib

# Workaround for protobuf version mismatch: IBC protobuf files were generated with
# protoc 6.x which uses runtime_version, but the environment has protobuf 4.25.8
# We need to patch runtime_version before importing the IBC protobuf modules
import sys
import types
from pathlib import Path
from typing import TYPE_CHECKING

import requests
from pystarport import ports

try:
    from google.protobuf import runtime_version
except ImportError:
    # Create a mock runtime_version module for older protobuf versions
    runtime_version = types.ModuleType("runtime_version")
    runtime_version.Domain = types.SimpleNamespace()
    runtime_version.Domain.PUBLIC = "PUBLIC"

    def ValidateProtobufRuntimeVersion(*args, **kwargs):
        pass  # Skip validation for older protobuf versions

    runtime_version.ValidateProtobufRuntimeVersion = ValidateProtobufRuntimeVersion

    # Inject into sys.modules and google.protobuf before the IBC protobuf import
    sys.modules["google.protobuf.runtime_version"] = runtime_version
    import google.protobuf

    google.protobuf.runtime_version = runtime_version

import json

import grpc
from google.protobuf import json_format

from integration_tests.protobuf.cosmos.tx.v1beta1 import tx_pb2 as cosmos_tx_pb2
from integration_tests.protobuf.ibc.core.channel.v2 import query_pb2, query_pb2_grpc
from integration_tests.protobuf.ibc.core.channel.v2 import (  # noqa: F401
    tx_pb2 as ibc_channel_v2_tx_pb2,
)
from integration_tests.protobuf.ibc.core.client.v1 import tx_pb2 as ibc_client_tx_pb2
from integration_tests.protobuf.ibc.lightclients.wasm.v1 import wasm_pb2  # noqa: F401

if TYPE_CHECKING:
    from typing import Any

    # Forward reference to avoid circular import
    EurekaTestContext = dict[str, Any]


def store_wasm_light_client(context: "EurekaTestContext", wasm_file: Path) -> None:
    """
    Store the wasm light client code on Cronos via governance proposal.

    This stores the dummy light client used for testing. In production,
    this would be the actual Ethereum light client.

    This function is idempotent - if the code is already stored, it will
    return the existing checksum without attempting to store again.

    Args:
        context: The test context dictionary that will be updated with
            wasm_checksum
        wasm_file: Path to the wasm file to store
    """
    from integration_tests import cosmoscli
    from integration_tests.utils import approve_proposal, wait_for_new_blocks

    print("\n=== Storing Wasm Light Client on Cronos ===")

    cronos = context["cronos"]

    cli = cronos.cosmos_cli()

    # Read and compute checksum of the wasm code
    with gzip.open(wasm_file, "rb") as f:
        wasm_content = f.read()

    checksum_bytes = hashlib.sha256(wasm_content).digest()
    computed_checksum = checksum_bytes.hex()
    print(f"Wasm code checksum: {computed_checksum}")

    # Check if the wasm code is already stored
    api_port = ports.api_port(cronos.base_port(0))
    query_url = (
        f"http://127.0.0.1:{api_port}/ibc/lightclients/wasm/v1/"
        f"checksums/{computed_checksum}/code"
    )
    response = requests.get(query_url)

    if response.ok:
        # Code already exists, verify and return
        code_resp = response.json()
        if "data" in code_resp:
            returned_data = base64.b64decode(code_resp["data"])
            actual_checksum = hashlib.sha256(returned_data).hexdigest()
            if computed_checksum == actual_checksum:
                print(f"Wasm light client already stored: {computed_checksum}")
                context["wasm_checksum"] = computed_checksum
                return

    # Code doesn't exist, submit governance proposal to store it
    zipped_content = wasm_file.read_bytes()
    gov_module_addr = cosmoscli.module_address("gov")

    msg_type = "/ibc.lightclients.wasm.v1.MsgStoreCode"
    proposal_json = {
        "title": "Store Wasm Light Client Code",
        "summary": "Store dummy light client wasm code for IBC Eureka testing",
        "messages": [
            {
                "@type": msg_type,
                "signer": gov_module_addr,
                "wasm_byte_code": base64.b64encode(zipped_content).decode("utf-8"),
            }
        ],
        "deposit": "100basetcro",
    }

    rsp = cli.submit_gov_proposal(
        "community",
        "submit-proposal",
        proposal_json,
        broadcast_mode="sync",
        wait_tx=False,  # Don't wait - the tx is large and may take time
    )
    assert rsp["code"] == 0, rsp["raw_log"]

    wait_for_new_blocks(cli, 2)

    tx_hash = rsp["txhash"]
    tx_result = cli.query_tx("hash", tx_hash)
    assert tx_result.get("code", 0) == 0, f"Transaction failed: {tx_result}"

    approve_proposal(cronos, tx_result["events"], msg=msg_type, gas="20000000")

    # Verify the code was stored
    response = requests.get(query_url)
    assert response.ok, f"Query failed: {response.status_code} {response.text}"

    code_resp = response.json()
    assert "data" in code_resp, "Response missing 'data' field"

    returned_data = base64.b64decode(code_resp["data"])
    actual_checksum = hashlib.sha256(returned_data).hexdigest()
    assert (
        computed_checksum == actual_checksum
    ), f"Checksum mismatch: expected {computed_checksum}, got {actual_checksum}"

    print(f"Wasm light client stored successfully with checksum: {computed_checksum}")
    context["wasm_checksum"] = computed_checksum


def decode_create_client_tx(tx_bytes: bytes) -> ibc_client_tx_pb2.MsgCreateClient:
    """
    Decode a Cosmos transaction and extract the MsgCreateClient message.

    Args:
        tx_bytes: The transaction bytes from create_client_cosmos_response.tx

    Returns:
        The decoded MsgCreateClient message

    Raises:
        ValueError: If the transaction doesn't contain a MsgCreateClient message
    """
    # Decode the transaction as TxBody
    tx_body = cosmos_tx_pb2.TxBody()
    tx_body.ParseFromString(tx_bytes)

    # Find the MsgCreateClient message
    msg_create_client_type_url = "/ibc.core.client.v1.MsgCreateClient"

    for msg in tx_body.messages:
        if msg.type_url == msg_create_client_type_url:
            # Decode the message value as MsgCreateClient
            msg_create_client = ibc_client_tx_pb2.MsgCreateClient()
            msg_create_client.ParseFromString(msg.value)
            return msg_create_client

    raise ValueError(
        f"No MsgCreateClient message found in transaction. "
        f"Found {len(tx_body.messages)} message(s) with types: "
        f"{[msg.type_url for msg in tx_body.messages]}"
    )


def submit_create_client_tx(
    cronos: "Any",
    tx_bytes: bytes,
    relayer_base_path: Path,
    context: "EurekaTestContext",
    expected_client_id: str,
) -> None:
    from integration_tests.utils import parse_events_rpc

    # Import WASM light client types so they're registered in protobuf
    # symbol database (already imported at module level, but kept for clarity)
    # Submit transaction using CLI
    cli = cronos.cosmos_cli(0)

    # Parse TxBody from bytes
    tx_body = cosmos_tx_pb2.TxBody()
    tx_body.ParseFromString(tx_bytes)

    # Convert TxBody to JSON dict
    # Now that WASM types are imported, MessageToDict should work
    tx_body_dict = json_format.MessageToDict(tx_body)

    # Create transaction JSON structure
    # Calculate fee dynamically based on current base fee
    # Query the current base fee from the latest block
    w3 = cronos.w3
    latest_block = w3.eth.get_block("latest")
    base_fee = latest_block.get("baseFeePerGas", 0)

    # Use base fee with a 20% buffer to ensure it's sufficient
    # If base_fee is 0, use a reasonable default
    if base_fee == 0:
        # Fallback: query minimum gas price from feemarket params
        try:
            feemarket_params = cli.query_params("feemarket")
            min_gas_price = int(
                float(feemarket_params.get("min_gas_price", "10000000000000"))
            )
        except Exception:
            # Final fallback - use a conservative value
            min_gas_price = 40000000
    else:
        # Use base fee with buffer
        min_gas_price = int(base_fee * 1.2)

    # Ensure minimum gas price is at least 40M to handle dynamic changes
    min_gas_price = max(min_gas_price, 40000000)

    gas_limit = 20000000
    fee_amount = gas_limit * min_gas_price

    tx_json = {
        "body": tx_body_dict,
        "auth_info": {
            "signer_infos": [],
            "fee": {
                "amount": [{"denom": "basetcro", "amount": str(fee_amount)}],
                "gas_limit": str(gas_limit),
            },
        },
        "signatures": [],
    }

    # Write transaction JSON to relayer_base_path
    tx_file = relayer_base_path / "create_client_tx.json"
    with open(tx_file, "w") as f:
        json.dump(tx_json, f)

    # Sign the transaction
    signer = "validator"
    signed_tx = cli.sign_single_tx(str(tx_file), signer)

    # Write signed transaction to relayer_base_path
    signed_tx_file = relayer_base_path / "create_client_tx_signed.json"
    with open(signed_tx_file, "w") as f:
        json.dump(signed_tx, f)

    # Broadcast the signed transaction
    rsp = cli.broadcast_tx(str(signed_tx_file), broadcast_mode="sync")
    assert rsp["code"] == 0, (
        f"Transaction failed: " f"{rsp.get('raw_log', 'Unknown error')}"
    )

    # Parse events to extract client_id
    events = parse_events_rpc(rsp["events"])
    client_id = events.get("create_client", {}).get("client_id")
    assert client_id is not None, f"client_id not found in events: {events}"
    assert (
        client_id == expected_client_id
    ), f"Expected client_id {expected_client_id}, got {client_id}"

    context["cosmos_client_id"] = client_id


def register_counterparty_on_cosmos(
    cronos: "Any",
    relayer_base_path: Path,
    client_id: str,
    counterparty_client_id: str,
    relayer_signer_address: str,
    signer: str = "validator",
    gas: int = 200000,
) -> None:
    """
    Register counterparty on Cosmos chain via MsgRegisterCounterparty.

    The signer must be the same address that created the client (typically
    the relayer signer address).

    Args:
        cronos: The Cronos network instance
        relayer_base_path: Path to the relayer base directory for storing
            transaction files
        client_id: The client ID on Cosmos (e.g., "08-wasm-0")
        counterparty_client_id: The counterparty client ID (e.g., "solidity-0")
        relayer_signer_address: The relayer signer address (bech32 format)
            that created the client
        signer: The signer key name for signing the transaction
            (default: "validator")
        gas: Gas limit for the transaction (default: 200000)

    Raises:
        AssertionError: If the transaction fails
    """
    cli = cronos.cosmos_cli(0)
    # Use the relayer signer address as the message signer
    # (must match the address that created the client)
    signer_address = relayer_signer_address

    # Manually create the message JSON with correct type URL format
    # The CLI expects type URLs in the format "/package.Message" not
    # "type.googleapis.com/..."
    import base64

    msg_json = {
        "@type": "/ibc.core.client.v2.MsgRegisterCounterparty",
        "client_id": client_id,
        "counterparty_merkle_prefix": [
            base64.b64encode(b"").decode("utf-8")
        ],  # Empty merkle prefix
        "counterparty_client_id": counterparty_client_id,
        "signer": signer_address,
    }

    # Create TxBody JSON dict directly
    tx_body_dict = {
        "messages": [msg_json],
        "memo": "",
        "timeout_height": "0",
        "extension_options": [],
        "non_critical_extension_options": [],
    }

    # Calculate fee
    w3 = cronos.w3
    latest_block = w3.eth.get_block("latest")
    base_fee = latest_block.get("baseFeePerGas", 0)

    if base_fee == 0:
        try:
            feemarket_params = cli.query_params("feemarket")
            min_gas_price = int(
                float(feemarket_params.get("min_gas_price", "10000000000000"))
            )
        except Exception:
            min_gas_price = 40000000
    else:
        min_gas_price = int(base_fee * 1.2)

    min_gas_price = max(min_gas_price, 40000000)
    fee_amount = gas * min_gas_price

    tx_json = {
        "body": tx_body_dict,
        "auth_info": {
            "signer_infos": [],
            "fee": {
                "amount": [{"denom": "basetcro", "amount": str(fee_amount)}],
                "gas_limit": str(gas),
            },
        },
        "signatures": [],
    }

    # Write transaction JSON to relayer_base_path
    tx_file = relayer_base_path / "register_counterparty_tx.json"
    with open(tx_file, "w") as f:
        json.dump(tx_json, f)

    # Sign the transaction
    signed_tx = cli.sign_single_tx(str(tx_file), signer)

    # Write signed transaction to relayer_base_path
    signed_tx_file = relayer_base_path / "register_counterparty_tx_signed.json"
    with open(signed_tx_file, "w") as f:
        json.dump(signed_tx, f)

    # Broadcast the signed transaction
    rsp = cli.broadcast_tx(str(signed_tx_file), broadcast_mode="sync")
    assert rsp["code"] == 0, (
        f"Transaction failed: " f"{rsp.get('raw_log', 'Unknown error')}"
    )

    print(
        f"Successfully registered counterparty {counterparty_client_id} "
        f"for client {client_id}"
    )


def encode_abi_fungible_token_packet_data(
    denom: str, amount: str, sender: str, receiver: str, memo: str
) -> bytes:
    """
    Encode FungibleTokenPacketData using ABI encoding.

    This matches the Go function EncodeABIFungibleTokenPacketData which
    encodes the packet data as a Solidity struct using ABI encoding.

    Args:
        denom: Token denomination
        amount: Amount as string
        sender: Sender address
        receiver: Receiver address (hex format, lowercase)
        memo: Optional memo

    Returns:
        ABI-encoded bytes of the FungibleTokenPacketData struct
    """
    from eth_abi import encode

    # The struct order matches Go's getICS20ABI() and EncodeABIFungibleTokenPacketData:
    # tuple {
    #   denom    string
    #   sender   string
    #   receiver string
    #   amount   uint256
    #   memo     string
    # }
    # Note: Amount is *big.Int in Go but ABI encoding uses uint256
    # Convert amount string to int for proper encoding
    amount_int = int(amount)

    # The tuple order must match the Go ABI definition exactly:
    # denom, sender, receiver, amount, memo
    tuple_type = "(string,string,string,uint256,string)"
    tuple_value = (denom, sender, receiver, amount_int, memo)
    # encode() takes types as list and values as list
    # For a single tuple: types=['(string,...)'], values=[(val1, val2, ...)]
    encoded = encode([tuple_type], [tuple_value])

    # Debug: print encoding details
    print(f"ABI Encoding - Tuple type: {tuple_type}")
    print(f"ABI Encoding - Values: {tuple_value}")
    print(f"ABI Encoding - Encoded length: {len(encoded)} bytes")
    print(f"ABI Encoding - First 100 hex chars: {encoded.hex()[:100]}")

    return encoded


def send_ics20_transfer_packet(
    cronos: "Any",
    relayer_base_path: Path,
    source_client_id: str,
    denom: str,
    amount: str,
    sender_address: str,
    receiver_address: str,
    memo: str,
    timeout_timestamp: int,
    signer: str = "validator",
    gas: int = 200_000,
) -> bytes:
    """
    Send an ICS20 transfer packet from Cosmos chain.

    Args:
        cronos: The Cronos network instance
        relayer_base_path: Path to the relayer base directory for storing
            transaction files
        source_client_id: The source client ID (e.g., "08-wasm-0")
        denom: Token denomination
        amount: Amount as string
        sender_address: Sender address (bech32 format)
        receiver_address: Receiver address (hex format, lowercase)
        memo: Optional memo
        timeout_timestamp: Timeout timestamp in unix seconds
        signer: The signer key name for signing the transaction
            (default: "validator")
        gas: Gas limit for the transaction (default: 200_000)

    Returns:
        Transaction hash bytes

    Raises:
        AssertionError: If the transaction fails
    """
    cli = cronos.cosmos_cli(0)

    # Encode the FungibleTokenPacketData using ABI encoding
    encoded_payload = encode_abi_fungible_token_packet_data(
        denom=denom,
        amount=amount,
        sender=sender_address,
        receiver=receiver_address,
        memo=memo,
    )

    # Validate sender_address is a valid bech32 address
    if not sender_address or len(sender_address) == 0:
        raise ValueError("Invalid sender_address: empty or None")

    # Manually construct the message JSON dict to ensure all fields are correctly set
    # This matches the pattern used in register_counterparty_on_cosmos
    import base64

    # Convert payload bytes to base64 string
    payload_value_b64 = base64.b64encode(encoded_payload).decode("utf-8")

    # Manually create the message JSON dict
    msg_dict = {
        "source_client": source_client_id,
        "timeout_timestamp": str(timeout_timestamp),
        "payloads": [
            {
                "source_port": "transfer",
                "destination_port": "transfer",
                "version": "ics20-1",
                "encoding": "application/x-solidity-abi",
                "value": payload_value_b64,
            }
        ],
        "signer": sender_address,
    }

    # Create TxBody JSON dict
    tx_body_dict = {
        "messages": [
            {
                "@type": "/ibc.core.channel.v2.MsgSendPacket",
                **msg_dict,
            }
        ],
        "memo": "",
        "timeout_height": "0",
        "extension_options": [],
        "non_critical_extension_options": [],
    }

    # Calculate fee
    w3 = cronos.w3
    latest_block = w3.eth.get_block("latest")
    base_fee = latest_block.get("baseFeePerGas", 0)

    if base_fee == 0:
        try:
            feemarket_params = cli.query_params("feemarket")
            min_gas_price = int(
                float(feemarket_params.get("min_gas_price", "10000000000000"))
            )
        except Exception:
            min_gas_price = 40000000
    else:
        min_gas_price = int(base_fee * 1.2)

    min_gas_price = max(min_gas_price, 40000000)
    fee_amount = gas * min_gas_price

    tx_json = {
        "body": tx_body_dict,
        "auth_info": {
            "signer_infos": [],
            "fee": {
                "amount": [{"denom": "basetcro", "amount": str(fee_amount)}],
                "gas_limit": str(gas),
            },
        },
        "signatures": [],
    }

    # Write transaction JSON to relayer_base_path
    tx_file = relayer_base_path / "send_packet_tx.json"
    with open(tx_file, "w") as f:
        json.dump(tx_json, f)

    # Sign the transaction
    signed_tx = cli.sign_single_tx(str(tx_file), signer)

    # Write signed transaction to relayer_base_path
    signed_tx_file = relayer_base_path / "send_packet_tx_signed.json"
    with open(signed_tx_file, "w") as f:
        json.dump(signed_tx, f)

    # Broadcast the signed transaction
    rsp = cli.broadcast_tx(str(signed_tx_file), broadcast_mode="sync")
    assert rsp["code"] == 0, (
        f"Transaction failed: " f"{rsp.get('raw_log', 'Unknown error')}"
    )

    # Extract transaction hash
    tx_hash = rsp["txhash"]
    tx_hash_bytes = bytes.fromhex(tx_hash)

    print(f"Successfully sent ICS20 transfer packet: {tx_hash}")
    return tx_hash_bytes


def query_balance(cronos: "Any", address: str, denom: str) -> int:
    """
    Query the balance of a specific denomination for an address on Cosmos chain.

    Args:
        cronos: The Cronos network instance
        address: Address in bech32 format
        denom: Token denomination

    Returns:
        Balance amount as integer
    """
    cli = cronos.cosmos_cli(0)
    return cli.balance(address, denom)


def verify_packet_commitment_exists(
    cronos: "Any", client_id: str, sequence: int
) -> tuple["Any", "Any", "Any"]:
    """
    Verify that a packet commitment exists and return gRPC resources.

    This function sets up a gRPC channel, queries for a packet commitment,
    and verifies it exists. It returns the channel, query stub, and commitment
    request for later use (e.g., verifying the commitment is removed).

    Args:
        cronos: The Cronos network instance
        client_id: The client ID (e.g., "08-wasm-0")
        sequence: The packet sequence number

    Returns:
        A tuple of (channel, query_stub, commitment_request) where:
        - channel: The gRPC channel (should be closed after use)
        - query_stub: The QueryStub instance for IBC channel queries
        - commitment_request: The QueryPacketCommitmentRequest object

    Raises:
        AssertionError: If the packet commitment is not found
    """
    grpc_port = ports.grpc_port(cronos.base_port(0))
    grpc_url = f"127.0.0.1:{grpc_port}"
    channel = grpc.insecure_channel(grpc_url)
    query_stub = query_pb2_grpc.QueryStub(channel)

    # Query packet commitment to verify it exists
    commitment_request = query_pb2.QueryPacketCommitmentRequest(
        client_id=client_id, sequence=sequence
    )
    commitment_response = query_stub.PacketCommitment(commitment_request)
    assert len(commitment_response.commitment) > 0, "Packet commitment not found"

    return channel, query_stub, commitment_request


def verify_packet_commitment_removed(
    query_stub: "Any", commitment_request: "Any"
) -> None:
    """
    Verify that a packet commitment has been removed after acknowledgement.

    This function queries for a packet commitment and expects it to not exist
    (raises an RpcError with "not found" message). If the commitment still exists,
    it raises an AssertionError.

    Args:
        query_stub: The gRPC QueryStub instance for IBC channel queries
        commitment_request: The QueryPacketCommitmentRequest object

    Raises:
        AssertionError: If the packet commitment still exists or if an
            unexpected error occurs
    """
    # Verify commitments removed
    try:
        commitment_response_after = query_stub.PacketCommitment(commitment_request)
        assert False, (
            "Packet commitment should be removed but still exists: "
            f"{commitment_response_after.commitment.hex()}"
        )
    except grpc.RpcError as e:
        assert "packet commitment hash not found" in str(e) or "not found" in str(
            e
        ), f"Unexpected error: {e}"


def broadcast_ack_relay_tx(
    cronos: "Any",
    relayer_base_path: Path,
    ack_relay_tx_body_bz: bytes,
    signer: str = "validator",
) -> None:
    """
    Broadcast an acknowledgement relay transaction to Cosmos chain.

    This function parses the transaction body bytes, calculates the fee,
    creates the transaction JSON, signs it, and broadcasts it to the Cosmos chain.
    It expects the transaction to succeed and raises an AssertionError if it fails.

    Args:
        cronos: The Cronos network instance
        relayer_base_path: Path to the relayer base directory for storing
            transaction files
        ack_relay_tx_body_bz: The transaction body bytes from the relayer
        signer: The signer key name for signing the transaction
            (default: "validator")

    Raises:
        AssertionError: If the transaction fails
    """
    # Parse transaction body
    tx_body = cosmos_tx_pb2.TxBody()
    tx_body.ParseFromString(ack_relay_tx_body_bz)

    tx_body_dict = json_format.MessageToDict(tx_body)

    # Calculate fee
    w3 = cronos.w3
    latest_block = w3.eth.get_block("latest")
    base_fee = latest_block.get("baseFeePerGas", 0)

    if base_fee == 0:
        try:
            feemarket_params = cronos.cosmos_cli(0).query_params("feemarket")
            min_gas_price = int(
                float(feemarket_params.get("min_gas_price", "10000000000000"))
            )
        except Exception:
            min_gas_price = 40000000
    else:
        min_gas_price = int(base_fee * 1.2)

    min_gas_price = max(min_gas_price, 40000000)
    gas_limit = 2_000_000
    fee_amount = gas_limit * min_gas_price

    tx_json = {
        "body": tx_body_dict,
        "auth_info": {
            "signer_infos": [],
            "fee": {
                "amount": [{"denom": "basetcro", "amount": str(fee_amount)}],
                "gas_limit": str(gas_limit),
            },
        },
        "signatures": [],
    }

    # Write transaction JSON to relayer_base_path
    ack_tx_file = relayer_base_path / "ack_relay_tx.json"
    with open(ack_tx_file, "w") as f:
        json.dump(tx_json, f)

    # Sign and broadcast the transaction
    cli = cronos.cosmos_cli(0)
    signed_tx = cli.sign_single_tx(str(ack_tx_file), signer)

    signed_tx_file = relayer_base_path / "ack_relay_tx_signed.json"
    with open(signed_tx_file, "w") as f:
        json.dump(signed_tx, f)

    ack_broadcast_rsp = cli.broadcast_tx(str(signed_tx_file), broadcast_mode="sync")
    assert ack_broadcast_rsp["code"] == 0, (
        f"Acknowledgement transaction failed: "
        f"{ack_broadcast_rsp.get('raw_log', 'Unknown error')}"
    )

    # Return the transaction hash as bytes
    tx_hash = ack_broadcast_rsp["txhash"]
    return bytes.fromhex(tx_hash)
