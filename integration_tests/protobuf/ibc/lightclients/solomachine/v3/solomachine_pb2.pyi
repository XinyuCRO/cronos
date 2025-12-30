from gogoproto import gogo_pb2 as _gogo_pb2
from google.protobuf import any_pb2 as _any_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ClientState(_message.Message):
    __slots__ = ()
    SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    IS_FROZEN_FIELD_NUMBER: _ClassVar[int]
    CONSENSUS_STATE_FIELD_NUMBER: _ClassVar[int]
    sequence: int
    is_frozen: bool
    consensus_state: ConsensusState
    def __init__(self, sequence: _Optional[int] = ..., is_frozen: _Optional[bool] = ..., consensus_state: _Optional[_Union[ConsensusState, _Mapping]] = ...) -> None: ...

class ConsensusState(_message.Message):
    __slots__ = ()
    PUBLIC_KEY_FIELD_NUMBER: _ClassVar[int]
    DIVERSIFIER_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    public_key: _any_pb2.Any
    diversifier: str
    timestamp: int
    def __init__(self, public_key: _Optional[_Union[_any_pb2.Any, _Mapping]] = ..., diversifier: _Optional[str] = ..., timestamp: _Optional[int] = ...) -> None: ...

class Header(_message.Message):
    __slots__ = ()
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    NEW_PUBLIC_KEY_FIELD_NUMBER: _ClassVar[int]
    NEW_DIVERSIFIER_FIELD_NUMBER: _ClassVar[int]
    timestamp: int
    signature: bytes
    new_public_key: _any_pb2.Any
    new_diversifier: str
    def __init__(self, timestamp: _Optional[int] = ..., signature: _Optional[bytes] = ..., new_public_key: _Optional[_Union[_any_pb2.Any, _Mapping]] = ..., new_diversifier: _Optional[str] = ...) -> None: ...

class Misbehaviour(_message.Message):
    __slots__ = ()
    SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    SIGNATURE_ONE_FIELD_NUMBER: _ClassVar[int]
    SIGNATURE_TWO_FIELD_NUMBER: _ClassVar[int]
    sequence: int
    signature_one: SignatureAndData
    signature_two: SignatureAndData
    def __init__(self, sequence: _Optional[int] = ..., signature_one: _Optional[_Union[SignatureAndData, _Mapping]] = ..., signature_two: _Optional[_Union[SignatureAndData, _Mapping]] = ...) -> None: ...

class SignatureAndData(_message.Message):
    __slots__ = ()
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    signature: bytes
    path: bytes
    data: bytes
    timestamp: int
    def __init__(self, signature: _Optional[bytes] = ..., path: _Optional[bytes] = ..., data: _Optional[bytes] = ..., timestamp: _Optional[int] = ...) -> None: ...

class TimestampedSignatureData(_message.Message):
    __slots__ = ()
    SIGNATURE_DATA_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    signature_data: bytes
    timestamp: int
    def __init__(self, signature_data: _Optional[bytes] = ..., timestamp: _Optional[int] = ...) -> None: ...

class SignBytes(_message.Message):
    __slots__ = ()
    SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    DIVERSIFIER_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    sequence: int
    timestamp: int
    diversifier: str
    path: bytes
    data: bytes
    def __init__(self, sequence: _Optional[int] = ..., timestamp: _Optional[int] = ..., diversifier: _Optional[str] = ..., path: _Optional[bytes] = ..., data: _Optional[bytes] = ...) -> None: ...

class HeaderData(_message.Message):
    __slots__ = ()
    NEW_PUB_KEY_FIELD_NUMBER: _ClassVar[int]
    NEW_DIVERSIFIER_FIELD_NUMBER: _ClassVar[int]
    new_pub_key: _any_pb2.Any
    new_diversifier: str
    def __init__(self, new_pub_key: _Optional[_Union[_any_pb2.Any, _Mapping]] = ..., new_diversifier: _Optional[str] = ...) -> None: ...
