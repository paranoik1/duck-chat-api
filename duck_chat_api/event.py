from typing import Any

from msgspec import Struct

from .extra import Source, StateTool
from .parts import Part, PartSource, PartText, PartTool


class Error(Struct, tag="error", tag_field="action"):
    status: int
    type: str


class Event(Struct, rename="camel", tag_field="role"):
    id: str
    created: float

    def to_part(self) -> Part:
        raise NotImplementedError(self.__class__.__name__)


class MessageEvent(Event, tag="assistant", tag_field="role"):
    model: str
    message: str

    def to_part(self) -> PartText:
        return PartText.create(self.message)


class ToolEvent(Event, tag="tool-invocation", tag_field="role", omit_defaults=True):
    tool_call_id: str
    state: StateTool

    # If state = call
    tool_arguments: str | None = None
    tool_name: str | None = None

    # if state = result
    result: str | None = None

    def to_part(self) -> PartTool:
        return PartTool.create(
            tool_call_id=self.tool_call_id,
            state=self.state,
            tool_arguments=self.tool_arguments,
            tool_name=self.tool_name,
            result=self.result,
        )


class SourceEvent(Event, tag="source", tag_field="role"):
    source: Source
    tool_call_id: str

    # FIXME: В Duck.ai Source сохранается в историю (в список messages)
    def to_part(self) -> PartSource:
        return PartSource.create(self.source)
