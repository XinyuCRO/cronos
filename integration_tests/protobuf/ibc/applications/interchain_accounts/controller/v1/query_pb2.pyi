from ibc.applications.interchain_accounts.controller.v1 import controller_pb2 as _controller_pb2
from google.api import annotations_pb2 as _annotations_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class QueryInterchainAccountRequest(_message.Message):
    __slots__ = ()
    OWNER_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_ID_FIELD_NUMBER: _ClassVar[int]
    owner: str
    connection_id: str
    def __init__(self, owner: _Optional[str] = ..., connection_id: _Optional[str] = ...) -> None: ...

class QueryInterchainAccountResponse(_message.Message):
    __slots__ = ()
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    address: str
    def __init__(self, address: _Optional[str] = ...) -> None: ...

class QueryParamsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class QueryParamsResponse(_message.Message):
    __slots__ = ()
    PARAMS_FIELD_NUMBER: _ClassVar[int]
    params: _controller_pb2.Params
    def __init__(self, params: _Optional[_Union[_controller_pb2.Params, _Mapping]] = ...) -> None: ...
