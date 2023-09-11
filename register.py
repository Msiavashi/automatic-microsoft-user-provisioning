import argparse
import logging
from tap import TAPManager
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def setup_console_logging():
    """Set up console logging."""
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)
    logging.getLogger().setLevel(logging.DEBUG)

class MicrosoftSignIn:
    def __init__(self, mode="production"):
        self.mode = mode
        self.tap_manager = TAPManager()
        self.driver = self.setup_driver()
        self.logger = None

    def setup_driver(self):
        """Setup and return a selenium driver based on the mode."""
        logging.info("Setting up the driver...")
        options = webdriver.ChromeOptions()
        
        if self.mode == "production":
            options.add_argument("--headless")
        
        options.page_load_strategy = 'eager'
        # options.add_argument('--disable-application-cache')
        driver = webdriver.Chrome(options=options)
        logging.info("Driver set up successfully.")
        return driver

    def setup_logger(self, email):
        """Setup and return a logger for the email."""
        if not os.path.exists('logs'):
            os.makedirs('logs')

        logger = logging.getLogger(email)
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(f'logs/{email}.log')
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        return logger

    def register_security_key(self, email, tap=None, user_id=None, issuer_id=None):
        """Try to register a security key."""
        self.logger = self.setup_logger(email)
        if self.mode == "debug" and not tap:
            tap = self.tap_manager.retrieve_TAP(user_id, issuer_id)
        try:
            self.navigate_and_fill_details(email, tap)
        except Exception as e:
            self.logger.error(f"Error registering security key for {email}: {str(e)}")
            self.capture_logs_and_screenshots(email)

    def navigate_and_fill_details(self, email, tap):
        """Navigate to the Microsoft sign-in page and fill in the required details."""
        logging.info("Navigating to Microsoft sign-in page...")
        self.driver.get("https://mysignins.microsoft.com/")
        WebDriverWait(self.driver, 5).until(EC.url_changes("https://mysignins.microsoft.com/"))
        self.fill_email(email)
        self.click_next()
        self.enter_tap(tap)
        self.click_sign_in()
        self.navigate_to_security_info()
        self.click_add_sign_in_method()
        self.select_security_key()
        self.click_add_button()
        self.click_usb_device_button()
        
    def click_add_button(self):
        """Click the 'Add' button."""
        try:
            logging.info("Clicking the 'Add' button...")
            
            # Use WebDriverWait with XPath to identify the 'Add' button
            add_button = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='button' and .//span[text()='Add']]"))
            )
            
            add_button.click()
                
        except Exception as e:
            self.logger.error(f"Error clicking 'Add' button: {str(e)}")
            raise
    
        
    def select_security_key(self):
        """Select 'Security key' from the dropdown."""
        try:
            logging.info("Clicking the dropdown to expand...")

            # Click on the dropdown to expand it
            dropdown = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@role='combobox' and @aria-label='Authentication method options']"))
            )
            dropdown.click()

            # Wait a bit for the dropdown to fully expand
            time.sleep(2)  # You can adjust this based on the site's responsiveness

            logging.info("Selecting 'Security key' from the expanded dropdown...")

            # Click on the 'Security key' option
            security_key_option = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'ms-Button-flexContainer') and .//span[text()='Security key']]"))
            )
            security_key_option.click()

        except Exception as e:
            self.logger.error(f"Error selecting 'Security key' from dropdown: {str(e)}")
            raise

        
    def click_usb_device_button(self):
        """Click the 'USB device' button."""
        try:
            logging.info("Clicking the 'USB device' button...")
            
            # Use WebDriverWait with XPath to identify the 'USB device' button
            usb_button = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='button' and .//span[text()='USB device']]"))
            )
            
            usb_button.click()
                
        except Exception as e:
            self.logger.error(f"Error clicking 'USB device' button: {str(e)}")
            raise

        
    def click_add_sign_in_method(self):
        """Click the 'Add sign-in method' link."""
        try:
            logging.info("Clicking the 'Add sign-in method' link...")
            
            # Use WebDriverWait with a simpler XPath targeting the label text
            add_method_link = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Add sign-in method']"))
            )
            
            add_method_link.click()
                
        except Exception as e:
            self.logger.error(f"Error clicking 'Add sign-in method' link: {str(e)}")
            raise

        
    def navigate_to_security_info(self):
        """Directly navigate to the security info page."""
        try:
            logging.info("Navigating directly to the security info page...")
            self.driver.get("https://mysignins.microsoft.com/security-info")
        except Exception as e:
            self.logger.error(f"Error navigating to security info page: {str(e)}")
            raise

    def click_sign_in(self):
        """Click the sign in button."""
        try:
            logging.info("Clicking the sign in button...")
            
            # Use WebDriverWait with XPath to identify the sign in button
            sign_in_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @value='Sign in' and contains(@class, 'button_primary')]"))
            )
            
            sign_in_button.click()
                
        except Exception as e:
            self.logger.error(f"Error clicking sign in button: {str(e)}")
            raise

    def fill_email(self, email):
        """Fill the email field."""
        try:
            logging.info(f"Filling in email: {email}")
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='email' and @name='loginfmt']"))
            )
            email_input.send_keys(email)
        except Exception as e:
            self.logger.error(f"Error filling email: {str(e)}")
            raise

    def click_next(self):
        """Click the next button."""
        try:
            logging.info("Clicking the next button...")
            next_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @value='Next' and contains(@class, 'button_primary')]"))
            )
            next_button.click()
        except Exception as e:
            self.logger.error(f"Error clicking next button: {str(e)}")
            raise

    def enter_tap(self, tap):
        """Enter the Temporary Access Pass."""
        try:
            logging.info(f"Entering Temporary Access Pass: {tap}")
            
            # Use WebDriverWait with the name attribute to identify the TAP input field
            tap_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "accesspass"))
            )
            
            tap_input.send_keys(tap)
                
        except Exception as e:
            self.logger.error(f"Error entering TAP: {str(e)}")
            raise

    def capture_logs_and_screenshots(self, email):
        """Capture screenshots and logs for debugging purposes."""
        self.capture_screenshot(email)
        self.capture_browser_logs(email)

    def capture_screenshot(self, email):
        """Capture a screenshot."""
        try:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            self.driver.save_screenshot(f'screenshots/{email}_{timestamp}.png')
        except Exception as e:
            self.logger.error(f"Error capturing screenshot: {str(e)}")

    def capture_browser_logs(self, email):
        """Capture browser logs."""
        try:
            browser_logs = self.driver.get_log('browser')
            with open(f'logs/{email}_browser_logs.txt', 'w') as f:
                for entry in browser_logs:
                    f.write(str(entry))
        except Exception as e:
            self.logger.error(f"Error capturing browser logs: {str(e)}")

    def close(self):
        """Close the selenium driver."""
        time.sleep(3000)
        self.driver.quit()


def main():
    setup_console_logging()
    logging.info("Starting the automation script...")

    parser = argparse.ArgumentParser(description="Automate Microsoft Sign-In to register a security key.")
    parser.add_argument("--mode", choices=["debug", "production"], default="production", help="Mode in which to run the script. Default is production.")
    parser.add_argument("--email", type=str, required=True, help="Email to be used for sign-in.")
    parser.add_argument("--tap", type=str, help="Temporary Access Pass. Optional in debug mode. Will receive from Microsoft if not provided in debug mode.")
    parser.add_argument("--userId", type=str, required=True, help="The user to register the credential/security-key for, Required in debug mode.")
    parser.add_argument("--issuerId", type=str, required=True, help="The user/admin who requests/issues the request. Required in debug mode.")
    args = parser.parse_args()

    ms_signin = MicrosoftSignIn(mode=args.mode)
    ms_signin.register_security_key(email=args.email, tap=args.tap, user_id=args.userId, issuer_id=args.issuerId)
    ms_signin.close()

    logging.info("Automation script finished.")


if __name__ == "__main__":
    main()