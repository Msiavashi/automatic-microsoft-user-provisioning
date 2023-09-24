import argparse
import logging
from logger import LoggerManager
from driver_manager import DriverManager
from microsoft_credential_manager import MicrosoftSignIn

class MainApp:
    """Orchestrates the entire process."""

    def __init__(self):
        LoggerManager.setup_console_logging()
        logging.info("Starting the automation script...")

    def run(self):
        parser = argparse.ArgumentParser(description="Automate Microsoft Sign-In to register a security key.")
        parser.add_argument("--mode", choices=["debug", "production"], default="production", help="Mode in which to run the script. Default is production.")
        parser.add_argument("--email", type=str, required=True, help="Email to be used for sign-in.")
        parser.add_argument("--tap", type=str, help="Temporary Access Pass. Optional in debug mode. Will receive from Microsoft if not provided in debug mode.")
        parser.add_argument("--userId", type=str, required=True, help="The user to register the credential/security-key for, Required in debug mode.")
        parser.add_argument("--issuerId", type=str, required=True, help="The user/admin who requests/issues the request. Required in debug mode.")
        args = parser.parse_args()

        driver_manager = DriverManager(mode=args.mode)
        ms_signin = MicrosoftSignIn(driver_manager, mode=args.mode)
        ms_signin.register_security_key(email=args.email, tap=args.tap, user_id=args.userId, issuer_id=args.issuerId)
        driver_manager.close()

        logging.info("Automation script finished.")

if __name__ == "__main__":
    app = MainApp()
    app.run()