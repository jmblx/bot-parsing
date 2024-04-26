import asyncio
import json
import re

import requests as rq
import aiohttp
from aiogram import types
from bs4 import BeautifulSoup


async def parse_categories(url: str) -> dict:
    headers = {'Accept-Language': 'ru'}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as response:
            content = await response.text()
        soup = BeautifulSoup(content, 'html.parser')
        cats_block = soup.find("nav", class_="main-CatalogNavigation")#.find("nav", class_="main-CatalogNavigation")
        cats = cats_block.find_all("li")
        categories = {}
        for cat in cats:
            cat = cat.find("a")
            cat_name = cat.text.strip()
            cat_url = f'{url}{cat.get("href")}'
            categories[cat_name] = cat_url
        return categories


async def parse_subcategories(url: str, mode: str = "deep") -> dict:
    headers = {'Accept-Language': 'ru'}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as response:
            content = await response.text()
    soup = BeautifulSoup(content, 'html.parser')
    if mode == "deep":
        categories_dict = {}

        categories = soup.find_all('li', class_='category__subCategories-group')
        for category in categories:
            category_name = category.find('header').text.strip()
            sub_categories_dict = {}
            sub_categories = category.find_all('li', class_='category__subCategories-collection')

            for sub_category in sub_categories:
                sub_category_name = sub_category.find('a').text.strip()
                sub_category_link = sub_category.find('a')['href']
                sub_categories_dict[f"{sub_category_name}"] = sub_category_link

            categories_dict[category_name] = sub_categories_dict

        return categories_dict

    elif mode == "flat":
        subcats = soup.find("div", class_='category__subCategories').find_all("a")
        result = {}
        for subcat in subcats:
            theme_name = subcat.text.strip()
            theme_url = f'https://999.md{subcat.get("href")}'
            result[theme_name] = theme_url
        return result


async def fetch_page(session, url):
    async with session.get(url) as response:
        return await response.text()


async def parse_page(content, callback_query):
    soup = BeautifulSoup(content, 'html.parser')
    products = []
    for item in soup.find_all("div", class_="ads-list-photo-item-title"):
        link = item.find('a')['href']
        title = item.find('a').text.strip()
        product_info = {'link': 'https://999.md' + link, 'title': title}
        products.append(product_info)
        # Отправляем продукт пользователю по мере обработки
        await callback_query.message.answer(f"{title}: https://999.md{link}")
    return products


async def parse_category_products(url: str, callback_query: types.CallbackQuery, pagination: str = "?page="):
    headers = {'Accept-Language': 'ru'}
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = []
        for page in range(1, 2):
            page_url = f"{url}{pagination}{page}"
            content = await fetch_page(session, page_url)
            task = asyncio.create_task(parse_page(content, callback_query))
            tasks.append(task)

        # Ждем завершения всех задач
        await asyncio.gather(*tasks)


async def parse_by_query(url: str):
    headers = {'Accept-Language': 'ru'}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as response:
            content = await response.text()
        soup = BeautifulSoup(content, 'html.parser')
        products = []
        for item in soup.find_all("div", class_="ads-list-photo-item-title"):
            link = item.find('a')['href']
            title = item.find('a').text.strip()
            product_info = {'link': 'https://999.md' + link, 'title': title}


if __name__ == '__main__':
    # print(asyncio.run(parse_subcategories('https://999.md/ru/category/transport')))
    # print(asyncio.run(parse_category_products("https://999.md/ru/list/transport/cars")))
    print(asyncio.run(parse_by_query("https://999.md/ru/search?query=телевизор")))
