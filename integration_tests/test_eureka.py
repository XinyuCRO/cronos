import subprocess
from pathlib import Path
from typing import Optional, TypedDict

import pytest

from integration_tests.eureka.relayer import (
    create_client,
    generate_relayer_config,
    get_grpc_client,
    get_relayer_pb2,
    relay_by_tx,
    start_relayer,
)
from integration_tests.utils import ADDRS, CONTRACTS, KEYS, derive_new_account

from .eureka.cronos import (
    broadcast_ack_relay_tx,
    decode_create_client_tx,
    query_balance,
    register_counterparty_on_cosmos,
    send_ics20_transfer_packet,
    store_wasm_light_client,
    submit_create_client_tx,
    verify_packet_commitment_exists,
    verify_packet_commitment_removed,
)
from .eureka.eth import (
    EurekaContracts,
    add_client_and_counterparty,
    approve_and_send_transfer_from_ethereum,
    broadcast_tx,
    deploy_ibc_contracts_to_eth,
    fund_user_account_with_erc20,
    verify_packet_commitment_exists_on_ethereum,
    verify_packet_commitment_removed_on_ethereum,
)
from .eureka.utils import get_verifier_address
from .network import Cronos, Geth, setup_custom_cronos

# ============================================================================
# Type Definitions
# ============================================================================


class EurekaTestContext(TypedDict):
    """Context object passed between test steps"""

    cronos: Cronos
    geth: Geth
    contracts: EurekaContracts
    wasm_checksum: str
    relayer_process: Optional[subprocess.Popen]
    sp1_ics07_address: str
    cosmos_client_id: str
    eth_client_id: str


# ============================================================================
# Constants
# ============================================================================

EUREKA_DIR = Path(__file__).parent / "solidity-ibc-eureka"
WASM_FILE = Path(__file__).parent / "wasm" / "cw_dummy_light_client.wasm.gz"

RELAYER_BINARY_PATH = "/Users/xinyuzhao/.cargo/bin/relayer"
# Client IDs used in the test (matching Go test values)
CUSTOM_CLIENT_ID = "solidity-0"  # Client ID on Ethereum
FIRST_WASM_CLIENT_ID = "08-wasm-0"  # First wasm client on Cosmos

# network|local|mock
SP1_PROVER = "mock"

# Relayer configuration
RELAYER_GRPC_ADDRESS = "127.0.0.1:3000"

# Test values (matching Go test values)
INITIAL_BALANCE = 1_000_000_000_000
TRANSFER_AMOUNT = 1_000_000_000


@pytest.fixture(scope="module")
def cronos_one_validator(tmp_path_factory):
    """Cronos instance with only one validator for eureka tests"""
    path = tmp_path_factory.mktemp("eureka")
    yield from setup_custom_cronos(
        path, 28000, Path(__file__).parent / "configs/eureka-one-validator.jsonnet"
    )


def test_eureka_flow(cronos_one_validator, geth, tmp_path_factory):
    context: EurekaTestContext = {
        "geth": geth,
        "cronos": cronos_one_validator,
        "contracts": None,  # type: ignore
        "wasm_checksum": "",
        "relayer_process": None,
        "sp1_ics07_address": "",
        "cosmos_client_id": "",
        "eth_client_id": "",
    }

    cronos = cronos_one_validator

    deploy_ibc_contracts_to_eth(context, EUREKA_DIR, KEYS, ADDRS)
    assert context["contracts"] is not None

    store_wasm_light_client(context, WASM_FILE)
    assert context["wasm_checksum"] is not None

    cosmos_chain_id = cronos.cosmos_cli(0).chain_id
    eth_chain_id = str(geth.w3.eth.chain_id)

    # Start Relayer
    relayer_base_path = tmp_path_factory.mktemp("relayer")
    relayer_config_path = generate_relayer_config(
        context=context,
        base_path=relayer_base_path,
        eureka_dir=EUREKA_DIR,
        signer_eth_address=ADDRS["validator"],
        eth_chain_id=eth_chain_id,
        cosmos_chain_id=cosmos_chain_id,
    )

    assert relayer_config_path is not None

    relayer_process = start_relayer(
        relayer_config_path, binary_path=RELAYER_BINARY_PATH
    )
    assert relayer_process is not None

    try:
        # Get verifier address based on prover type
        verifier_address = get_verifier_address(
            context["contracts"], SP1_PROVER, proof_type=None
        )
        assert verifier_address is not None

        relayer_client = get_grpc_client(RELAYER_GRPC_ADDRESS)
        assert relayer_client is not None

        # Retrieve create client tx(to ethereum) from relayer
        create_client_tx = create_client(
            relayer_client=relayer_client,
            cosmos_chain_id=cosmos_chain_id,
            eth_chain_id=str(eth_chain_id),
            verifier_address=verifier_address,
            zk_algorithm="groth16",
        )
        assert create_client_tx is not None

        # Broadcast the transaction to ethereum
        create_client_tx_receipt = broadcast_tx(
            w3=geth.w3,
            user_key=KEYS["validator"],
            gas_limit=15_000_000,
            to_address=None,
            tx_bytes=create_client_tx.tx,
        )

        sp1_ics07_address = create_client_tx_receipt["contractAddress"]
        assert sp1_ics07_address is not None
        context["sp1_ics07_address"] = sp1_ics07_address

        # Fund address with ERC20
        user_account = derive_new_account(n=8)
        fund_user_account_with_erc20(
            w3=geth.w3,
            user_account=user_account,
            erc20_contract_address=context["contracts"]["erc20"],
            contract_abi_path=CONTRACTS["TestERC20A"],
            validator_address=ADDRS["validator"],
            validator_key=KEYS["validator"],
        )

        print("=== Create ethereum light client on Cronos ===")
        relayer_pb2 = get_relayer_pb2()
        create_client_cosmos_request = relayer_pb2.CreateClientRequest(
            src_chain=str(eth_chain_id),
            dst_chain=cosmos_chain_id,
            parameters={
                "checksum_hex": context["wasm_checksum"],
            },
        )
        create_client_cosmos_response = relayer_client.CreateClient(
            create_client_cosmos_request
        )
        assert create_client_cosmos_response is not None
        assert len(create_client_cosmos_response.tx) > 0
        assert create_client_cosmos_response.address == ""

        msg_create_client = decode_create_client_tx(create_client_cosmos_response.tx)
        assert msg_create_client is not None

        # Submit transaction using CLI
        submit_create_client_tx(
            cronos=cronos,
            tx_bytes=create_client_cosmos_response.tx,
            relayer_base_path=relayer_base_path,
            context=context,
            expected_client_id=FIRST_WASM_CLIENT_ID,
        )

        # Add client and counterparty on EVM
        add_client_and_counterparty(
            context=context,
            eureka_dir=EUREKA_DIR,
            client_id=CUSTOM_CLIENT_ID,
            counterparty_client_id=FIRST_WASM_CLIENT_ID,
            sp1_ics07_address=context["sp1_ics07_address"],
            validator_key=KEYS["validator"],
            validator_address=ADDRS["validator"],
        )

        # The signer in the message must match the signer who created the client
        # Since submit_create_client_tx uses "validator" to sign,
        # we use validator address
        cli = cronos.cosmos_cli(0)
        validator_address = cli.address("validator")

        register_counterparty_on_cosmos(
            cronos=cronos,
            relayer_base_path=relayer_base_path,
            client_id=FIRST_WASM_CLIENT_ID,
            counterparty_client_id=CUSTOM_CLIENT_ID,
            relayer_signer_address=validator_address,
        )

        print("=== Send transfer on Cosmos chain ===")
        import time

        timeout_timestamp = int(time.time()) + 30 * 60  # 30 minutes from now
        transfer_amount_str = str(TRANSFER_AMOUNT)
        # Base denom for Cronos is "basetcro"
        denom = "basetcro"

        # Get user account for sending (using validator for simplicity)
        cosmos_user_address = validator_address
        ethereum_user_address = ADDRS["validator"]

        # Query initial balance before transfer
        balance_before = query_balance(cronos, cosmos_user_address, denom)

        cosmos_send_tx_hash = send_ics20_transfer_packet(
            cronos=cronos,
            relayer_base_path=relayer_base_path,
            source_client_id=FIRST_WASM_CLIENT_ID,
            denom=denom,
            amount=transfer_amount_str,
            sender_address=cosmos_user_address,
            receiver_address=ethereum_user_address,
            memo="nativesend",
            timeout_timestamp=timeout_timestamp,
            signer="validator",
            gas=200_000,
        )
        assert cosmos_send_tx_hash is not None
        assert len(cosmos_send_tx_hash) > 0

        print("=== Verify balances on Cosmos chain ===")
        balance_after = query_balance(cronos, cosmos_user_address, denom)

        # Query the actual transaction to get the fee amount
        from integration_tests.utils import parse_events_rpc, wait_for_new_blocks

        tx_result = cronos.cosmos_cli(0).query_tx("hash", cosmos_send_tx_hash.hex())
        events = parse_events_rpc(tx_result.get("events", []))
        tx_fee_str = events.get("tx", {}).get("fee", "0basetcro")
        # Extract fee amount (remove denom suffix)
        tx_fee = int(tx_fee_str.replace("basetcro", "")) if tx_fee_str else 0

        # Expected balance should account for both transfer amount and transaction fee
        expected_balance = balance_before - TRANSFER_AMOUNT - tx_fee
        assert balance_after == expected_balance, (
            f"Expected balance {expected_balance}, got {balance_after}. "
            f"Balance before: {balance_before}, Transfer amount: {TRANSFER_AMOUNT}, "
            f"Transaction fee: {tx_fee}"
        )

        # Wait for a few blocks to ensure the transaction is finalized
        # This helps ensure the relayer can properly fetch the event
        cli = cronos.cosmos_cli(0)
        wait_for_new_blocks(cli, 2)

        print("=== Receive packet on Ethereum ===")
        # Retrieve relay tx from relayer
        relay_response = relay_by_tx(
            relayer_client=relayer_client,
            src_chain=cosmos_chain_id,
            dst_chain=eth_chain_id,
            source_tx_ids=[cosmos_send_tx_hash],
            src_client_id=FIRST_WASM_CLIENT_ID,
            dst_client_id=CUSTOM_CLIENT_ID,
        )
        assert relay_response is not None
        assert len(relay_response.tx) > 0
        assert relay_response.address == context["contracts"]["ics26Router"]

        # Broadcast the relay transaction to Ethereum
        relay_tx_receipt = broadcast_tx(
            w3=geth.w3,
            user_key=KEYS["validator"],
            gas_limit=15_000_000,
            to_address=relay_response.address,
            tx_bytes=relay_response.tx,
        )
        assert relay_tx_receipt["status"] == 1, "Relay transaction failed"

        print("Successfully received packet on Ethereum")

        print("=== Verify balances on Ethereum ===")
        # Parse WriteAcknowledgement event to get the packet
        import json

        eureka_dir = EUREKA_DIR
        ics26_abi_path = eureka_dir / "abi" / "ICS26Router.json"
        ics26_abi_data = json.loads(ics26_abi_path.read_text())
        if isinstance(ics26_abi_data, list):
            ics26_abi = ics26_abi_data
        else:
            ics26_abi = ics26_abi_data["abi"]
        ics26_contract = geth.w3.eth.contract(
            address=context["contracts"]["ics26Router"], abi=ics26_abi
        )

        # Parse WriteAcknowledgement event from receipt
        write_ack_events = ics26_contract.events.WriteAcknowledgement().process_receipt(
            relay_tx_receipt
        )
        assert len(write_ack_events) > 0, "WriteAcknowledgement event not found"
        packet = write_ack_events[0]["args"]["packet"]

        # Recreate the full denom path
        dest_port = packet["payloads"][0]["destPort"]
        dest_client = packet["destClient"]
        denom_on_ethereum = f"{dest_port}/{dest_client}/{denom}"

        # Get IBC ERC20 contract address
        ics20_abi_path = eureka_dir / "abi" / "ICS20Transfer.json"
        ics20_abi_data = json.loads(ics20_abi_path.read_text())
        if isinstance(ics20_abi_data, list):
            ics20_abi = ics20_abi_data
        else:
            ics20_abi = ics20_abi_data["abi"]
        ics20_contract = geth.w3.eth.contract(
            address=context["contracts"]["ics20Transfer"], abi=ics20_abi
        )

        ibc_erc20_address = ics20_contract.functions.ibcERC20Contract(
            denom_on_ethereum
        ).call()
        assert (
            ibc_erc20_address != "0x0000000000000000000000000000000000000000"
        ), f"IBC ERC20 contract not found for denom: {denom_on_ethereum}"

        # Get IBCERC20 contract
        ibc_erc20_abi_path = eureka_dir / "abi" / "IBCERC20.json"
        ibc_erc20_abi_data = json.loads(ibc_erc20_abi_path.read_text())
        if isinstance(ibc_erc20_abi_data, list):
            ibc_erc20_abi = ibc_erc20_abi_data
        else:
            ibc_erc20_abi = ibc_erc20_abi_data["abi"]
        ibc_erc20_contract = geth.w3.eth.contract(
            address=ibc_erc20_address, abi=ibc_erc20_abi
        )

        # Verify IBCERC20 contract metadata
        actual_denom = ibc_erc20_contract.functions.name().call()
        assert (
            actual_denom == denom_on_ethereum
        ), f"Expected name {denom_on_ethereum}, got {actual_denom}"

        actual_symbol = ibc_erc20_contract.functions.symbol().call()
        assert (
            actual_symbol == denom_on_ethereum
        ), f"Expected symbol {denom_on_ethereum}, got {actual_symbol}"

        actual_full_denom = ibc_erc20_contract.functions.fullDenomPath().call()
        assert (
            actual_full_denom == denom_on_ethereum
        ), f"Expected fullDenomPath {denom_on_ethereum}, got {actual_full_denom}"

        # Verify balances on Ethereum
        user_balance = ibc_erc20_contract.functions.balanceOf(
            ethereum_user_address
        ).call()
        assert (
            user_balance == TRANSFER_AMOUNT
        ), f"Expected user balance {TRANSFER_AMOUNT}, got {user_balance}"

        # ICS20 contract balance on Ethereum should be zero
        ics20_transfer_balance = ibc_erc20_contract.functions.balanceOf(
            context["contracts"]["ics20Transfer"]
        ).call()
        assert (
            ics20_transfer_balance == 0
        ), f"Expected ICS20 contract balance 0, got {ics20_transfer_balance}"

        print("Successfully verified IBC ERC20 contract and balances")

        print("=== Acknowledge packet on Cosmos chain ===")
        # Get the ackTxHash from the relay transaction receipt
        # Convert transactionHash to bytes (it's typically HexBytes from web3.py)
        tx_hash = relay_tx_receipt["transactionHash"]
        if hasattr(tx_hash, "hex"):
            tx_hash_hex = tx_hash.hex()
        else:
            tx_hash_hex = tx_hash if isinstance(tx_hash, str) else tx_hash.hex()
        # Remove 0x prefix if present and convert to bytes
        ack_tx_hash = bytes.fromhex(
            tx_hash_hex[2:] if tx_hash_hex.startswith("0x") else tx_hash_hex
        )

        print("=== Acknowledge packet on Cosmos chain ===")
        print("=== Verify commitments exists ===")
        channel, query_stub, commitment_request = verify_packet_commitment_exists(
            cronos=cronos, client_id=FIRST_WASM_CLIENT_ID, sequence=1
        )

        # Retrieve relay tx for acknowledgement
        ack_relay_response = relay_by_tx(
            relayer_client=relayer_client,
            src_chain=eth_chain_id,
            dst_chain=cosmos_chain_id,
            source_tx_ids=[ack_tx_hash],
            src_client_id=CUSTOM_CLIENT_ID,
            dst_client_id=FIRST_WASM_CLIENT_ID,
        )
        assert ack_relay_response is not None
        assert len(ack_relay_response.tx) > 0
        # For acknowledgement relays to Cosmos, address should be empty
        assert ack_relay_response.address == "", (
            f"Expected empty address for acknowledgement relay, "
            f"got: {ack_relay_response.address}"
        )

        ack_relay_tx_body_bz = ack_relay_response.tx

        print("=== Broadcast relay tx to Cosmos ===")
        broadcast_ack_relay_tx(
            cronos=cronos,
            relayer_base_path=relayer_base_path,
            ack_relay_tx_body_bz=ack_relay_tx_body_bz,
            signer="validator",
        )

        print("=== Verify commitments removed ===")
        verify_packet_commitment_removed(query_stub, commitment_request)

        channel.close()
        print("Successfully acknowledged packet on Cosmos chain")

        print("=== Transfer tokens back from Ethereum to Cosmos ===")
        import time

        timeout_timestamp = int(time.time()) + 30 * 60  # 30 minutes from now
        eth_send_tx_hash = approve_and_send_transfer_from_ethereum(
            w3=geth.w3,
            eureka_dir=EUREKA_DIR,
            contracts=context["contracts"],
            ibc_erc20_address=ibc_erc20_address,
            ethereum_user_address=ethereum_user_address,
            cosmos_user_address=cosmos_user_address,
            transfer_amount=TRANSFER_AMOUNT,
            source_client_id=CUSTOM_CLIENT_ID,
            user_key=KEYS["validator"],
            timeout_timestamp=timeout_timestamp,
            memo="testreturnmemo",
        )
        assert eth_send_tx_hash is not None
        assert len(eth_send_tx_hash) > 0

        print("=== Receive packet on Cosmos chain ===")
        # Wait for a few blocks to ensure the transaction is finalized
        from integration_tests.utils import wait_for_new_blocks

        cli = cronos.cosmos_cli(0)
        wait_for_new_blocks(cli, 2)

        # Retrieve relay tx from relayer
        print("=== Retrieve relay tx ===")
        return_relay_response = relay_by_tx(
            relayer_client=relayer_client,
            src_chain=eth_chain_id,
            dst_chain=cosmos_chain_id,
            source_tx_ids=[eth_send_tx_hash],
            src_client_id=CUSTOM_CLIENT_ID,
            dst_client_id=FIRST_WASM_CLIENT_ID,
        )
        assert return_relay_response is not None
        assert len(return_relay_response.tx) > 0
        # For packet relays to Cosmos, address should be empty
        assert return_relay_response.address == "", (
            f"Expected empty address for packet relay, "
            f"got: {return_relay_response.address}"
        )

        return_relay_tx_body_bz = return_relay_response.tx

        balance_before = query_balance(cronos, cosmos_user_address, denom)

        # Broadcast relay tx to Cosmos
        print("=== Broadcast relay tx ===")
        return_ack_tx_hash = broadcast_ack_relay_tx(
            cronos=cronos,
            relayer_base_path=relayer_base_path,
            ack_relay_tx_body_bz=return_relay_tx_body_bz,
        )

        # Verify balances on Cosmos chain
        print("=== Verify balances on Cosmos chain ===")
        balance_after_return = query_balance(cronos, cosmos_user_address, denom)
        # Balance should be back close to initial balance (the tokens were returned)
        # Account for transaction fees from both the send and receive transactions
        # Query the receive transaction to get the fee
        tx_result = cronos.cosmos_cli(0).query_tx("hash", return_ack_tx_hash.hex())
        events = parse_events_rpc(tx_result.get("events", []))
        receive_tx_fee_str = events.get("tx", {}).get("fee", "0basetcro")
        receive_tx_fee = (
            int(receive_tx_fee_str.replace("basetcro", "")) if receive_tx_fee_str else 0
        )
        expected_balance = balance_before - receive_tx_fee + TRANSFER_AMOUNT

        assert balance_after_return == expected_balance, (
            f"Expected balance {expected_balance}, got {balance_after_return}. "
            f"Initial balance: {balance_before}, Receive tx fee: {receive_tx_fee}"
        )

        print("=== Acknowledge packet on Ethereum ===")
        # Wait for blocks to ensure Cosmos transaction is finalized
        from integration_tests.utils import wait_for_new_blocks

        wait_for_new_blocks(cli, 2)

        # Verify commitment exists
        print("=== Verify commitment exists ===")
        verify_packet_commitment_exists_on_ethereum(
            w3=geth.w3,
            ics26_contract=ics26_contract,
            client_id=CUSTOM_CLIENT_ID,
            sequence=1,
        )

        # Retrieve relay tx for acknowledgement (Cosmos -> Ethereum)
        print("=== Retrieve relay tx ===")

        ack_relay_response = relay_by_tx(
            relayer_client=relayer_client,
            src_chain=cosmos_chain_id,
            dst_chain=eth_chain_id,
            source_tx_ids=[return_ack_tx_hash],
            src_client_id=FIRST_WASM_CLIENT_ID,
            dst_client_id=CUSTOM_CLIENT_ID,
        )
        assert ack_relay_response is not None
        assert len(ack_relay_response.tx) > 0
        assert ack_relay_response.address == context["contracts"]["ics26Router"], (
            f"Expected address {context['contracts']['ics26Router']}, "
            f"got {ack_relay_response.address}"
        )

        # Submit relay tx to Ethereum
        print("=== Submit relay tx ===")
        ack_relay_tx_receipt = broadcast_tx(
            w3=geth.w3,
            user_key=KEYS["validator"],
            gas_limit=5_000_000,
            to_address=ack_relay_response.address,
            tx_bytes=ack_relay_response.tx,
        )
        assert ack_relay_tx_receipt["status"] == 1, "Ack relay transaction failed"

        # Verify the AckPacket event exists
        ack_packet_events = ics26_contract.events.AckPacket().process_receipt(
            ack_relay_tx_receipt
        )
        assert len(ack_packet_events) > 0, "AckPacket event not found"

        # Verify commitment removed
        print("=== Verify commitment removed ===")
        verify_packet_commitment_removed_on_ethereum(
            w3=geth.w3,
            ics26_contract=ics26_contract,
            client_id=CUSTOM_CLIENT_ID,
            sequence=1,
        )

        # Verify balances on Ethereum after ack
        print("=== Verify balances on Ethereum after ack ===")
        user_balance_after_ack = ibc_erc20_contract.functions.balanceOf(
            ethereum_user_address
        ).call()
        assert (
            user_balance_after_ack == 0
        ), f"Expected user balance 0, got {user_balance_after_ack}"

        ics20_transfer_balance_after_ack = ibc_erc20_contract.functions.balanceOf(
            context["contracts"]["ics20Transfer"]
        ).call()
        assert ics20_transfer_balance_after_ack == 0, (
            f"Expected ICS20 contract balance 0, "
            f"got {ics20_transfer_balance_after_ack}"
        )

    finally:
        # Always stop the relayer process, even if the test fails
        relayer_process.kill()
        relayer_process.wait()
