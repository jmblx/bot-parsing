import pickle
import time
from selenium import webdriver
from selenium.webdriver.common.by import By

# Определите заголовки
headers = {
    "Accept-Language": "ru",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
}

# Создайте объект options и добавьте заголовки
options = webdriver.ChromeOptions()
for key, value in headers.items():
    options.add_argument(f"--{key}={value}")

# Запустите браузер с заданными опциями
driver = webdriver.Chrome(options=options)
driver.maximize_window()
driver.get("https://kolesa.kz/a/show/167310286")
# cookies = pickle.load(open("./cookies.pkl", "rb"))
# for cookie in cookies:
#     driver.add_cookie(cookie)
#     print(cookie)
driver.refresh()  # Обновите страницу, чтобы учесть новый токен
driver.find_element(By.CLASS_NAME, "seller-phones__show-button").click()
time.sleep(2)
html_source = driver.page_source

print(html_source)
time.sleep(40)
pickle.dump(driver.get_cookies(), open("cookies_kolesa.pkl", "wb"))
driver.quit()
