from gogoproto import gogo_pb2 as _gogo_pb2
from ethermint.evm.v1 import chain_config_v0_pb2 as _chain_config_v0_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class V4Params(_message.Message):
    __slots__ = ()
    EVM_DENOM_FIELD_NUMBER: _ClassVar[int]
    ENABLE_CREATE_FIELD_NUMBER: _ClassVar[int]
    ENABLE_CALL_FIELD_NUMBER: _ClassVar[int]
    EXTRA_EIPS_FIELD_NUMBER: _ClassVar[int]
    CHAIN_CONFIG_FIELD_NUMBER: _ClassVar[int]
    ALLOW_UNPROTECTED_TXS_FIELD_NUMBER: _ClassVar[int]
    evm_denom: str
    enable_create: bool
    enable_call: bool
    extra_eips: ExtraEIPs
    chain_config: _chain_config_v0_pb2.V0ChainConfig
    allow_unprotected_txs: bool
    def __init__(self, evm_denom: _Optional[str] = ..., enable_create: _Optional[bool] = ..., enable_call: _Optional[bool] = ..., extra_eips: _Optional[_Union[ExtraEIPs, _Mapping]] = ..., chain_config: _Optional[_Union[_chain_config_v0_pb2.V0ChainConfig, _Mapping]] = ..., allow_unprotected_txs: _Optional[bool] = ...) -> None: ...

class ExtraEIPs(_message.Message):
    __slots__ = ()
    EIPS_FIELD_NUMBER: _ClassVar[int]
    eips: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, eips: _Optional[_Iterable[int]] = ...) -> None: ...
