from pathlib import Path
from typing import Any
import logging
import sys
import importlib
from importlib.util import spec_from_file_location, module_from_spec
import aiofiles # type: ignore
from bs4 import BeautifulSoup
from patchright.async_api import Playwright, TimeoutError, async_playwright, BrowserContext, Page
from xvfbwrapper import Xvfb  # type: ignore
from os.path import getmtime
from time import ctime
from datetime import datetime


MODELS_TYPE_PATH = Path(__file__).parent / "duck_chat" / "models" / "model_type.py"
DUCK_AI_URL = "https://duck.ai"

utils_logger = logging.getLogger("utils")


def xvfb(func):
    async def wrapper(*args, **kwargs):
        with Xvfb():
            return await func(*args, **kwargs)

    return wrapper


async def _launch_undetected_chromium(p: Playwright) -> BrowserContext:
    return await p.chromium.launch_persistent_context(
        user_data_dir="...", channel="chromium", headless=False, no_viewport=True
    )


async def accept_privacy_terms(page: Page):
    selector = 'div[role="dialog"][aria-modal="true"] button[type="button"]'
    button = page.locator(selector)
    try:
        await button.click(timeout=2000)
    except TimeoutError:
        utils_logger.warning("Timeout error: не найдена кнопка для принятия политики конфиденциальности")


@xvfb
async def get_headers() -> dict[str, Any] | None:
    async with async_playwright() as p:
        browser = await _launch_undetected_chromium(p)
        page = await browser.new_page()

        await page.goto(DUCK_AI_URL, wait_until="networkidle")
        # with open('inner.html', "w") as fp:
        #     html = await page.inner_html('html')
        #     fp.write(html)

        await accept_privacy_terms(page)

        await page.type('textarea[name="user-prompt"]', "Hello!", delay=100)
        await page.keyboard.press("Enter")

        async with page.expect_response(
            "https://duckduckgo.com/duckchat/v1/chat"
        ) as event_response:
            response = await event_response.value

        await browser.close()

        if response.status == 200:
            # vqd = await request.header_value(vqd_header_name)
            return response.request.headers
        
        utils_logger.critical("Не удалось получить headers запроса", stack_info=True)


@xvfb
async def __get_html() -> str:
    """Get html page from duck.ai"""
    async with async_playwright() as p:
        browser = await _launch_undetected_chromium(p)
        page = await browser.new_page()
        page.set_default_timeout(10000)

        await page.goto(DUCK_AI_URL, wait_until="networkidle")

        await accept_privacy_terms(page)

        button = page.locator("main > section > div:nth-child(2) > div > button").first
        await button.click()

        html = await page.inner_html("html") or ""

        await browser.close()
        return html


def __parse_models(html: str) -> dict[str, str]:
    """Get models from html page (labels tags)"""

    # Parse the content of the webpage
    soup = BeautifulSoup(html, "html.parser")

    # Find all tags and extract their names 
    # Не парсятся модели, требующие DuckDuckGo Pro
    models_inputs = soup.select('ul[role=radiogroup]:nth-child(1) input[name=model]')

    # Get models data
    data = {}
    for input in models_inputs:
        model_id = input.attrs.get("value")
        if not model_id:
            # utils_logger.error("model_id not found")
            raise ValueError("model_id не получен из атриббута value: " + str(input))
        elif not isinstance(model_id, str):
            # utils_logger.critical("model_id не является строкой (был получен {type(model_id)})")
            raise ValueError(f"model_id не является строкой (был получен {type(model_id)})")

        model_name = "".join(
            [part.title() for part in model_id.split("/")[-1].split("-")]
        )
        data[model_name] = model_id
    return data


async def __write_models(data: dict[str, str], path: Path) -> None:
    """Generate new model_type.py"""
    async with aiofiles.open(path, "w") as f:
        await f.write("from enum import Enum\n\n\nclass ModelType(Enum):\n")
        for k, v in data.items():
            await f.write(f'    {k} = "{v}"\n')
        
        first_model = list(data.keys())[0]
        await f.write(f'    DEFAULT = {first_model}')


def __reload_models_type_module() -> None:
    module_name = "duck_chat.models.model_type"

    # Если модуль уже загружен — перезагружаем
    if module_name in sys.modules:
        importlib.reload(sys.modules[module_name])
        utils_logger.info(f"[+] Модуль {module_name} перезагружен")
    else:
        # Если не загружен — импортируем впервые
        spec = spec_from_file_location(module_name, MODELS_TYPE_PATH)
        if spec is None or spec.loader is None:
            raise FileNotFoundError(f"Не удалось загрузить модуль из {MODELS_TYPE_PATH}")
        module = module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        utils_logger.info(f"[+] Модуль {module_name} загружен впервые")


def needs_editing() -> bool:
    """    
    Логика проверки необходимости редактирования
    Возвращаем True, если редактирование необходимо, иначе False
    """
    
    mtime = getmtime(MODELS_TYPE_PATH)
    date_string = ctime(mtime)
    date_last_updated = datetime.strptime(date_string, "%a %b %d %H:%M:%S %Y")
    return date_last_updated.day != datetime.now().day


async def generate_models() -> None:
    """
    Парсит модели с Duck.ai - приводит их в нормальный вид и сохраняет в MODELS_TYPE_PATH в виде Enum класса
    """
    html = await __get_html()
    data = __parse_models(html)
    await __write_models(data, MODELS_TYPE_PATH)

    utils_logger.info(f"Новый список моделей сохранен: {MODELS_TYPE_PATH}")

    __reload_models_type_module()


if __name__ == "__main__":
    import asyncio
    from pprint import pprint

    asyncio.run(generate_models())

    # headers = asyncio.run(get_headers())
    # pprint(headers)
