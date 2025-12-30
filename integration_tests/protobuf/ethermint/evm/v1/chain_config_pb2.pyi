from gogoproto import gogo_pb2 as _gogo_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class ChainConfig(_message.Message):
    __slots__ = ()
    HOMESTEAD_BLOCK_FIELD_NUMBER: _ClassVar[int]
    DAO_FORK_BLOCK_FIELD_NUMBER: _ClassVar[int]
    DAO_FORK_SUPPORT_FIELD_NUMBER: _ClassVar[int]
    EIP150_BLOCK_FIELD_NUMBER: _ClassVar[int]
    EIP150_HASH_FIELD_NUMBER: _ClassVar[int]
    EIP155_BLOCK_FIELD_NUMBER: _ClassVar[int]
    EIP158_BLOCK_FIELD_NUMBER: _ClassVar[int]
    BYZANTIUM_BLOCK_FIELD_NUMBER: _ClassVar[int]
    CONSTANTINOPLE_BLOCK_FIELD_NUMBER: _ClassVar[int]
    PETERSBURG_BLOCK_FIELD_NUMBER: _ClassVar[int]
    ISTANBUL_BLOCK_FIELD_NUMBER: _ClassVar[int]
    MUIR_GLACIER_BLOCK_FIELD_NUMBER: _ClassVar[int]
    BERLIN_BLOCK_FIELD_NUMBER: _ClassVar[int]
    LONDON_BLOCK_FIELD_NUMBER: _ClassVar[int]
    ARROW_GLACIER_BLOCK_FIELD_NUMBER: _ClassVar[int]
    GRAY_GLACIER_BLOCK_FIELD_NUMBER: _ClassVar[int]
    MERGE_NETSPLIT_BLOCK_FIELD_NUMBER: _ClassVar[int]
    SHANGHAI_TIME_FIELD_NUMBER: _ClassVar[int]
    CANCUN_TIME_FIELD_NUMBER: _ClassVar[int]
    PRAGUE_TIME_FIELD_NUMBER: _ClassVar[int]
    homestead_block: str
    dao_fork_block: str
    dao_fork_support: bool
    eip150_block: str
    eip150_hash: str
    eip155_block: str
    eip158_block: str
    byzantium_block: str
    constantinople_block: str
    petersburg_block: str
    istanbul_block: str
    muir_glacier_block: str
    berlin_block: str
    london_block: str
    arrow_glacier_block: str
    gray_glacier_block: str
    merge_netsplit_block: str
    shanghai_time: str
    cancun_time: str
    prague_time: str
    def __init__(self, homestead_block: _Optional[str] = ..., dao_fork_block: _Optional[str] = ..., dao_fork_support: _Optional[bool] = ..., eip150_block: _Optional[str] = ..., eip150_hash: _Optional[str] = ..., eip155_block: _Optional[str] = ..., eip158_block: _Optional[str] = ..., byzantium_block: _Optional[str] = ..., constantinople_block: _Optional[str] = ..., petersburg_block: _Optional[str] = ..., istanbul_block: _Optional[str] = ..., muir_glacier_block: _Optional[str] = ..., berlin_block: _Optional[str] = ..., london_block: _Optional[str] = ..., arrow_glacier_block: _Optional[str] = ..., gray_glacier_block: _Optional[str] = ..., merge_netsplit_block: _Optional[str] = ..., shanghai_time: _Optional[str] = ..., cancun_time: _Optional[str] = ..., prague_time: _Optional[str] = ...) -> None: ...
