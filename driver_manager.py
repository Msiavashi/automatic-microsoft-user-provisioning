import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService


class DriverManager:
    """Manages the Selenium driver setup and operations."""

    def __init__(self, mode="headless"):
        self.mode = mode
        self.driver = self.setup_driver()

    def setup_driver(self):
        options = webdriver.ChromeOptions()
        if self.mode == "headless":
            options.add_argument("--headless")
        options.page_load_strategy = 'eager'
        driver = webdriver.Chrome(service=ChromeService(
            executable_path="./chromedriver"), options=options)
        return driver

    def close(self):
        self.driver.quit()
