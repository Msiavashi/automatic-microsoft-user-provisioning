import argparse
import logging
import threading
import atexit
from logger import LoggerManager
from driver_manager import DriverManager
from microsoft_credential_manager import MicrosoftSignIn
from rabbitmq_manager import RabbitMQManager


class MainApp:
    """Orchestrates the entire process."""

    def __init__(self):
        LoggerManager.setup_console_logging()
        logging.info("Starting the automation script...")
        self.ms_signin = None
        self.test_mode = False
        self.rabbitmq_manager = None
        self.heartbeat_timer = None
        # Define an event to handle termination
        self.terminate_event = threading.Event()

    def initialize_resources(self):
        if not self.test_mode:
            self.rabbitmq_manager = RabbitMQManager(
                host='localhost', port=5672, queue_name='obr', consumer_callback=self.queue_consumer)
            self.rabbitmq_manager.start()
            self.start_heartbeat()

    def queue_consumer(self, ch, method, properties, body):
        print(f"[[+++]] Received: {body}")
        # Acknowledge message processing
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def start_rabbitmq_consumer(self):
        self.consumer_thread = threading.Thread(
            target=self.rabbitmq_manager.consume,
            args=(self.queue_consumer,))
        self.consumer_thread.daemon = True  # Daemonize thread
        self.consumer_thread.start()
        logging.info("RabbitMQ consumer thread started.")

    def send_heartbeat(self):
        try:
            logging.info("Sending heartbeat...")
            # Implement your heartbeat logic here
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

        driver_manager = DriverManager(mode=args.mode)
        self.ms_signin = MicrosoftSignIn(driver_manager)
        if (self.test_mode):
            self.ms_signin.register_security_key(
                email=args.email, user_id=args.userId, issuer_id=args.issuerId)
        self.initialize_resources()
        driver_manager.close()

        self.terminate_event.wait()
        logging.info("Automation script finished.")

    def close_resources(self):
        if not self.test_mode:
            self.stop_heartbeat()
            self.rabbitmq_manager.stop()
            self.terminate_event.set()  # Set the termination event to release the main thread


if __name__ == "__main__":
    app = MainApp()
    atexit.register(app.close_resources)  # Register cleanup function
    app.run()
