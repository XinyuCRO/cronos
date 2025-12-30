from gogoproto import gogo_pb2 as _gogo_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Params(_message.Message):
    __slots__ = ()
    SEND_ENABLED_FIELD_NUMBER: _ClassVar[int]
    RECEIVE_ENABLED_FIELD_NUMBER: _ClassVar[int]
    send_enabled: bool
    receive_enabled: bool
    def __init__(self, send_enabled: _Optional[bool] = ..., receive_enabled: _Optional[bool] = ...) -> None: ...

class Hop(_message.Message):
    __slots__ = ()
    PORT_ID_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_ID_FIELD_NUMBER: _ClassVar[int]
    port_id: str
    channel_id: str
    def __init__(self, port_id: _Optional[str] = ..., channel_id: _Optional[str] = ...) -> None: ...
