import logging
import os

try:
    from patchright.async_api import BrowserContext, Page, Playwright, TimeoutError, async_playwright
    from xvfbwrapper import Xvfb  # type: ignore
except ImportError:
    raise ImportError("Не были установлены пакеты из utils группы")

DUCK_AI_URL = "https://duck.ai"

utils_logger = logging.getLogger("utils")


os.environ["XDG_SESSION_TYPE"] = "x11"


def xvfb(func):
    async def wrapper(*args, **kwargs):
        with Xvfb():
            return await func(*args, **kwargs)

    return wrapper


async def _launch_undetected_chromium(p: Playwright) -> BrowserContext:
    return await p.chromium.launch_persistent_context(
        user_data_dir="...", channel="chromium", headless=False, no_viewport=True
    )


async def _accept_privacy_terms(page: Page):
    selector = 'div[role="dialog"][aria-modal="true"] button[type="button"]'
    button = page.locator(selector)
    try:
        await button.click(timeout=2000)
    except TimeoutError:
        utils_logger.warning(
            "Timeout error: не найдена кнопка для принятия политики конфиденциальности"
        )
