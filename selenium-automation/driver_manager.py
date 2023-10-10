from selenium import webdriver
import time
from selenium.webdriver.chrome.service import Service as ChromeService


class DriverManager:
    """Manages the Selenium driver setup and operations."""

    def __init__(self, mode="headless"):
        self.mode = mode
        self.driver = self.setup_driver()

    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--incognito")
        if self.mode == "headless":
            options.add_argument("start-maximized")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument("--headless=new")
            options.add_argument('--window-size=1920x1080')
        options.page_load_strategy = 'eager'
        driver = webdriver.Chrome(service=ChromeService(
            executable_path="./chromedriver"), options=options)
        return driver

    def close(self):
        self.driver.quit()
