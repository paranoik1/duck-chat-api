import logging
from asyncio import create_task
from contextlib import asynccontextmanager
from subprocess import Popen
from traceback import format_exc, print_exc

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel

from duck_chat import DuckChat, ModelType
from duck_chat.exceptions import ChallengeException, DuckChatException
from headers_manager import HeadersManager
from utils import get_headers


service_logger = logging.getLogger("fastapi.service")


class Prompt(BaseModel):
    content: str
    model: ModelType = ModelType.DEFAULT


def notify():
    Popen('notify-send "DuckLocalChat" "Заголовки получены и сохранены"', shell=True)


async def background_save_headers():
    service_logger.info("Запущена функция для получения headers")

    headers = await get_headers()
    service_logger.info("headers получены")

    await HeadersManager().save_headers(headers)
    service_logger.info("headers сохранен")

    notify()


@asynccontextmanager
async def lifespan(_):
    try:
        await HeadersManager().load_headers()
    except ValueError:
        await background_save_headers()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/chat", response_model=str)
async def chat(prompt: Prompt):
    headers = HeadersManager().get()

    async with DuckChat(headers, prompt.model) as duck:
        try:
            return await duck.ask_question(prompt.content)
        except ChallengeException:
            # create_task(background_save_headers())

            # raise HTTPException(
            #     418,
            #     "Произошла ошибка проверки заголовков... Была создана фоновая задача для получения новых заголовков! Попробуйте позже",
            # )

            await background_save_headers()

            headers = HeadersManager().get()
            duck.set_headers(headers)

            return await duck.ask_question(prompt.content)
        except DuckChatException:
            service_logger.critical(
                "Произошла неизвестная ошибка при отправке сообщения Duck.AI...",
                stack_info=True,
            )
            raise HTTPException(500)
