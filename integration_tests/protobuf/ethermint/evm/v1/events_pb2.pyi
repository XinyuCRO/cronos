from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class EventEthereumTx(_message.Message):
    __slots__ = ()
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    ETH_HASH_FIELD_NUMBER: _ClassVar[int]
    INDEX_FIELD_NUMBER: _ClassVar[int]
    GAS_USED_FIELD_NUMBER: _ClassVar[int]
    HASH_FIELD_NUMBER: _ClassVar[int]
    RECIPIENT_FIELD_NUMBER: _ClassVar[int]
    ETH_TX_FAILED_FIELD_NUMBER: _ClassVar[int]
    amount: str
    eth_hash: str
    index: str
    gas_used: str
    hash: str
    recipient: str
    eth_tx_failed: str
    def __init__(self, amount: _Optional[str] = ..., eth_hash: _Optional[str] = ..., index: _Optional[str] = ..., gas_used: _Optional[str] = ..., hash: _Optional[str] = ..., recipient: _Optional[str] = ..., eth_tx_failed: _Optional[str] = ...) -> None: ...

class EventTxLog(_message.Message):
    __slots__ = ()
    TX_LOGS_FIELD_NUMBER: _ClassVar[int]
    tx_logs: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, tx_logs: _Optional[_Iterable[str]] = ...) -> None: ...

class EventMessage(_message.Message):
    __slots__ = ()
    MODULE_FIELD_NUMBER: _ClassVar[int]
    SENDER_FIELD_NUMBER: _ClassVar[int]
    TX_TYPE_FIELD_NUMBER: _ClassVar[int]
    module: str
    sender: str
    tx_type: str
    def __init__(self, module: _Optional[str] = ..., sender: _Optional[str] = ..., tx_type: _Optional[str] = ...) -> None: ...

class EventBlockBloom(_message.Message):
    __slots__ = ()
    BLOOM_FIELD_NUMBER: _ClassVar[int]
    bloom: str
    def __init__(self, bloom: _Optional[str] = ...) -> None: ...
