import os
import pickle
import re
import time
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import pycountry
from selenium import webdriver
from selenium.webdriver.common.by import By


async def fetch(url, session, semaphore):
    async with semaphore:
        async with session.get(url) as response:
            return await response.text()


def get_country_name(url):
    match_country = re.search(r"(?<=\.)([a-z]{2})(?=/|$)", url)

    if match_country:
        country = match_country.group(1)
        country.upper()
        country = pycountry.countries.get(alpha_2=country)
        return country.name if country else "Не опредлено"
    else:
        return "Не опредлено"


def form_data(data: dict, text_limit: int = 200) -> str:
    data["text"] = data["text"] if len(data["text"]) < text_limit else data["text"][:text_limit] + "..."
    required = ['title', 'date', 'country', 'phone', 'price', 'link']
    for key in required:
        if key not in data:
            data[key] = "Нет данных"
    if data.get('alternative_prices', None):
        alt = f"<b>Дополнительные цены:</b>\n  - <code>{data['alternative_prices']}</code>\n"
    else:
        alt = ""

    message = (
        f"<b>🛒 Название товара:</b> {data['title']}\n"
        f"<b>📅 Дата обновления:</b> {data['date']}\n"
        f"<b>🌍 Страна:</b> {data['country']}\n"
        f"<b>📞 Телефоны:</b> <code>{data['phone']}</code>\n"
        f"<b>💵 Цена:</b> <code>{data.get('price', 'Договорная')}</code>\n"
        f"{alt}"
        f"<b>🔗 Ссылка на объявление:</b> {data['link']}\n"
        f"<b>📝 Описание:</b>\n{data['text']}\n"
    )
    return message


def normalize_url(url: str):
    # if not url.startswith("http"):
    #     url = f"https://{url}"
    url = url.replace("%22", "").replace('"', '')
    url = f"https://999.md{url}" if "https" not in url else url
    return url


def get_driver(url: str):
    headers = {
        "Accept-Language": "ru",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
    }

    options = webdriver.ChromeOptions()
    for key, value in headers.items():
        options.add_argument(f"--{key}={value}")

    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    driver.get(url)
    # cookies_file_path = os.path.join("parsing", "cookies_kolesa.pkl")
    # cookies = pickle.load(open(cookies_file_path, "rb"))
    # for cookie in cookies:
    #     driver.add_cookie(cookie)
    # pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))
    return driver


def modify_url_gumtreeza(url, page, q_param):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    # Формирование нового пути с учётом номера страницы
    new_path = f"/s-all-the-ads/page-{page}/v1b0p{page}"

    # Сборка нового URL
    new_url = urlunparse(parsed_url._replace(path=new_path, query=urlencode({'q': q_param})))
    return new_url


