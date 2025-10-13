from types import TracebackType
from typing import Any, AsyncGenerator, Self

import aiohttp
import msgspec

from .exceptions import (ChallengeException, ConversationLimitException,
                         DuckChatException, RatelimitException)
from .models import History, ModelType


class DuckChat:
    CHAT_URL = "https://duckduckgo.com/duckchat/v1/chat"

    def __init__(
        self,
        headers: dict[str, Any],
        model: ModelType,
        session: aiohttp.ClientSession | None = None,
        **client_session_kwargs,
    ) -> None:
        self._headers = headers

        self.history = History(model, [])

        self._session = session or aiohttp.ClientSession(**client_session_kwargs)

        self.__encoder = msgspec.json.Encoder()
        self.__decoder = msgspec.json.Decoder()

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

    async def __stream_events(
        self, response: aiohttp.ClientResponse
    ) -> AsyncGenerator[dict[str, Any]]:
        async for line in response.content:
            line = line.decode("utf8")
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
                data = self.__decoder.decode(chunk)
                yield data
            except Exception:
                raise DuckChatException(f"Couldn't parse body={chunk}")

    @staticmethod
    def __check_and_raise_error(event: dict[str, Any]):
        if event.get("action") == "error":
            err_message = event.get("type", str(event))
            if err_message == "ERR_CONVERSATION_LIMIT":
                raise ConversationLimitException(err_message)
            elif err_message == "ERR_CHALLENGE":
                raise ChallengeException(err_message)

            raise DuckChatException(err_message)

    async def _get_answer(self) -> str:
        """Get message answer from chatbot"""
        data = self.__encoder.encode(self.history)

        async with self._session.post(
            self.CHAT_URL, headers=self._headers, data=data
        ) as response:
            if response.status == 429:
                raise RatelimitException(response.content)

            answer = []

            async for event in self.__stream_events(response):
                self.__check_and_raise_error(event)

                answer.append(event.get("message", ""))

        return "".join(answer)

    async def ask_question(self, query: str) -> str:
        """Get answer from chat AI"""
        self.history.add_input(query)

        message = await self._get_answer()

        self.history.add_answer(message)
        return message

    async def ask_question_stream(self, query: str) -> AsyncGenerator[str, None]:
        """Stream answer from chat AI"""
        self.history.add_input(query)

        message_list = []
        async for event in self.__stream_events():
            self.__check_and_raise_error(event)

            message = event.get("message")
            yield message

            message_list.append(message)

        self.history.add_answer("".join(message_list))
