import asyncio
from typing import Optional

import requests as rq
import aiohttp
from aiogram import types
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.common import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from parsing.parent import BaseParser
from parsing.utils import get_country_name, fetch, form_data, get_driver, modify_url_gumtreeza


class GumtreeZa(BaseParser):
    base_url = "https://www.gumtree.co.za"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.webdriver = None
        # self.webdriver = get_driver(self.base_url)

    async def parse_products(
            self,
            url: str,
            data: dict,
            callback_query: types.CallbackQuery = None,
            message: types.Message = None,
            rate_limit=1,
    ) -> None:
        print(url)
        headers = {
            "Accept-Language": "ru",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        }

        if not self.webdriver:
            self.webdriver = webdriver.Chrome()
            cookie = {
                "name": "bt_auth",
                "value": "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJib2x0LXNlcnZpY2UtYXV0aGVudGljYXRpb24iLCJqdGkiOiI2NjQ3YmYzNDU2MmUxOTYyZWJhMzc2YmEiLCJzdWIiOiIxMzMxOTA4NDYiLCJpYXQiOjE3MTU5NzgwMzYsImV4cCI6MTc0NzUxNDAzNn0.1AkodCtVN1N6DvLvngryJyR04c_T7Ja0Edo_rkQ4325RJBdsf1V17BlA_vaE5ByHu4V2IAQSkIWWYin7vNmdbA",
                "domain": ".gumtree.co.za",
                "path": "/",
                "max_age": 31536000
            }
            self.webdriver.get(self.base_url)
            self.webdriver.add_cookie(cookie)
            self.webdriver.set_page_load_timeout(10)

        driver = self.webdriver
        retries = 3

        while retries > 0:
            try:
                driver.get(url)
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "display-phone"))
                ).click()
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "real-phone"))
                )
                content = driver.page_source
                soup = BeautifulSoup(content, "lxml")
                phones = soup.find_all("span", class_="real-phone")
                data["phone"] = "\n".join([phone.text for phone in phones])
                data["price"] = soup.find("span", class_="ad-price").text.strip().replace(r'\xa0000\n    ', '')
                result = []
                attr_tags = soup.find("div", class_="attribute").find_all('dl')
                for attr_tag in attr_tags:
                    title = attr_tag.find('span', class_="name").get_text(strip=True).replace('\xa0', ' ')
                    value = attr_tag.find('span', class_="value").get_text(strip=True).replace('\xa0', ' ')
                    result.append(f"{title}: {value}")
                final_string = ", ".join(result)
                description = soup.find("div", class_="description-content").text.strip()
                data["text"] = final_string + "\n" + description
                data["country"] = get_country_name(url)
                formed_data = form_data(data)

                if callback_query:
                    await callback_query.message.answer(formed_data)
                elif message:
                    await message.answer(formed_data)

                break  # Exit loop if successful
            except TimeoutException:
                retries -= 1
                print(f"TimeoutException: retries left {retries}")
                await asyncio.sleep(2)  # Pause before retrying
            except WebDriverException as e:
                print(f"WebDriverException: {e}")
                retries -= 1
                await asyncio.sleep(2)  # Pause before retrying
            except Exception as e:
                print(f"Exception: {e}")
                retries = 0


    async def parse_page(self, content, callback_query=None, message=None):
        soup = BeautifulSoup(content, "lxml")
        print(soup.find("ul", class_="seller-phones__phones-list"))
        products = []
        tasks = []
        urls = soup.find_all('a', class_='related-ad-title')
        urls = [url.get('href') for url in urls]
        print(*urls, sep='\n')

        c = 0
        for item in soup.find_all('a', class_='related-ad-title'):
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
            else:
                raise Exception("Не на что отвечать")
            tasks.append(task)
            c += 1
            if c > 7:
                return products
            await asyncio.sleep(4)
        await asyncio.gather(*tasks)

        return products

    async def fetch_page(self, session, url: str):
        return await super().fetch_page(session, url)

    async def parse_all_pages(
            self,
            url: str,
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
            for page in range(2, 4):
                page_url = modify_url_gumtreeza(url, page, text_query)
                print(page_url)
                content = await self.fetch_page(session, f"{page_url}")
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


if __name__ == "__main__":
    j = GumtreeZa()
    # print(j.webdriver)
    print(asyncio.run(j.parse_page(rq.get("https://www.gumtree.co.za/s-all-the-ads/v1b0p1?q=toyota").text)))



