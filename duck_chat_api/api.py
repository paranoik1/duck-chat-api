import json
from types import TracebackType
from typing import Any, AsyncGenerator, Self

import aiohttp
import msgspec

from .event import Error, Event, MessageEvent, Part, SourceEvent, ToolEvent
from .exceptions import ERROR_MAPPING, DuckChatException, RatelimitException
from .request_data import (Customization, Metadata, ModelType, RequestData,
                           ToolChoice)


class DuckChat:
    CHAT_URL = "https://duckduckgo.com/duckchat/v1/chat"

    def __init__(
        self,
        headers: dict[str, Any],
        model: ModelType | str,
        request_data: RequestData | None = None,
        session: aiohttp.ClientSession | None = None,
        **client_session_kwargs,
    ) -> None:
        self._headers = headers

        self.request_data = request_data or RequestData(model)

        self._session = session or aiohttp.ClientSession(**client_session_kwargs)

        self.__encoder = msgspec.json.Encoder()
        self.__decoder = msgspec.json.Decoder(
            type=ToolEvent | MessageEvent | SourceEvent
        )

    def set_headers(self, headers: dict[str, Any]) -> None:
        self._headers = headers

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ) -> None:
        await self._session.__aexit__(exc_type, exc_value, traceback)

    async def __stream_data(
        self, response: aiohttp.ClientResponse
    ) -> AsyncGenerator[Event | Error]:
        async for line_bytes in response.content:
            line = line_bytes.decode("utf8")
            chunk = line

            if line.startswith("data: "):
                chunk = line[6:]
                if chunk.startswith("[DONE]"):
                    break
                elif chunk.startswith("[PING]"):
                    continue
                elif chunk.startswith("[CHAT_TITLE:") and chunk.endswith("]\n"):
                    continue
            elif line in {"\n", "\r", "\r\n"}:
                continue

            try:
                data = json.loads(chunk)
                if data.get("action") == "error":
                    yield msgspec.json.decode(chunk, type=Error)
                    break

                event = self.__decoder.decode(chunk)
                yield event
            except Exception:
                raise DuckChatException(f"Couldn't parse body={chunk}")

    @staticmethod
    def __raise_error(error: Error):
        err_message = error.type

        exception = ERROR_MAPPING.get(err_message, DuckChatException)

        raise exception(err_message)

    async def _request_api(self) -> AsyncGenerator[Event]:
        """Get message answer from chatbot"""
        data = self.__encoder.encode(self.request_data)

        async with self._session.post(
            self.CHAT_URL, headers=self._headers, data=data
        ) as response:
            if response.status == 429:
                raise RatelimitException(response.content)

            async for event_or_error in self.__stream_data(response):
                if isinstance(event_or_error, Error):
                    self.__raise_error(event_or_error)
                    # Нужен лишь для корректной типизации mypy в коде
                    break

                event = event_or_error
                yield event

    def _prepare_request_data(
        self, query: str | list[Part], web_search: bool = False, **customization_kwargs
    ) -> None:
        self.request_data.add_input(query)

        self.request_data.metadata.tool_choice.web_search = web_search
        self.request_data.metadata.customization = Customization(**customization_kwargs)

    async def ask_question(
        self, query: str | list[Part], web_search: bool = False, **customization_kwargs
    ) -> AsyncGenerator[Part]:
        """Get answer from chat AI"""
        self._prepare_request_data(query, web_search=web_search, **customization_kwargs)

        parts = []
        async for event in self._request_api():
            part = event.to_part()
            if part.IS_SAVE:
                parts.append(part)

            yield part

        self.request_data.add_answer(parts=parts, content="")
