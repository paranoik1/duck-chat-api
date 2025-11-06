from json import dumps, loads
from typing import Any

import aiofiles

DEFAULT_PATH_HEADERS_JSON = "./headers.json"


class HeadersManager:
    singleton = None

    def __new__(cls, *args, **kwargs):
        if cls.singleton is None:
            cls.singleton = super().__new__(cls)

        return cls.singleton

    def get(self) -> dict[str, Any]:
        return self._headers

    async def load_headers(self, path: str = DEFAULT_PATH_HEADERS_JSON) -> None:
        try:
            async with aiofiles.open(path) as fp:
                data = await fp.read()
                self._headers = loads(data)
        except FileNotFoundError:
            raise ValueError("Файл заголовков не найден: " + path)

    async def save_headers(
        self, headers: dict[str, Any], path: str = DEFAULT_PATH_HEADERS_JSON
    ):
        self._headers = headers
        async with aiofiles.open(path, "w") as fp:
            data = dumps(headers, indent=4)
            await fp.write(data)
