import time

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By


def main():
    driver = uc.Chrome(headless=True, use_subprocess=False)
    driver.get('https://kolesa.kz/a/show/167927294')
    driver.find_element(By.CLASS_NAME, "seller-phones__show-button").click()
    time.sleep(2)
    content = driver.page_source
    driver.save_screenshot('nowsecure.png')
    print(BeautifulSoup(content, 'html.parser').prettify())


if __name__ == '__main__':
    main()
