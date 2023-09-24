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

    def generate_security_key_name(self, user_id):
        """
        Generates a security key name string in the following format:

        [Prefix]-[ShortenedCustomerID]-[RandomString]-[Date]

        - Prefix: A constant string "IDM" that identifies the key as belonging to IDmelon.
        - ShortenedCustomerID: The last 8 characters of the user's MongoDB ID.
        - RandomString: A 6 characters long random alphanumeric string.
        - Date: The date the key was generated, in the format YYYYMMDD.

        Example:
        IDM-1A2B3C4D-A1B2C3-20230917

        Where:
        - "IDM" stands for IDmelon.
        - "1A2B3C4D" is the shortened MongoDB ID (last 8 characters).
        - "A1B2C3" is the random alphanumeric string.
        - "20230917" is the date (September 17, 2023).

        :param user_id: The user's MongoDB ID.
        :return: The generated security key name string.
        """
        # Extract the last 8 characters of the MongoDB ID
        shortened_customer_id = user_id[-8:]

        # Generate a random alphanumeric string of 6 characters
        random_string = ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=6))

        # Get the current date in YYYYMMDD format
        date_str = datetime.datetime.now().strftime('%Y%m%d')

        # Construct the name string
        name_str = f"IDM-{shortened_customer_id}-{random_string}-{date_str}"

        return name_str

    def fill_security_key_name(self, user_id):
        try:
            # Generate the security key name
            security_key_name = self.generate_security_key_name(user_id)

            self.logger.info(
                f"Filling in security key name: {security_key_name}")

            # Locate the input field by its tag name and type attribute and fill it with the generated name string
            name_input = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[contains(@id, "TextField")]'))
            )
            name_input.send_keys(security_key_name)

        except Exception as e:
            self.logger.error(f"Error filling security key name: {str(e)}")
            raise

    def register_security_key(self, email, tap=None, user_id=None, issuer_id=None):
        """Try to register a security key."""
        self.logger = LoggerManager.setup_logger(email)
        if self.mode == "debug" and not tap:
            tap = self.tap_manager.retrieve_TAP(user_id, issuer_id)
        try:
            self.navigate_and_fill_details(email, tap, user_id)
        except Exception as e:
            self.logger.error(
                f"Error registering security key for {email}: {str(e)}")
            LoggerManager.capture_screenshot(self.driver, email)
            LoggerManager.capture_browser_logs(self.driver, email)

    def navigate_and_fill_details(self, email, tap, user_id):
        """Navigate to the Microsoft sign-in page and fill in the required details."""
        self.logger.info("Navigating to Microsoft sign-in page...")
        self.driver.get("https://mysignins.microsoft.com/")
        WebDriverWait(self.driver, 5).until(
            EC.url_changes("https://mysignins.microsoft.com/"))
        self.fill_email(email)
        self.click_next()
        self.enter_tap(tap)
        self.click_sign_in()
        # Wait for the element with class 'mectrl_profilepic' to ensure the full DOM is rendered
        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'mectrl_profilepic'))
        )
        self.navigate_to_security_info()
        self.click_add_sign_in_method()
        self.select_security_key()
        self.click_add_button()
        self.click_usb_device_button()
        self.click_next_to_add_sk()
        self.inject_js_into_page(user_id)
        self.fill_security_key_name(user_id)
        self.click_last_next_button()
        time.sleep(5)

    def click_next_to_add_sk(self):
        """Click the next button."""
        try:
            self.logger.info("Clicking the next button...")

            # Using XPath to target the button with the text "Next"
            next_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(@class, 'ms-Button--primary') and .//span[text()='Next']]"))
            )
            next_button.click()
        except Exception as e:
            self.logger.error(f"Error clicking next button: {str(e)}")
            raise

    def execute_cdp_cmd(self, cmd: str, params: dict = None):
        if params is None:
            params = {}
        resource = f"/session/{self.driver.session_id}/chromium/send_command_and_get_result"
        url = self.driver.command_executor._url + resource
        body = {"cmd": cmd, "params": params}

        json_body = json.dumps(body)  # Convert body to JSON string
        response = self.driver.command_executor._request(
            "POST", url, json_body
        )  # Pass JSON string as body
        return response.get("value")

    def inject_js_into_page(self, user_id):
        """Replace values in the JS template and inject it into the current page."""

        js_code = self.js_template.format(
            os.getenv(
                "AUTHNAPI_URL") + os.getenv("AUTHNAPI_OBR_PATH"), os.getenv("PASSKEY_OBR_API_KEY"), user_id
        )

        try:
            result = self.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": js_code},
            )

            if result:
                self.logger.info("JS code injected successfully.")
            else:
                self.logger.warning("JS code injection might have failed.")

        except Exception as e:
            self.logger.error(f"Error during JS injection: {str(e)}")
            raise

    def click_add_button(self):
        """Click the 'Add' button."""
        try:
            self.logger.info("Clicking the 'Add' button...")

            # Use WebDriverWait with XPath to identify the 'Add' button
            add_button = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[@type='button' and .//span[text()='Add']]"))
            )

            add_button.click()

        except Exception as e:
            self.logger.error(f"Error clicking 'Add' button: {str(e)}")
            raise

    def select_security_key(self):
        """Select 'Security key' from the dropdown."""
        try:
            self.logger.info("Clicking the dropdown to expand...")

            # Click on the dropdown to expand it
            dropdown = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//div[@role='combobox' and @aria-label='Authentication method options']"))
            )
            dropdown.click()

            # Wait a bit for the dropdown to fully expand
            # You can adjust this based on the site's responsiveness
            time.sleep(2)

            self.logger.info(
                "Selecting 'Security key' from the expanded dropdown...")

            # Click on the 'Security key' option
            security_key_option = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//span[contains(@class, 'ms-Button-flexContainer') and .//span[text()='Security key']]"))
            )
            security_key_option.click()

        except Exception as e:
            self.logger.error(
                f"Error selecting 'Security key' from dropdown: {str(e)}")
            raise

    def click_usb_device_button(self):
        """Click the 'USB device' button."""
        try:
            self.logger.info("Clicking the 'USB device' button...")

            # Use WebDriverWait with XPath to identify the 'USB device' button
            usb_button = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[@type='button' and .//span[text()='USB device']]"))
            )

            usb_button.click()

        except Exception as e:
            self.logger.error(f"Error clicking 'USB device' button: {str(e)}")
            raise

    def click_add_sign_in_method(self):
        """Click the 'Add sign-in method' link."""
        try:
            self.logger.info("Clicking the 'Add sign-in method' link...")

            # Use WebDriverWait with a simpler XPath targeting the label text
            add_method_link = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//span[text()='Add sign-in method']"))
            )

            add_method_link.click()

        except Exception as e:
            self.logger.error(
                f"Error clicking 'Add sign-in method' link: {str(e)}")
            raise

    def navigate_to_security_info(self):
        """Directly navigate to the security info page."""
        try:
            self.logger.info(
                "Navigating directly to the security info page...")
            self.driver.get("https://mysignins.microsoft.com/security-info")
        except Exception as e:
            self.logger.error(
                f"Error navigating to security info page: {str(e)}")
            raise

    def click_sign_in(self):
        """Click the sign in button."""
        try:
            self.logger.info("Clicking the sign in button...")

            # Use WebDriverWait with XPath to identify the sign in button
            sign_in_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//input[@type='submit' and @value='Sign in' and contains(@class, 'button_primary')]"))
            )

            sign_in_button.click()

        except Exception as e:
            self.logger.error(f"Error clicking sign in button: {str(e)}")
            raise

    def fill_email(self, email):
        """Fill the email field."""
        try:
            self.logger.info(f"Filling in email: {email}")
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//input[@type='email' and @name='loginfmt']"))
            )
            email_input.send_keys(email)
        except Exception as e:
            self.logger.error(f"Error filling email: {str(e)}")
            raise

    def click_last_next_button(self):
        """Click the last 'Next' button that finalize the security key creation."""
        try:
            self.logger.info("Clicking the 'Next' button...")

            # Using XPath to target the button with the text "Next" and specific class names
            next_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[@type='button' and contains(@class, 'ms-Button') and contains(@class, 'ms-Button--primary') and .//span[text()='Next']]"))
            )
            next_button.click()
        except Exception as e:
            self.logger.error(f"Error clicking 'Next' button: {str(e)}")
            raise

    def click_next(self):
        """Click the next button."""
        try:
            self.logger.info("Clicking the next button...")
            next_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//input[@type='submit' and @value='Next' and contains(@class, 'button_primary')]"))
            )
            next_button.click()
        except Exception as e:
            self.logger.error(f"Error clicking next button: {str(e)}")
            raise

    def enter_tap(self, tap):
        """Enter the Temporary Access Pass."""
        try:
            self.logger.info(f"Entering Temporary Access Pass: {tap}")

            # Use WebDriverWait with the name attribute to identify the TAP input field
            tap_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "accesspass"))
            )

            tap_input.send_keys(tap)

        except Exception as e:
            self.logger.error(f"Error entering TAP: {str(e)}")
            raise
