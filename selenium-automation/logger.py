import threading
import sys
import logging
import time
import os
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

LOG_COLORS = {
    'ERROR': Fore.RED,
    'DEBUG': Fore.BLUE,
    'INFO': Fore.GREEN,
    'WARNING': Fore.YELLOW,
    'CRITICAL': Fore.MAGENTA,
    'WAITING': Fore.CYAN,
    'RESET': Style.RESET_ALL
}


class ColoredFormatter(logging.Formatter):
    def format(self, record):
        log_message = super().format(record)
        return f"{LOG_COLORS.get(record.levelname, LOG_COLORS['RESET'])}{log_message}{LOG_COLORS['RESET']}"


# Rest of your code remains the same


class LogConfig:
    LOG_LEVEL = logging.INFO  # Set the desired log level here


class LoggerManager:
    """Handles all logging-related functionality."""

    verbose = True  # Class variable to control verbosity

    class TUI:
        loading_message = None
        loading_stopped = None  # Instance variable to store the event

        @staticmethod
        def info(message):
            if not LoggerManager.verbose:
                colored_message = f"{LOG_COLORS['INFO']}INFO: {message}{LOG_COLORS['RESET']}"
                print(colored_message)

        @staticmethod
        def warning(message):
            if not LoggerManager.verbose:
                colored_message = f"{LOG_COLORS['WARNING']}WARNING: {message}{LOG_COLORS['RESET']}"
                print(colored_message)

        @staticmethod
        def success(message):
            if not LoggerManager.verbose:
                colored_message = f"{LOG_COLORS['INFO']}SUCCESS: {message}{LOG_COLORS['RESET']}"
                print(colored_message)

        @staticmethod
        def error(message):
            if not LoggerManager.verbose:
                colored_message = f"{LOG_COLORS['ERROR']}ERROR: {message}{LOG_COLORS['RESET']}"
                print(colored_message)

        @staticmethod
        def start_loading(message="Loading..."):
            """Start a loading animation in a separate thread."""
            if not LoggerManager.verbose:
                colored_message = f"{LOG_COLORS['WAITING']}{message}{LOG_COLORS['RESET']}"
                LoggerManager.TUI.loading_message = colored_message

                def loading_animation():
                    spinner = ['|', '/', '-', '\\']
                    while not LoggerManager.TUI.loading_stopped.is_set():
                        for char in spinner:
                            sys.stdout.write(f"\r{LoggerManager.TUI.loading_message} {char}")
                            sys.stdout.flush()
                            time.sleep(0.1)

                LoggerManager.TUI.loading_stopped = threading.Event()
                loading_thread = threading.Thread(target=loading_animation)
                loading_thread.start()

        @staticmethod
        def stop_loading():
            if LoggerManager.TUI.loading_stopped:
                LoggerManager.TUI.loading_stopped.set()
                time.sleep(1)
                sys.stdout.write(f"\r{' ' * (len(LoggerManager.TUI.loading_message) + 2)}\r")
                sys.stdout.flush()

    @staticmethod
    def setup_console_logging():
        # Setting up console logging only if verbose is True
        if LoggerManager.verbose:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(LogConfig.LOG_LEVEL)
            formatter = ColoredFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            logging.getLogger().addHandler(console_handler)

        # Setting up file logging for console logs
        if not os.path.exists('logs/console_logs'):
            os.makedirs('logs/console_logs')
        console_file_handler = logging.FileHandler(
            f'logs/console_logs/console.log')
        console_file_handler.setLevel(LogConfig.LOG_LEVEL)
        formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(console_file_handler)

        # Setting the log level
        logging.getLogger().setLevel(LogConfig.LOG_LEVEL)

    @staticmethod
    def setup_logging(email):
        if not os.path.exists('logs'):
            os.makedirs('logs')
        logger = logging.getLogger(email)
        logger.setLevel(LogConfig.LOG_LEVEL)
        fh = logging.FileHandler(f'logs/{email}.log')
        fh.setLevel(LogConfig.LOG_LEVEL)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        return logger

    @staticmethod
    def capture_screenshot(driver, email, filename=None):
        """Capture a screenshot."""
        try:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            screenshot_dir = f'screenshots/{email}'
            email_dir = os.path.join(screenshot_dir, email)
            os.makedirs(email_dir, exist_ok=True)

            if filename is None:
                filename = f"{email}_{timestamp}.png"
            elif not filename.endswith('.png'):
                filename += '.png'

            screenshot_path = os.path.join(email_dir, filename)
            driver.save_screenshot(screenshot_path)
        except Exception as e:
            logging.error(f"Error capturing screenshot: {str(e)}")

    @staticmethod
    def capture_browser_logs(driver, email):
        """Capture browser logs."""
        try:
            browser_logs = driver.get_log('browser')
            with open(f'logs/{email}_browser_logs.txt', 'w') as f:
                for entry in browser_logs:
                    f.write(str(entry))
        except Exception as e:
            logging.error(f"Error capturing browser logs: {str(e)}")
