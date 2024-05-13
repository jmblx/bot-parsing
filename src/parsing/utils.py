import os
import pickle
import re
import time

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


def form_data(data: dict):
    message = (
        f"<b>🛒 Название товара:</b> {data['title']}\n"
        f"<b>📅 Дата обновления:</b> {data['date']}\n"
        f"<b>🌍 Страна:</b> {data['country']}\n"
        f"<b>📞 Телефон:</b> <code>{data['phone']}</code>\n"
        f"<b>💵 Цена:</b> <code>{data.get('price', 'Договорная')}</code>\n"
        f"<b>Дополнительные цены:</b>\n  - <code>{data['alternative_prices']}</code>\n"
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
    cookies_file_path = os.path.join("parsing", "cookies_kolesa.pkl")
    cookies = pickle.load(open(cookies_file_path, "rb"))
    for cookie in cookies:
        driver.add_cookie(cookie)
    # pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))
    return driver
