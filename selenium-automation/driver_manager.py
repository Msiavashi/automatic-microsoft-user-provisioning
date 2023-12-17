from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import os
from config import Config

os.environ['WDM_LOG_LEVEL'] = '0'


class DriverManager:
    """Manages the Selenium driver setup and operations."""

    def __init__(self, mode="headless"):
        self.mode = mode
        self.driver = self.setup_driver()

    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--incognito")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument('--window-size=1920x1080')
        options.add_argument("--log-level=3")
        options.add_argument("--log-level=OFF")
        if self.mode == "headless":
            options.add_argument("--headless")

        options.page_load_strategy = 'eager'

        options.add_argument("--enable-logging")
        options.add_argument("--v=1")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])  # This excludes the verbose logging
        caps = DesiredCapabilities.CHROME

        driver = webdriver.Chrome(service=ChromeService(
            executable_path=Config.get_chrome_driver_path(), desired_capabilities=caps), options=options)
        return driver

    def close(self):
        self.driver.quit()
