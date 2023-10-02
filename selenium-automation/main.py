import argparse
import os
import json
import logging
import threading
import atexit
from logger import LoggerManager
from driver_manager import DriverManager
from microsoft_credential_manager import MicrosoftSignIn, SecurityKeysLimitException, TwoFactorAuthRequiredException, OrganizationNeedsMoreInformationException
from rabbitmq_manager import RabbitMQManager
from services import AzureAutoOBRClient
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from tap import TAPRetrievalFailureException


class MainApp:
    """Orchestrates the entire process."""

    def __init__(self):
        LoggerManager.setup_console_logging()
        logging.info("Starting the automation script...")
        self.azure_auto_obr_client = AzureAutoOBRClient()
        self.ms_signin = None
        self.test_mode = False
        self.rabbitmq_manager = None
        self.heartbeat_timer = None
        self.driver_manager = None
        self.mode = None
        # Define an event to handle termination
        self.terminate_event = threading.Event()

    def initialize_resources(self):
        if not self.test_mode:
            self.rabbitmq_manager = RabbitMQManager(
                host=os.environ.get("RABBITMQ_HOSTNAME", "localhost"), port=5672, queue_name='obr', consumer_callback=self.queue_consumer)
            self.rabbitmq_manager.start()
            self.start_heartbeat()

    def queue_consumer(self, ch, method, properties, body):
        try:
            self.driver_manager = DriverManager(mode=self.mode)
            self.ms_signin = MicrosoftSignIn(self.driver_manager)
            message = json.loads(body)
            self.process_message(message)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except json.JSONDecodeError:
            logging.error("Failed to decode message body as JSON.")
        except Exception as ex:
            logging.error(f"Error processing message: {ex}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        finally:
            self.driver_manager.close()

    def process_message(self, message):
        status, detail = "failed", "An unknown error occurred during processing."
        try:
            email = message.get("email")
            user_id = message.get("userId")
            issuer_id = message.get("issuerId")
            requestId = message.get("requestId")

            self.ms_signin.register_security_key(
                email=email, user_id=user_id, issuer_id=issuer_id)
            status, detail = "done", "Credential successfully created."
        except TimeoutException as ex:
            detail = "Timeout while interacting with Microsoft."
            logging.error(f"{detail}: {ex}")
        except NoSuchElementException as ex:
            detail = "Element not found."
            logging.error(f"{detail}: {ex}")
        except SecurityKeysLimitException as ex:
            detail = "You have reached the limit of 10 security keys on https://mysignins.microsoft.com/"
            logging.error(detail)
        except WebDriverException as ex:
            detail = "Internal error occurred. Retry may lead to success."
            logging.error(f"{detail}: {ex}")
        except TAPRetrievalFailureException as ex:
            detail = str(ex)
            logging.error(detail)
        except OrganizationNeedsMoreInformationException as ex:
            detail = str(ex)
            logging.error(detail)
        except TwoFactorAuthRequiredException as ex:
            detail = str(ex)
            logging.error(detail)
        except Exception as ex:
            logging.error(f"Error processing message: {ex}")

        if not self.test_mode and status:  # Update status only when not in test_mode
            try:
                self.azure_auto_obr_client.update_request_status(
                    user_id, requestId, status, detail)
            except Exception as ex:
                logging.error(str(ex))
        else:
            logging.info(f"{status}: {detail}")

    def start_rabbitmq_consumer(self):
        self.consumer_thread = threading.Thread(
            target=self.rabbitmq_manager.consume,
            args=(self.queue_consumer,))
        self.consumer_thread.daemon = True  # Daemonize thread
        self.consumer_thread.start()
        logging.info("RabbitMQ consumer thread started.")

    def send_heartbeat(self):
        try:
            # logging.info("Sending heartbeat...")
            self.start_heartbeat()  # Reschedule the next heartbeat
        except Exception as e:
            logging.error(f"Error sending heartbeat: {e}")

    def start_heartbeat(self):
        if self.heartbeat_timer:
            self.heartbeat_timer.cancel()
        self.heartbeat_timer = threading.Timer(10, self.send_heartbeat)
        self.heartbeat_timer.daemon = True
        self.heartbeat_timer.start()

    def stop_heartbeat(self):
        if self.heartbeat_timer:
            self.heartbeat_timer.cancel()

    def run(self):
        parser = argparse.ArgumentParser(
            description="Automate Microsoft Sign-In to register a security key.")
        parser.add_argument("--mode", choices=["headless", "headful"], default="headless",
                            help="Mode in which to run the script. Default is headful.")
        parser.add_argument("--email", type=str,
                            help="Email to be used for sign-in.")
        parser.add_argument("--userId", type=str,
                            help="The user to register the credential/security-key for, Required in debug mode.")
        parser.add_argument("--issuerId", type=str,
                            help="The user/admin who requests/issues the request. Required in debug mode.")
        parser.add_argument("--test", action='store_true',
                            help="Set to true to run in test mode. Default is false.")
        args = parser.parse_args()

        self.test_mode = args.test

        self.mode = args.mode
        if (self.test_mode):
            self.driver_manager = DriverManager(mode=self.mode)
            self.ms_signin = MicrosoftSignIn(self.driver_manager)
            self.process_message({
                "email": args.email,
                "userId": args.userId,
                "issuerId": args.issuerId
            })
            self.driver_manager.close()
        else:
            self.initialize_resources()
            self.terminate_event.wait()
        logging.info("Automation script finished.")

    def close_resources(self):
        if not self.test_mode:
            self.stop_heartbeat()
            self.rabbitmq_manager.stop()
            self.terminate_event.set()  # Set the termination event to release the main thread
            self.driver_manager.close()


if __name__ == "__main__":
    app = MainApp()
    atexit.register(app.close_resources)  # Register cleanup function
    app.run()
