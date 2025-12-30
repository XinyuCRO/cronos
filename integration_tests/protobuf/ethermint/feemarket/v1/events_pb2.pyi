from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class EventFeeMarket(_message.Message):
    __slots__ = ()
    BASE_FEE_FIELD_NUMBER: _ClassVar[int]
    base_fee: str
    def __init__(self, base_fee: _Optional[str] = ...) -> None: ...

class EventBlockGas(_message.Message):
    __slots__ = ()
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    height: str
    amount: str
    def __init__(self, height: _Optional[str] = ..., amount: _Optional[str] = ...) -> None: ...
