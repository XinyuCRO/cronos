from gogoproto import gogo_pb2 as _gogo_pb2
from ethermint.evm.v1 import chain_config_pb2 as _chain_config_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TraceConfig(_message.Message):
    __slots__ = ()
    TRACER_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    REEXEC_FIELD_NUMBER: _ClassVar[int]
    DISABLE_STACK_FIELD_NUMBER: _ClassVar[int]
    DISABLE_STORAGE_FIELD_NUMBER: _ClassVar[int]
    DEBUG_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    OVERRIDES_FIELD_NUMBER: _ClassVar[int]
    ENABLE_MEMORY_FIELD_NUMBER: _ClassVar[int]
    ENABLE_RETURN_DATA_FIELD_NUMBER: _ClassVar[int]
    TRACER_JSON_CONFIG_FIELD_NUMBER: _ClassVar[int]
    STATE_OVERRIDES_FIELD_NUMBER: _ClassVar[int]
    BLOCK_OVERRIDES_FIELD_NUMBER: _ClassVar[int]
    tracer: str
    timeout: str
    reexec: int
    disable_stack: bool
    disable_storage: bool
    debug: bool
    limit: int
    overrides: _chain_config_pb2.ChainConfig
    enable_memory: bool
    enable_return_data: bool
    tracer_json_config: str
    state_overrides: bytes
    block_overrides: bytes
    def __init__(self, tracer: _Optional[str] = ..., timeout: _Optional[str] = ..., reexec: _Optional[int] = ..., disable_stack: _Optional[bool] = ..., disable_storage: _Optional[bool] = ..., debug: _Optional[bool] = ..., limit: _Optional[int] = ..., overrides: _Optional[_Union[_chain_config_pb2.ChainConfig, _Mapping]] = ..., enable_memory: _Optional[bool] = ..., enable_return_data: _Optional[bool] = ..., tracer_json_config: _Optional[str] = ..., state_overrides: _Optional[bytes] = ..., block_overrides: _Optional[bytes] = ...) -> None: ...
