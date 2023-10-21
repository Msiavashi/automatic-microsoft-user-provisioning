from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


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
        if self.mode == "headless":
            options.add_argument("--headless")

        options.page_load_strategy = 'eager'

        options.add_argument("--enable-logging")
        options.add_argument("--v=1")
        caps = DesiredCapabilities.CHROME

        driver = webdriver.Chrome(service=ChromeService(
            executable_path="./chromedriver", desired_capabilities=caps), options=options)
        return driver

    def close(self):
        self.driver.quit()
