from selenium.webdriver.support.ui import WebDriverWait
import random
import string
import datetime
from tap import TAPManager
import time
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from logger import LoggerManager
import os
from dotenv import load_dotenv
import json

load_dotenv()


class MicrosoftSignIn:
    """Handles the Microsoft sign-in process."""

    def __init__(self, driver_manager, mode="production"):
        self.mode = mode
        self.tap_manager = TAPManager()
        self.driver = driver_manager.driver
        self.logger = None
        with open("makeCredential.js", "r") as file:
            self.js_template = file.read()

    def _generate_security_key_name(self, user_id):
        shortened_customer_id = user_id[-8:]
        random_string = ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=6))
        date_str = datetime.datetime.now().strftime('%Y%m%d')
        return f"IDM-{shortened_customer_id}-{random_string}-{date_str}"

    def _fill_security_key_name(self, user_id):
        try:
            security_key_name = self._generate_security_key_name(user_id)
            self.logger.info(
                f"Filling in security key name: {security_key_name}")
            name_input = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[contains(@id, "TextField")]'))
            )
            name_input.send_keys(security_key_name)
        except Exception as e:
            self.logger.error(f"Error filling security key name: {str(e)}")
            raise

    def register_security_key(self, email, tap=None, user_id=None, issuer_id=None):
        self.logger = LoggerManager.setup_logger(email)
        if self.mode == "debug" and not tap:
            tap = self.tap_manager.retrieve_TAP(user_id, issuer_id)
        try:
            self._navigate_and_fill_details(email, tap, user_id)
        except Exception as e:
            self.logger.error(
                f"Error registering security key for {email}: {str(e)}")
            LoggerManager.capture_screenshot(self.driver, email)
            LoggerManager.capture_browser_logs(self.driver, email)

    def _navigate_and_fill_details(self, email, tap, user_id):
        self.logger.info("Navigating to Microsoft sign-in page...")
        self.driver.get("https://mysignins.microsoft.com/")
        WebDriverWait(self.driver, 5).until(
            EC.url_changes("https://mysignins.microsoft.com/"))
        self._fill_email(email)
        self._click_next()
        self._enter_tap(tap)
        self._click_sign_in()
        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'mectrl_profilepic')))
        self._navigate_to_security_info()
        self._add_sign_in_method()
        self._select_security_key()
        self._click_add_button()
        self._click_usb_device_button()
        self._click_next_to_add_sk()
        self._inject_js_into_page(user_id)
        self._fill_security_key_name(user_id)
        self._click_final_next_button()
        time.sleep(5)

    def _click_next_to_add_sk(self):
        self._click_button("//button[contains(@class, 'ms-Button--primary') and .//span[text()='Next']]",
                           "next")

    def _execute_cdp_cmd(self, cmd: str, params: dict = None):
        params = params or {}
        resource = f"/session/{self.driver.session_id}/chromium/send_command_and_get_result"
        url = self.driver.command_executor._url + resource
        body = {"cmd": cmd, "params": params}
        response = self.driver.command_executor._request(
            "POST", url, json.dumps(body))
        return response.get("value")

    def _inject_js_into_page(self, user_id):
        js_code = self.js_template.format(
            os.getenv("AUTHNAPI_URL") +
            os.getenv("AUTHNAPI_OBR_PATH"), os.getenv(
                "PASSKEY_OBR_API_KEY"), user_id
        )
        try:
            result = self._execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument", {"source": js_code})
            if result:
                self.logger.info("JS code injected successfully.")
            else:
                self.logger.warning("JS code injection might have failed.")
        except Exception as e:
            self.logger.error(f"Error during JS injection: {str(e)}")
            raise

    def _click_add_button(self):
        self._click_button(
            "//button[@type='button' and .//span[text()='Add']]", "Add")

    def _select_security_key(self):
        try:
            self.logger.info("Clicking the dropdown to expand...")
            dropdown = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//div[@role='combobox' and @aria-label='Authentication method options']"))
            )
            dropdown.click()
            self.logger.info(
                "Selecting 'Security key' from the expanded dropdown...")
            security_key_option = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//span[contains(@class, 'ms-Button-flexContainer') and .//span[text()='Security key']]"))
            )
            security_key_option.click()
        except Exception as e:
            self.logger.error(
                f"Error selecting 'Security key' from dropdown: {str(e)}")
            raise

    def _click_usb_device_button(self):
        self._click_button(
            "//button[@type='button' and .//span[text()='USB device']]", "USB device")

    def _add_sign_in_method(self):
        self._click_button(
            "//span[text()='Add sign-in method']", "Add sign-in method")

    def _navigate_to_security_info(self):
        try:
            self.logger.info(
                "Navigating directly to the security info page...")
            self.driver.get("https://mysignins.microsoft.com/security-info")
        except Exception as e:
            self.logger.error(
                f"Error navigating to security info page: {str(e)}")
            raise

    def _click_sign_in(self):
        self._click_button("//input[@type='submit' and @value='Sign in' and contains(@class, 'button_primary')]",
                           "sign in")

    def _fill_email(self, email):
        self._fill_input(
            "//input[@type='email' and @name='loginfmt']", email, "email")

    def _click_final_next_button(self):
        self._click_button(
            "//button[@type='button' and contains(@class, 'ms-Button') and contains(@class, 'ms-Button--primary') and .//span[text()='Next']]",
            "Next")

    def _click_next(self):
        self._click_button(
            "//input[@type='submit' and @value='Next' and contains(@class, 'button_primary')]", "Next")

    def _enter_tap(self, tap):
        self._fill_input("//input[@name='accesspass']",
                         tap, "Temporary Access Pass")

    def _click_button(self, xpath, button_name):
        try:
            self.logger.info(f"Clicking the {button_name} button...")
            button = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, xpath)))
            button.click()
        except Exception as e:
            self.logger.error(f"Error clicking {button_name} button: {str(e)}")
            raise

    def _fill_input(self, xpath, value, input_name):
        try:
            self.logger.info(f"Filling in {input_name}: {value}")
            input_field = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, xpath)))
            input_field.send_keys(value)
        except Exception as e:
            self.logger.error(f"Error filling {input_name}: {str(e)}")
            raise
