from gogoproto import gogo_pb2 as _gogo_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Log(_message.Message):
    __slots__ = ()
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    TOPICS_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    BLOCK_NUMBER_FIELD_NUMBER: _ClassVar[int]
    TX_HASH_FIELD_NUMBER: _ClassVar[int]
    TX_INDEX_FIELD_NUMBER: _ClassVar[int]
    BLOCK_HASH_FIELD_NUMBER: _ClassVar[int]
    INDEX_FIELD_NUMBER: _ClassVar[int]
    REMOVED_FIELD_NUMBER: _ClassVar[int]
    address: str
    topics: _containers.RepeatedScalarFieldContainer[str]
    data: bytes
    block_number: int
    tx_hash: str
    tx_index: int
    block_hash: str
    index: int
    removed: bool
    def __init__(self, address: _Optional[str] = ..., topics: _Optional[_Iterable[str]] = ..., data: _Optional[bytes] = ..., block_number: _Optional[int] = ..., tx_hash: _Optional[str] = ..., tx_index: _Optional[int] = ..., block_hash: _Optional[str] = ..., index: _Optional[int] = ..., removed: _Optional[bool] = ...) -> None: ...
