from abc import ABC, abstractmethod
from aiogram import types


class BaseParser(ABC):
    base_url = None  # Установите базовый URL как атрибут класса

    def __init__(self):
        if self.base_url is None:
            raise NotImplementedError("Subclasses must define the 'base_url' attribute.")

    async def parse_categories(self, url: str) -> dict:
        pass

    async def parse_subcategories(self, url: str, mode: str = "deep") -> dict:
        pass

    async def parse_category_products(
        self,
        url: str,
        pagination: str = "?page=",
        callback_query: types.CallbackQuery = None,
        message: types.Message = None,
        text_query: str = "",
    ):
        pass

    # Обязательные методы
    @abstractmethod
    async def parse_products(
        self,
        url: str,
        data: dict,
        callback_query: types.CallbackQuery = None,
        message: types.Message = None,
        rate_limit=1,
    ) -> None:
        pass

    @abstractmethod
    async def parse_page(
        self,
        content,
        callback_query: types.CallbackQuery = None,
        message: types.Message = None,
    ):
        pass

    @abstractmethod
    async def fetch_page(self, session, url: str):
        url = url.strip().replace('%22', '')
        async with session.get(url) as response:
            return await response.text()
