import sys
import argparse
import logging
import os

from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from csv_loader import load_csv_to_queue
from logger import LoggerManager
from driver_manager import DriverManager
from custom_exceptions import *
from microsoft_credential_manager import MicrosoftSignIn
from services import AzureAutoOBRClient
from login import Login


# Constants
MODE_HEADLESS = "headless"
MODE_HEADFUL = "headful"
DEFAULT_CSV_PATH = "users.csv"
STATUS_FAILED = "failed"
STATUS_DONE = "done"
MAX_RETRIES = 1

class MainApp:
    """Orchestrates the entire process."""

    def __init__(self, mode):
        LoggerManager.setup_console_logging()
        logging.info("Starting the automation script...")
        self.azure_auto_obr_client = AzureAutoOBRClient()
        self.ms_signin = None
        self.driver_manager = None
        self.mode = mode  # Store the mode as an instance variable


    def setup_driver_and_signin(self, email):
        self.driver_manager = DriverManager(mode=self.mode)  # Pass the mode to DriverManager
        self.ms_signin = MicrosoftSignIn(self.driver_manager, email)

    def register_security_key(self, message):
        email, user_id, issuer_id, requestId = [message.get(key) for key in
                                                ["email", "userId", "issuerId", "requestId"]]
        self.ms_signin.register_security_key(email=email, user_id=user_id, issuer_id=issuer_id)

    def handle_exception(self, exception, email):
        exception_mapping = {
            MicrosoftAccessPassValidationException: "Microsoft raised an error: an access pass could not be found or "
                                                    "verified for the user.",
            TimeoutException: "Timeout while interacting with Microsoft. Page or element not loaded.",
            NoSuchElementException: "Element not found.",
            SecurityKeysLimitException: "You have reached the limit of 10 security keys.",
            WebDriverException: "Internal error occurred.",
            TAPRetrievalFailureException: str(exception),
            OrganizationNeedsMoreInformationException: str(exception),
            TwoFactorAuthRequiredException: str(exception),
            RedirectedToPasswordPageException: str(exception),
            Exception: f"Error processing message: {exception}"
        }
        detail = exception_mapping.get(type(exception), "An unexpected error occurred.")
        logging.error(f"{detail}: {exception}")
        return detail

    def finalize_process(self, status, detail, email, message):
        try:
            if status == STATUS_FAILED:
                self.report_failure(email, detail)

            self.driver_manager.close()
            self.update_request_status(message, status, detail)
        except KeyboardInterrupt:
            logging.info("Program interrupted by user. Exiting gracefully.")
            sys.exit(0)

        LoggerManager.TUI.stop_loading()

    def report_failure(self, email, detail):
        LoggerManager.TUI.error(f"Failed to create security key for {email}: {detail}")
        LoggerManager.capture_screenshot(self.driver_manager.driver, email)
        LoggerManager.capture_browser_logs(self.driver_manager.driver, email)

    def update_request_status(self, message, status, detail):
        user_id, requestId = message.get("userId"), message.get("requestId")
        try:
            self.azure_auto_obr_client.update_request_status(user_id, requestId, status, detail)
        except Exception as ex:
            logging.error(str(ex))

    def process_message(self, message):
        email = message.get("email")
        retries = message.get("retries")
        self.setup_driver_and_signin(email)
        status, detail = STATUS_FAILED, "An unknown error occurred during processing."
        try:
            if retries <= 1:
                LoggerManager.TUI.start_loading(f"{'Retrying ' if retries == 1 else ''}Registering security key for {email}")
                self.register_security_key(message)
                status, detail = STATUS_DONE, "Credential successfully created."
                LoggerManager.TUI.stop_loading()
                LoggerManager.TUI.success(f'Security key successfully created for {email}')
        except Exception as ex:
            detail = self.handle_exception(ex, email)
            raise
        finally:
            LoggerManager.TUI.stop_loading()
            self.finalize_process(status, detail, email, message)

    def consume_csv(self, csv_path):
        queue = load_csv_to_queue(csv_path)
        while not queue.empty():
            user = queue.get()
            user.setdefault("retries", 0)
            try:
                self.process_message(user)
            except (TimeoutException, NoSuchElementException, WebDriverException, TAPRetrievalFailureException) as ex:
                if user["retries"] < MAX_RETRIES:
                    user["retries"] += 1
                    queue.put(user)
                    logging.error(f"Error processing message (Retry {user['retries']} of {MAX_RETRIES}): {ex}")
                else:
                    logging.error(f"Max retry count reached for message: {ex}")
            except Exception as ex:
                logging.error(f"Error processing message: {ex}")

    def run(self):
        args = self.parse_arguments()
        self.consume_csv(args.csv)
        logging.info("Automation script finished.")

    @staticmethod
    def parse_arguments():
        parser = argparse.ArgumentParser(description="Automate Microsoft Sign-In to register a security key.")
        parser.add_argument("--mode", default=MODE_HEADLESS,
                            help="Mode in which to run the script. Default is headless.",
                            choices=[MODE_HEADLESS, MODE_HEADFUL])
        parser.add_argument("--csv", type=str, help="Path to the CSV file", required=False, default=DEFAULT_CSV_PATH)
        parser.add_argument("--verbose", type=bool, help="Path to the CSV file", required=False, default=False, action=argparse.BooleanOptionalAction)
        parser.add_argument("--version", action="store_true", help="Print the script version")
        parser.add_argument("--login", type=bool, help="Login and get updated session", required=False, action=argparse.BooleanOptionalAction)
        return parser.parse_args()


if __name__ == "__main__":
    args = MainApp.parse_arguments()  # Parse command-line arguments

    if args.login:
        Login.start()
        sys.exit(0)

    credentials = Login.load_credentials()
    if not Login.validate_api_key(credentials):
        print("Your session has expired or does not exist. Please use the --login flag to login before proceeding.")
        sys.exit(1)

    if args.version:
        version = os.environ.get("VERSION", "Unknown")
        print(f"Script Version: {version}")
        sys.exit(0)

    try:
        LoggerManager.verbose = args.verbose
        app = MainApp(args.mode)  # Pass the mode from command line to MainApp constructor
        app.run()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        logging.error(e)
        sys.exit(0)
