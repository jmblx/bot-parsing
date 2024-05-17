import asyncio
from typing import Optional

import requests as rq
import aiohttp
from aiogram import types
from bs4 import BeautifulSoup
import pickle
import time
from selenium import webdriver
from selenium.webdriver.common.by import By

from parsing.parent import BaseParser
from parsing.utils import get_country_name, fetch, form_data, get_driver


class KolesaKz(BaseParser):
    base_url = "https://kolesa.kz"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.webdriver = get_driver(self.base_url)

    async def parse_categories(self, url: Optional[str] = None) -> dict:
        url = self.base_url if url is None else url
        headers = {
            "Accept-Language": "ru",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        }
        conn = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(
            headers=headers, trust_env=True, connector=conn
        ) as session:
            async with session.get(url, ssl=False) as response:
                content = await response.text()
            soup = BeautifulSoup(content, "html.parser")
            cats = soup.find_all("li", class_="main-menu__item")
            categories = {}
            for cat in cats:
                cat = cat.find("a")
                cat_name = cat.text.strip()
                cat_url = f'{url}{cat.get("href")}'
                response = await session.get(cat_url)
                soup = BeautifulSoup(await response.text(), "html.parser")
                if soup.find("div", class_="menu-container"):
                    categories[cat_name] = cat_url

        return categories

    async def parse_subcategories(self, url: str, mode: str = "deep") -> dict:
        headers = {
            "Accept-Language": "ru",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        }
        conn = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(
            headers=headers, trust_env=True, connector=conn
        ) as session:
            async with session.get(url) as response:
                content = await response.text()
        soup = BeautifulSoup(content, "html.parser")
        subcategories_dict = {}

        subcategories = soup.find_all(
            "span", class_="action-link"
        )
        for subcategory in subcategories:
            subcategories_dict[subcategory.text.strip()] = f'{self.base_url}/{subcategory.get("data-alias")}'

        return subcategories_dict

    async def parse_products(
        self,
        url: str,
        data: dict,
        callback_query: types.CallbackQuery = None,
        message: types.Message = None,
        rate_limit=1,
    ) -> None:
        # driver = self.webdriver
        # driver.get(url)
        # driver.find_element(By.CLASS_NAME, "seller-phones__show-button").click()
        # time.sleep(2)
        # content = driver.page_source
        headers = {
            "Accept-Language": "ru",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        }
        conn = aiohttp.TCPConnector(ssl=False)
        semaphore = asyncio.Semaphore(rate_limit)
        async with aiohttp.ClientSession(
            headers=headers, trust_env=True, connector=conn
        ) as session:
            content = await fetch(url, session, semaphore)

        soup = BeautifulSoup(content, "lxml")
        # print(soup, soup.find("ul", class_="seller-phones__phones-list").find_all("li"), soup.find("div", class_="offer__price").text.strip(), sep="\n")
        # phones = soup.find("ul", class_="seller-phones__phones-list").find_all("li")
        # data["phone"] = "\n".join([phone.text for phone in phones])
        data["price"] = soup.find("div", class_="offer__price").text.strip().replace(r'\xa0000\n    ','')
        result = []
        dl_tags = soup.find("div", class_="offer__sidebar-info").find_all('dl')
        for dl in dl_tags:
            title = dl.find('dt').get_text(strip=True).replace('\xa0', ' ')  # Убрать спецсимволы и пробелы
            value = dl.find('dd').get_text(strip=True).replace('\xa0', ' ')
            result.append(f"{title}: {value}")
        final_string = ", ".join(result)
        description = soup.find("div", class_="text").text.strip()
        data["text"] = final_string + "\n" + description
        data["country"] = get_country_name(url)
        formed_data = form_data(data)

        if callback_query:
            await callback_query.message.answer(formed_data)
        elif message:
            await message.answer(formed_data)
        # print(data)
        # main_price_element = soup.find("li", class_="is-main")
        # if main_price_element:
        #     extracted_price = main_price_element.find(
        #         class_="adPage__content__price-feature__prices__price__value"
        #     ).text.strip()
        #     extracted_currency = main_price_element.find(
        #         class_="adPage__content__price-feature__prices__price__currency"
        #     ).text.strip()
        #     data["price"] = extracted_price + " " + extracted_currency
        #
        # alt_prices_elements = soup.find_all("li", class_="is-aside")
        # alt_prices = []
        # for price_element in alt_prices_elements:
        #     alt_price = price_element.find(
        #         class_="adPage__content__price-feature__prices__price__value"
        #     ).text.strip()
        #     alt_currency = price_element.find(
        #         class_="adPage__content__price-feature__prices__price__currency"
        #     ).text.strip()
        #     alt_prices.append(f"{alt_price} {alt_currency}")
        #
        # data["alternative_prices"] = "\n  - ".join(alt_prices)
        #
        # # Другие данные
        # try:
        #     data["phone"] = (
        #         soup.find("div", class_="adPage__content__footer__wrapper")
        #         .find("a")
        #         .get("href")
        #         .split(":")[1]
        #     )
        # except AttributeError:
        #     return
        # try:
        #     text = (
        #         soup.find("div", class_="adPage__content__inner")
        #         .select('[itemprop="description"]')[0]
        #         .text.strip()
        #     )
        # except IndexError:
        #     text = "текста объявления не найдено или его нет"
        # data["text"] = text if len(text) < 200 else text[:200] + "..."
        # data["full_text"] = text
        # data["country"] = get_country_name(url)
        # data["date"] = soup.find(
        #     "div", class_="adPage__aside__stats__date"
        # ).text.replace("Дата обновления: ", "")
        #
        # # Формирование и отправка сообщения
        # formed_data = form_data(data)
        #
        # if callback_query:
        #     await callback_query.message.answer(formed_data)
        # elif message:
        #     await message.answer(formed_data)

    async def parse_page(self, content, callback_query=None, message=None):

        soup = BeautifulSoup(content, "lxml")
        products = []
        tasks = []
        c = 0
        for item in soup.find_all("a", class_="a-card__link"):
            link = item.get("href")
            title = item.text.strip()

            product_info = {"link": f"{self.base_url}{link}", "title": title}
            products.append(product_info)
            if callback_query:
                task = asyncio.create_task(
                    self.parse_products(
                        product_info["link"],
                        data=product_info,
                        callback_query=callback_query,
                    )
                )
            elif message:
                task = asyncio.create_task(
                    self.parse_products(
                        product_info["link"],
                        data=product_info,
                        message=message,
                    )
                )
            tasks.append(task)
            c += 1
            if c > 7:
                return products
        await asyncio.gather(*tasks)

        return products

    async def fetch_page(self, session, url: str):
        return await super().fetch_page(session, url)

    async def parse_category_products(
        self,
        url: str,
        pagination: str = "page=",
        callback_query: types.CallbackQuery = None,
        message: types.Message = None,
        text_query: str = "",
    ):
        headers = {
            "Accept-Language": "ru",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
        }
        conn = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(
            headers=headers, trust_env=True, connector=conn
        ) as session:
            tasks = []
            for page in range(
                2, 4
            ):
                if callback_query:
                    page_url = f"{url}{pagination}{page}"
                else:
                    page_url = f"{url}{text_query}&{pagination}{page}"

                print(page_url)
                content = await self.fetch_page(session, page_url)
                if callback_query:
                    task = asyncio.create_task(
                        self.parse_page(content, callback_query=callback_query)
                    )
                else:
                    task = asyncio.create_task(
                        self.parse_page(content, message=message)
                    )
                tasks.append(task)

            await asyncio.gather(*tasks)
            # self.webdriver.quit()


if __name__ == "__main__":
    # j = KolesaKz()
    # print(j.webdriver)
    # print(asyncio.run(j.parse_categories("https://kolesa.kz")))
    import pickle
    import requests

    # Загрузите cookies из файла
    with open('cookies_kolesa.pkl', 'rb') as f:
        cookies = pickle.load(f)

    # Создайте сессию requests
    session = requests.Session()
    print(cookies)
    # session.cookies.update(cookies)

    # Теперь вы можете использовать сессию для отправки запросов, которые включают ваши cookies
    response = session.get("https://kolesa.kz/a/show/170159273")
    soup = BeautifulSoup(response.content, "lxml")
    print(soup.find("ul", class_="seller-phones__phones-list"))

