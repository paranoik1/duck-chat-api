import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, UploadFile, Form
from pydantic import BaseModel

from duck_chat_api import DuckChat, ModelType, PartText, PartSource, PartImage, Part
from duck_chat_api.exceptions import ChallengeException, DuckChatException, RatelimitException
from duck_chat_api.service.headers_manager import HeadersManager
from duck_chat_api.utils.headers import get_headers
from base64 import b64encode

# from subprocess import Popen



# from .utils import generate_models

service_logger = logging.getLogger("fastapi.service")
# models: dict[str, str] = {}


class Prompt(BaseModel):
    content: str
    model: ModelType | str = ModelType.DEFAULT
    web_search: bool = False



# def notify():
#     Popen('notify-send "DuckLocalChat" "Заголовки получены и сохранены"', shell=True)


async def task_save_headers() -> dict[str, Any]:
    service_logger.info("Запущена функция для получения headers")

    headers = await get_headers()
    service_logger.info("headers получены")

    await HeadersManager().save_headers(headers)
    service_logger.info("headers сохранен")

    # notify()
    return headers


@asynccontextmanager
async def lifespan(_):
    try:
        await HeadersManager().load_headers()
    except ValueError:
        await task_save_headers()

    yield


app = FastAPI(lifespan=lifespan)


async def _duck_chat(duck: DuckChat, query: list[Part], web_search: bool, *, count: int = 0) -> str:
    try:
        answer = ""
        async for part in duck.ask_question(query, web_search):
            if isinstance(part, PartText):
                answer += part.text
            elif isinstance(part, PartSource):
                answer += "\n" + part.source.title + ": " + part.source.url

        return answer
    except (ChallengeException, RatelimitException) as ex:
        if count >= 3:
            raise ex

        headers = await task_save_headers()
        duck.set_headers(headers)
        count += 1
        return await _duck_chat(duck, query, web_search, count=count)
    except DuckChatException as ex:
        err_message = ex.args[0]

        service_logger.critical(
            "Произошла ошибка: " + err_message,
            stack_info=True,
        )
        raise HTTPException(500, detail=err_message)


@app.post("/chat", response_model=str)
async def chat(content: str = Form(), model: str | ModelType = Form(), web_search: bool = Form(False), file: UploadFile | None = None):
    headers = HeadersManager().get()

    query = [
        PartText.create(content),
    ]
    if file:
        image = await file.read()
        query.append(
            PartImage.create(
                b64encode(image).decode()
            )
        )

    async with DuckChat(headers, model) as duck:
        return await _duck_chat(duck, query, web_search)
