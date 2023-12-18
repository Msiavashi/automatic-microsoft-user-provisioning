import datetime
import json
import os
import random
import string
import time

from dotenv import load_dotenv
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from custom_exceptions import *
from logger import LoggerManager
from tap import TAPManager
from config import Config

load_dotenv(dotenv_path=Config.get_env_path())


class MicrosoftSignIn:
    """Handles the Microsoft sign-in process."""

    LONG_PROCESS = 60
    NORMAL_PROCESS = 30
    SHORT_PROCESS = 5
    SIGN_IN_URL = "https://mysignins.microsoft.com/security-info"

    def __init__(self, driver_manager, email):
        self.tap_manager = TAPManager()
        self.driver = driver_manager.driver
        self.logger = LoggerManager.setup_logging(email)
        self.email = email
        self.driver.set_page_load_timeout(MicrosoftSignIn.LONG_PROCESS)

        with open(Config.get_make_credential_path(), "r") as file:
            self.js_template = file.read()

    def _check_logs_for_errors(self):
        logs = self.driver.get_log('browser')
        for log in logs:
            if "message" in log and "an access pass could not be found or verified for the user" in log[
                "message"].lower():
                raise MicrosoftAccessPassValidationException(
                    "Access pass validation error detected.")

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
            name_input = WebDriverWait(self.driver, self.LONG_PROCESS).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[contains(@id, "TextField")]'))
            )
            name_input.send_keys(security_key_name)
        except Exception as e:
            self.logger.error(f"Error filling security key name: {str(e)}")
            raise

    def register_security_key(self, email, user_id=None, issuer_id=None):
        try:
            self.logger.info("Retrieving TAP ...")
            tap = self.tap_manager.retrieve_TAP(user_id, issuer_id)
            # This delay is necessary in order for Microsoft to propagate the TAP so we don't see the password field.
            time.sleep(3)
            self._navigate_and_fill_details(email, tap, user_id)
        except TAPRetrievalFailureException as e:
            self.logger.error(
                f"Failed to retrieve tap: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(
                f"Error registering security key for {email}: {str(e)}")
            raise

    def _handle_stay_signed_in_prompt(self):
        try:
            WebDriverWait(self.driver, self.SHORT_PROCESS).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@class='row text-title' and @role='heading' and @aria-level='1']"))
            )
            self.logger.info("'Stay signed in?' prompt appeared.")
            self._click_no_stay_signed_in()
        except TimeoutException:
            self.logger.debug("'Stay signed in?' prompt did not appear.")

    def _click_no_stay_signed_in(self):
        # self._click_button(
        #     "//input[@type='button' and @id='idBtn_Back' and @value='No']", "No")
        self._click_button(
            "//input[@type='submit' and @id='idSIButton9']", "Yes")

    def _navigate_and_fill_details(self, email, tap, user_id):
        self.logger.info(
            "Navigating to Microsoft sign-in, security-info page...")
        self.driver.get(self.SIGN_IN_URL)
        self._fill_email(email)
        self._click_next()
        self._enter_tap(tap)
        self._click_sign_in()
        self._handle_stay_signed_in_prompt()
        self._check_require_more_information_error()
        self._check_logs_for_errors()
        self._add_sign_in_method()
        self._select_security_key()
        self._click_add_button()
        self._click_usb_device_button()
        self._click_next_to_add_sk()
        self._inject_js_into_page(user_id)
        self._fill_security_key_name(user_id)
        self._click_final_next_button()
        time.sleep(5)
        self.logger.info("Credential Successfully Created!")

    def _check_require_more_information_error(self):
        self.logger.info(
            "Checking your organization requires more information...")
        error_xpath = '//*[@id="ProofUpDescription"]'
        try:
            error_element = WebDriverWait(self.driver, self.SHORT_PROCESS).until(
                EC.presence_of_element_located((By.XPATH, error_xpath)))
            if error_element:
                raise OrganizationNeedsMoreInformationException(
                    "Your organization needs more information to keep your account secure on https://mysignins.microsoft.com/. You are receiving it because your organization has enabled security defaults in Microsoft Office 365.")
        except TimeoutException:
            self.logger.info(
                "Organization needs more information... error did not happen")

    def _check_for_sk_limit(self):
        try:
            error_element = WebDriverWait(self.driver, self.SHORT_PROCESS).until(
                EC.presence_of_element_located(
                    (By.ID, 'ms-banner')
                )
            )
            error_message = error_element.text
            if "You have already reached the limit of 10 security keys" in error_message:
                self.logger.error(
                    "You have already reached the limit of 10 security keys")
                raise SecurityKeysLimitException(error_message)
        except TimeoutException:
            self.logger.debug(
                "'ms-banner' element indicating 10 security keys limit did not appear. Proceed without error...")
            raise

    def _check_for_two_factor_auth_error(self):
        error_xpath = "//div[contains(text(), 'To set up a security key, you need to sign in with two-factor authentication.')]"
        try:
            error_element = WebDriverWait(self.driver, self.SHORT_PROCESS).until(
                EC.presence_of_element_located((By.XPATH, error_xpath)))
            if error_element:
                raise TwoFactorAuthRequiredException(error_element.text)
        except TimeoutException:
            raise

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
            dropdown = WebDriverWait(self.driver, self.LONG_PROCESS).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//div[@role='combobox' and @aria-label='Authentication method options']"))
            )
            dropdown.click()
            self.logger.info(
                "Selecting 'Security key' from the expanded dropdown...")
            security_key_option = WebDriverWait(self.driver, self.LONG_PROCESS).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//span[contains(@class, 'ms-Button-flexContainer') and .//span[text()='Security key']]"))
            )
            security_key_option.click()
        except Exception as e:
            self.logger.error(
                f"Error selecting 'Security key' from dropdown: {str(e)}")
            raise

    def _click_usb_device_button(self):
        try:
            self._click_button(
                "//button[@type='button' and .//span[text()='USB device']]", "USB device")
        except TimeoutException as e:
            try:
                self._check_for_sk_limit()
                self._check_for_two_factor_auth_error()
            except (SecurityKeysLimitException, TwoFactorAuthRequiredException) as e:
                raise e
            raise e

    def _add_sign_in_method(self):
        try:
            self.logger.info("Clicking on 'Add sign-in method' button")
            self._click_button("Add method", "Add sign-in method", by=By.NAME)

        except TimeoutError as e:
            self.logger.error(f"Timeout while waiting for Add sign-in method button: {e}")
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

    def _click_button(self, locator, button_name, extra_delay=0, by=None, attributes=None):
        by = by or By.XPATH
        attributes = attributes or {}
        time.sleep(2)
        try:
            self.logger.info(f"Clicking the {button_name} button...")
            button = WebDriverWait(self.driver, self.NORMAL_PROCESS + extra_delay).until(
                EC.element_to_be_clickable((by, locator), **attributes))
            LoggerManager.capture_screenshot(
                self.driver, self.email, f"click_{button_name}")
            button.click()
        except TimeoutException as e:
            LoggerManager.capture_screenshot(
                self.driver, self.email, f"failed_click_{button_name}")
            self.logger.error(f"Timeout while clicking {button_name}: {e}")
            raise

    def _fill_input(self, xpath, value, input_name):
        try:
            self.logger.info(f"Filling in {input_name}: {value}")
            input_field = WebDriverWait(self.driver, self.LONG_PROCESS).until(
                EC.presence_of_element_located((By.XPATH, xpath)))
            input_field.send_keys(value)
        except Exception as e:
            self.logger.error(f"Error filling {input_name}: {str(e)}")
            raise
