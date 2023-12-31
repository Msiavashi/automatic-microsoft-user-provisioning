from selenium.webdriver.support.ui import WebDriverWait
import threading
from selenium.common.exceptions import TimeoutException
import random
import string
import datetime
from tap import TAPManager, TAPRetrievalFailureException
import time
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from logger import LoggerManager
import os
from dotenv import load_dotenv
import json

load_dotenv()


class MicrosoftAccessPassValidationException(Exception):
    """Occurs when an access pass validation error is found in the console."""
    pass


class OrganizationNeedsMoreInformationException(Exception):
    "Occures when user needs to take action on their account to be able to login"
    pass


class SecurityKeysLimitException(Exception):
    "Occure when microsoft display exception related to maximum number of security keys reached"
    pass


class TwoFactorAuthRequiredException(Exception):
    """Occurs when a security key setup requires two-factor authentication."""
    pass


class MicrosoftSignIn:
    """Handles the Microsoft sign-in process."""

    LONG_PROCESS = 60
    NORMAL_PROCESS = 30
    SHORT_PROCESS = 5

    def __init__(self, driver_manager, test_mode=False):
        self.tap_manager = TAPManager()
        self.driver = driver_manager.driver
        self.test_mode = test_mode

        with open("makeCredential.js", "r") as file:
            self.js_template = file.read()

    def _check_logs_for_errors(self):
        logs = self.driver.get_log('browser')
        for log in logs:
            if "message" in log and "an access pass could not be found or verified for the user" in log["message"].lower():
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
        self.logger = LoggerManager.setup_logger(email)
        try:
            self.logger.info("Retrieving TAP ...")
            tap = self.tap_manager.retrieve_TAP(user_id, issuer_id)
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
        self.driver.get("https://mysignins.microsoft.com/security-info")
        self.logger.info(
            "Log listener enabled...")
        self._fill_email(email)
        self._click_next()
        LoggerManager.capture_screenshot_for_debug(
            self.driver, email, "click_next")
        self._enter_tap(tap)
        LoggerManager.capture_screenshot_for_debug(
            self.driver, email, "enter_tap")
        self._click_sign_in()
        LoggerManager.capture_screenshot_for_debug(
            self.driver, email, "click_sign_in")
        self._handle_stay_signed_in_prompt()
        LoggerManager.capture_screenshot_for_debug(
            self.driver, email, "handle_stay_signed_in_promp")
        self._check_require_more_information_error()
        self._check_logs_for_errors()
        LoggerManager.capture_screenshot_for_debug(
            self.driver, email, "check_require_more_information_error")
        self._add_sign_in_method()
        LoggerManager.capture_screenshot_for_debug(
            self.driver, email, "add_sign_in_method")
        self._select_security_key()
        self._click_add_button()
        self._click_usb_device_button()
        self._click_next_to_add_sk()
        self._inject_js_into_page(user_id)
        self._fill_security_key_name(user_id)
        LoggerManager.capture_screenshot_for_debug(
            self.driver, email, "fill_security_key_name")
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
                    (By.XPATH, "//span[contains(@class, 'ms-Button-flexContainer') and .//span[text()='Security key']]"))
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
            # Wait for the "Add method" button to be clickable for up to 15 seconds
            self.logger.info("Clicking on 'Add sign-in method' button")
            add_method_button = WebDriverWait(self.driver, self.NORMAL_PROCESS).until(
                EC.element_to_be_clickable((By.NAME, "Add method"))
            )

            time.sleep(2)

            # Once the button is clickable, click on it
            add_method_button.click()

            # Add additional actions here if needed

        except TimeoutError as e:
            self.logger.info(
                f"Timeout while waiting for Add sign-in method button: {e}")
            raise
        # self._click_button(
        #     "//span[text()='Add sign-in method']", "Add sign-in method", self.NORMAL_PROCESS)

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

    def _click_button(self, xpath, button_name, extra_delay=0):
        time.sleep(2)
        try:
            self.logger.info(f"Clicking the {button_name} button...")
            button = WebDriverWait(self.driver, self.NORMAL_PROCESS + extra_delay).until(
                EC.element_to_be_clickable((By.XPATH, xpath)))
            button.click()
        except Exception as e:
            self.logger.error(f"Error clicking {button_name} button: {str(e)}")
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
