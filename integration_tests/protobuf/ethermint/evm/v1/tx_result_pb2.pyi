from gogoproto import gogo_pb2 as _gogo_pb2
from ethermint.evm.v1 import transaction_logs_pb2 as _transaction_logs_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TxResult(_message.Message):
    __slots__ = ()
    CONTRACT_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    BLOOM_FIELD_NUMBER: _ClassVar[int]
    TX_LOGS_FIELD_NUMBER: _ClassVar[int]
    RET_FIELD_NUMBER: _ClassVar[int]
    REVERTED_FIELD_NUMBER: _ClassVar[int]
    GAS_USED_FIELD_NUMBER: _ClassVar[int]
    contract_address: str
    bloom: bytes
    tx_logs: _transaction_logs_pb2.TransactionLogs
    ret: bytes
    reverted: bool
    gas_used: int
    def __init__(self, contract_address: _Optional[str] = ..., bloom: _Optional[bytes] = ..., tx_logs: _Optional[_Union[_transaction_logs_pb2.TransactionLogs, _Mapping]] = ..., ret: _Optional[bytes] = ..., reverted: _Optional[bool] = ..., gas_used: _Optional[int] = ...) -> None: ...
