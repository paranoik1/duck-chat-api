from typing import Any

from . import (DUCK_AI_URL, _accept_privacy_terms, _launch_undetected_chromium,
               utils_logger, xvfb, async_playwright)


@xvfb
async def get_headers() -> dict[str, Any]:
    async with async_playwright() as p:
        browser = await _launch_undetected_chromium(p)
        page = await browser.new_page()

        await page.goto(DUCK_AI_URL, wait_until="networkidle")

        await _accept_privacy_terms(page)

        await page.type('textarea[name="user-prompt"]', "Hello!", delay=100)
        await page.keyboard.press("Enter")

        async with page.expect_response(
            "https://duckduckgo.com/duckchat/v1/chat"
        ) as event_response:
            response = await event_response.value

        await browser.close()

        utils_logger.debug("Получен ответ: " + str(response.status))
        utils_logger.debug(response.headers)

        if response.status == 200:
            return response.request.headers

        raise ValueError("Не удалось получить headers запроса")
