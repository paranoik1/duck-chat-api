import logging

from ..utils.models import get_models_page_html, parse_models

utils_logger = logging.getLogger("service.utils")


async def generate_models() -> dict[str, str]:
    """
    Парсит модели с Duck.ai
    """
    html = await get_models_page_html()
    data = parse_models(html)

    utils_logger.info(f"Новый список моделей успешно получен")

    return data
