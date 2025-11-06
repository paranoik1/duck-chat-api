from msgspec import Struct, field

from .extra import Role
from .model_type import ModelType
from .parts import Part


# FIXME: пользователь может отправлять content в видео строки, а так же в виде списка Parts (text or image)
class Message(Struct):
    role: Role


class MessageUser(Message):
    content: str | list[Part] = ""

    @classmethod
    def create(cls, content: str | list[Part]):
        return cls(role=Role.USER, content=content)


class MessageAssistant(Message):
    content: str = ""
    parts: list[Part] = field(default_factory=list)

    @classmethod
    def create(cls, parts: list[Part], content: str = ""):
        return cls(role=Role.ASSISTANT, content=content, parts=parts)


class ToolChoice(Struct, rename="pascal"):
    # Для валидации
    news_search: bool = False
    videos_search: bool = False
    local_search: bool = False
    weather_forecast: bool = False
    # Можно использовать
    web_search: bool = False


class Customization(Struct, rename="camel", omit_defaults=True):
    assistant_role: str | None = None
    user_role: str | None = None
    assistant_name: str = ""
    user_name: str = ""
    tone: str = "Default"
    should_seek_clarity: bool = True
    length: str = "Default"
    additional_instructions: str = ""


class Metadata(Struct):
    tool_choice: ToolChoice = field(name="toolChoice", default_factory=ToolChoice)
    customization: Customization = field(default_factory=Customization)


class RequestData(Struct, rename="camel"):
    model: ModelType | str
    messages: list[Message] = field(default_factory=list)
    can_use_tools: bool = True
    can_use_approx_location: bool = True
    metadata: Metadata = field(default_factory=Metadata)

    def add_input(self, content: str | list[Part]) -> None:
        self.messages.append(MessageUser.create(content=content))

    def add_answer(self, parts: list[Part], content: str = "") -> None:
        self.messages.append(MessageAssistant.create(content=content, parts=parts))
