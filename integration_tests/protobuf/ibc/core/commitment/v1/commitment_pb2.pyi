from gogoproto import gogo_pb2 as _gogo_pb2
from cosmos.ics23.v1 import proofs_pb2 as _proofs_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class MerkleRoot(_message.Message):
    __slots__ = ()
    HASH_FIELD_NUMBER: _ClassVar[int]
    hash: bytes
    def __init__(self, hash: _Optional[bytes] = ...) -> None: ...

class MerklePrefix(_message.Message):
    __slots__ = ()
    KEY_PREFIX_FIELD_NUMBER: _ClassVar[int]
    key_prefix: bytes
    def __init__(self, key_prefix: _Optional[bytes] = ...) -> None: ...

class MerkleProof(_message.Message):
    __slots__ = ()
    PROOFS_FIELD_NUMBER: _ClassVar[int]
    proofs: _containers.RepeatedCompositeFieldContainer[_proofs_pb2.CommitmentProof]
    def __init__(self, proofs: _Optional[_Iterable[_Union[_proofs_pb2.CommitmentProof, _Mapping]]] = ...) -> None: ...
