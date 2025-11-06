from bs4 import BeautifulSoup

from . import (DUCK_AI_URL, _accept_privacy_terms, _launch_undetected_chromium,
               xvfb, async_playwright)


@xvfb
async def get_models_page_html() -> str:
    """Get html page from duck.ai"""
    async with async_playwright() as p:
        browser = await _launch_undetected_chromium(p)
        page = await browser.new_page()
        page.set_default_timeout(10000)

        await page.goto(DUCK_AI_URL, wait_until="networkidle")

        await _accept_privacy_terms(page)

        button = page.locator("main > section > div:nth-child(2) > div > button").first
        await button.click()

        html = await page.inner_html("html") or ""

        await browser.close()
        return html


def parse_models(html: str) -> dict[str, str]:
    """Get models from html page (labels tags)"""

    # Parse the content of the webpage
    soup = BeautifulSoup(html, "html.parser")

    # Find all tags and extract their names
    # Не парсятся модели, требующие DuckDuckGo Pro
    models_inputs = soup.select("ul[role=radiogroup]:nth-child(1) input[name=model]")

    # Get models data
    data = {}
    for input in models_inputs:
        model_id = input.attrs.get("value")
        if not model_id:
            # utils_logger.error("model_id not found")
            raise ValueError("model_id не получен из атриббута value: " + str(input))
        elif not isinstance(model_id, str):
            # utils_logger.critical("model_id не является строкой (был получен {type(model_id)})")
            raise ValueError(
                f"model_id не является строкой (был получен {type(model_id)})"
            )

        model_name = "".join(
            [part.title() for part in model_id.split("/")[-1].split("-")]
        )
        data[model_name] = model_id
    return data
