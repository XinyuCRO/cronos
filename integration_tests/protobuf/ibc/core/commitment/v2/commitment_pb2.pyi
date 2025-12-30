from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class MerklePath(_message.Message):
    __slots__ = ()
    KEY_PATH_FIELD_NUMBER: _ClassVar[int]
    key_path: _containers.RepeatedScalarFieldContainer[bytes]
    def __init__(self, key_path: _Optional[_Iterable[bytes]] = ...) -> None: ...
