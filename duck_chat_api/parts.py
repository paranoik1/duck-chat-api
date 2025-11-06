from typing import Any, Literal

from msgspec import Struct, field

from .extra import Source, StateTool


class Part(Struct, rename="camel"):
    type: str
    IS_SAVE = True

    @classmethod
    def create(cls, *args, **kwargs):
        raise NotImplementedError(cls.__name__)


class PartTool(Part, omit_defaults=True):
    tool_call_id: str
    state: StateTool

    # If state = call
    tool_arguments: str | None = None
    tool_name: str | None = None

    # if state = result
    result: str | None = None

    @classmethod
    def create(cls, **kwargs):
        return cls(type="tool-invocation", **kwargs)


class PartText(Part):
    text: str = ""

    @classmethod
    def create(cls, text: str):
        return cls(type="text", text=text)


class PartImage(Part):
    _format_image = "data:{mime_type};base64,{base64}"

    mime_type: str = "image/webp"
    image: str = ""

    @classmethod
    def create(cls, image_base64: str, mime_type: str = mime_type):
        data_image_base64 = cls._format_image.format(
            mime_type=mime_type, base64=image_base64
        )

        return cls(type="image", mime_type=mime_type, image=data_image_base64)


# Не предназначен для ручного создания
class PartSource(Part):
    IS_SAVE = False

    source: Source

    @classmethod
    def create(cls, source: Source):
        return cls(type="source", source=source)
