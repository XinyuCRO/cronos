from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RelayByTxRequest(_message.Message):
    __slots__ = ("src_chain", "dst_chain", "source_tx_ids", "timeout_tx_ids", "src_client_id", "dst_client_id", "src_packet_sequences", "dst_packet_sequences")
    SRC_CHAIN_FIELD_NUMBER: _ClassVar[int]
    DST_CHAIN_FIELD_NUMBER: _ClassVar[int]
    SOURCE_TX_IDS_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_TX_IDS_FIELD_NUMBER: _ClassVar[int]
    SRC_CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    DST_CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    SRC_PACKET_SEQUENCES_FIELD_NUMBER: _ClassVar[int]
    DST_PACKET_SEQUENCES_FIELD_NUMBER: _ClassVar[int]
    src_chain: str
    dst_chain: str
    source_tx_ids: _containers.RepeatedScalarFieldContainer[bytes]
    timeout_tx_ids: _containers.RepeatedScalarFieldContainer[bytes]
    src_client_id: str
    dst_client_id: str
    src_packet_sequences: _containers.RepeatedScalarFieldContainer[int]
    dst_packet_sequences: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, src_chain: _Optional[str] = ..., dst_chain: _Optional[str] = ..., source_tx_ids: _Optional[_Iterable[bytes]] = ..., timeout_tx_ids: _Optional[_Iterable[bytes]] = ..., src_client_id: _Optional[str] = ..., dst_client_id: _Optional[str] = ..., src_packet_sequences: _Optional[_Iterable[int]] = ..., dst_packet_sequences: _Optional[_Iterable[int]] = ...) -> None: ...

class RelayByTxResponse(_message.Message):
    __slots__ = ("tx", "address")
    TX_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    tx: bytes
    address: str
    def __init__(self, tx: _Optional[bytes] = ..., address: _Optional[str] = ...) -> None: ...

class CreateClientRequest(_message.Message):
    __slots__ = ("src_chain", "dst_chain", "parameters")
    class ParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    SRC_CHAIN_FIELD_NUMBER: _ClassVar[int]
    DST_CHAIN_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    src_chain: str
    dst_chain: str
    parameters: _containers.ScalarMap[str, str]
    def __init__(self, src_chain: _Optional[str] = ..., dst_chain: _Optional[str] = ..., parameters: _Optional[_Mapping[str, str]] = ...) -> None: ...

class CreateClientResponse(_message.Message):
    __slots__ = ("tx", "address")
    TX_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    tx: bytes
    address: str
    def __init__(self, tx: _Optional[bytes] = ..., address: _Optional[str] = ...) -> None: ...

class UpdateClientRequest(_message.Message):
    __slots__ = ("src_chain", "dst_chain", "dst_client_id")
    SRC_CHAIN_FIELD_NUMBER: _ClassVar[int]
    DST_CHAIN_FIELD_NUMBER: _ClassVar[int]
    DST_CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    src_chain: str
    dst_chain: str
    dst_client_id: str
    def __init__(self, src_chain: _Optional[str] = ..., dst_chain: _Optional[str] = ..., dst_client_id: _Optional[str] = ...) -> None: ...

class UpdateClientResponse(_message.Message):
    __slots__ = ("tx", "address")
    TX_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    tx: bytes
    address: str
    def __init__(self, tx: _Optional[bytes] = ..., address: _Optional[str] = ...) -> None: ...

class InfoRequest(_message.Message):
    __slots__ = ("src_chain", "dst_chain")
    SRC_CHAIN_FIELD_NUMBER: _ClassVar[int]
    DST_CHAIN_FIELD_NUMBER: _ClassVar[int]
    src_chain: str
    dst_chain: str
    def __init__(self, src_chain: _Optional[str] = ..., dst_chain: _Optional[str] = ...) -> None: ...

class InfoResponse(_message.Message):
    __slots__ = ("target_chain", "source_chain", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    TARGET_CHAIN_FIELD_NUMBER: _ClassVar[int]
    SOURCE_CHAIN_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    target_chain: Chain
    source_chain: Chain
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, target_chain: _Optional[_Union[Chain, _Mapping]] = ..., source_chain: _Optional[_Union[Chain, _Mapping]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class Chain(_message.Message):
    __slots__ = ("chain_id", "ibc_version", "ibc_contract")
    CHAIN_ID_FIELD_NUMBER: _ClassVar[int]
    IBC_VERSION_FIELD_NUMBER: _ClassVar[int]
    IBC_CONTRACT_FIELD_NUMBER: _ClassVar[int]
    chain_id: str
    ibc_version: str
    ibc_contract: str
    def __init__(self, chain_id: _Optional[str] = ..., ibc_version: _Optional[str] = ..., ibc_contract: _Optional[str] = ...) -> None: ...
