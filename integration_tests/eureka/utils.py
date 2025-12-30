"""
Eureka IBC test utilities.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .eth import EurekaContracts


def get_verifier_address(
    contracts: "EurekaContracts", prover: str, proof_type: str | None = None
) -> str:
    """
    Get the verifier address based on the prover type and proof type.

    Args:
        contracts: The deployed contracts dictionary
        prover: The prover type ("mock", "network", or "local")
        proof_type: The proof type ("groth16" or "plonk"), required if prover
            is not "mock"

    Returns:
        str: The verifier contract address

    Raises:
        ValueError: If the prover type or proof type is invalid
    """
    if prover == "mock":
        return contracts["verifierMock"]

    if proof_type is None:
        raise ValueError(
            f"proof_type is required when prover is '{prover}', "
            "but proof_type was not provided"
        )

    if proof_type == "groth16":
        return contracts["verifierGroth16"]
    elif proof_type == "plonk":
        return contracts["verifierPlonk"]
    else:
        raise ValueError(f"invalid proof type: {proof_type}")
