from ethermint.evm.v1 import log_pb2 as _log_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TransactionLogs(_message.Message):
    __slots__ = ()
    HASH_FIELD_NUMBER: _ClassVar[int]
    LOGS_FIELD_NUMBER: _ClassVar[int]
    hash: str
    logs: _containers.RepeatedCompositeFieldContainer[_log_pb2.Log]
    def __init__(self, hash: _Optional[str] = ..., logs: _Optional[_Iterable[_Union[_log_pb2.Log, _Mapping]]] = ...) -> None: ...
