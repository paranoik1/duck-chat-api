from enum import StrEnum
from typing import Literal

from msgspec import Struct

StateTool = Literal["call", "result"]


class Source(Struct):
    url: str
    title: str
    site: str


class Role(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SOURCE = "source"
    TOOL_INVOCATION = "tool-invocation"
