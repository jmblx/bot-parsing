import asyncio

import aiohttp
from aiogram import types
from bs4 import BeautifulSoup

from parsing.parent import BaseParser
from parsing.utils import get_country_name, fetch, form_data


class MD999(BaseParser):
    base_url = "https://999.md/ru"

    async def parse_categories(self, url: str) -> dict:
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
            cats_block = soup.find(
                "nav", class_="main-CatalogNavigation"
            )  # .find("nav", class_="main-CatalogNavigation")
            cats = cats_block.find_all("li")
            categories = {}
            for cat in cats:
                cat = cat.find("a")
                cat_name = cat.text.strip()
                cat_url = f'{url}{cat.get("href")}'
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
        if mode == "deep":
            categories_dict = {}

            categories = soup.find_all(
                "li", class_="category__subCategories-group"
            )
            for category in categories:
                category_name = category.find("header").text.strip()
                sub_categories_dict = {}
                sub_categories = category.find_all(
                    "li", class_="category__subCategories-collection"
                )

                for sub_category in sub_categories:
                    sub_category_name = sub_category.find("a").text.strip()
                    sub_category_link = sub_category.find("a")["href"]
                    sub_categories_dict[f"{sub_category_name}"] = (
                        sub_category_link
                    )

                categories_dict[category_name] = sub_categories_dict

            return categories_dict

        elif mode == "flat":
            subcats = soup.find(
                "div", class_="category__subCategories"
            ).find_all("a")
            result = {}
            for subcat in subcats:
                theme_name = subcat.text.strip()
                theme_url = f'https://999.md{subcat.get("href")}'
                result[theme_name] = theme_url
            return result

    async def parse_products(
        self,
        url: str,
        data: dict,
        callback_query: types.CallbackQuery = None,
        message: types.Message = None,
        rate_limit=1,
    ) -> None:
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

            main_price_element = soup.find("li", class_="is-main")
            if main_price_element:
                extracted_price = main_price_element.find(
                    class_="adPage__content__price-feature__prices__price__value"
                ).text.strip()
                extracted_currency = main_price_element.find(
                    class_="adPage__content__price-feature__prices__price__currency"
                ).text.strip()
                data["price"] = extracted_price + " " + extracted_currency

            alt_prices_elements = soup.find_all("li", class_="is-aside")
            alt_prices = []
            for price_element in alt_prices_elements:
                alt_price = price_element.find(
                    class_="adPage__content__price-feature__prices__price__value"
                ).text.strip()
                alt_currency = price_element.find(
                    class_="adPage__content__price-feature__prices__price__currency"
                ).text.strip()
                alt_prices.append(f"{alt_price} {alt_currency}")

            data["alternative_prices"] = "\n  - ".join(alt_prices)

            # Другие данные
            try:
                data["phone"] = (
                    soup.find("div", class_="adPage__content__footer__wrapper")
                    .find("a")
                    .get("href")
                    .split(":")[1]
                )
            except AttributeError:
                return
            try:
                text = (
                    soup.find("div", class_="adPage__content__inner")
                    .select('[itemprop="description"]')[0]
                    .text.strip()
                )
            except IndexError:
                text = "текста объявления не найдено или его нет"
            data["text"] = text if len(text) < 200 else text[:200] + "..."
            data["full_text"] = text
            data["country"] = get_country_name(url)
            data["date"] = soup.find(
                "div", class_="adPage__aside__stats__date"
            ).text.replace("Дата обновления: ", "")

            # Формирование и отправка сообщения
            formed_data = form_data(data)

            if callback_query:
                await callback_query.message.answer(formed_data)
            elif message:
                await message.answer(formed_data)

    async def parse_page(self, content, callback_query=None, message=None):
        soup = BeautifulSoup(content, "lxml")
        products = []
        tasks = []
        # for item in soup.find_all("div", class_="ads-list-photo-item-title"):
        c = 0
        for item in soup.find_all("li", class_="ads-list-photo-item"):
            title_block = item.find("div", class_="ads-list-photo-item-title")
            link = title_block.find("a")["href"]
            title = title_block.find("a").text.strip()

            product_info = {"link": "https://999.md" + link, "title": title}
            products.append(product_info)
            if callback_query:
                task = asyncio.create_task(
                    self.parse_products(
                        product_info["link"],
                        data=product_info,
                        callback_query=callback_query,
                    )
                )
                # await callback_query.message.answer(f"{title}: https://999.md{link}")
            elif message:
                task = asyncio.create_task(
                    self.parse_products(
                        product_info["link"],
                        data=product_info,
                        message=message,
                    )
                )
                # await message.answer(f"{title}: https://999.md{link}")
            tasks.append(task)
            c += 1
            if c > 10:
                return products

        await asyncio.gather(*tasks)

        print(products)
        return products

    async def fetch_page(self, session, url: str):
        return await super().fetch_page(session, url)

    async def parse_category_products(
        self,
        url: str,
        pagination: str = "?page=",
        callback_query: types.CallbackQuery = None,
        message: types.Message = None,
        text_query: str = "",
    ):
        headers = {
            "Accept-Language": "ru",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        }
        conn = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(
            headers=headers, trust_env=True, connector=conn
        ) as session:
            tasks = []
            for page in range(
                2,
            ):
                if callback_query:
                    page_url = f"{url}{pagination}{page}"
                else:
                    page_url = f"{url}{pagination}{page}&query={text_query}"

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

            # Ждем завершения всех задач
            await asyncio.gather(*tasks)



if __name__ == "__main__":
    parser = MD999("https://999.md/ru")
    # print(asyncio.run(parse_subcategories('https://999.md/ru/category/transport')))
    print(
        asyncio.run(
            parser.parse_category_products(
                "https://999.md/ru/search", text_query="Volkswagen Tiguan"
            )
        )
    )
    # response = rq.get("https://999.md/ru/86616025")
    # soup = BeautifulSoup(response.text, 'html.parser')
    # phone = soup.find("div", class_="adPage__content__footer__wrapper").find("a").get("href").split(":")[1]
    # print(phone)
    ...
