import logging
import time
import os

LOG_COLORS = {
    'ERROR': '\033[91m',
    'DEBUG': '\033[94m',
    'INFO': '\033[92m',
    'WARNING': '\033[93m',
    'CRITICAL': '\033[95m',
    'RESET': '\033[0m'
}

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        log_message = super().format(record)
        return f"{LOG_COLORS.get(record.levelname, LOG_COLORS['RESET'])}{log_message}{LOG_COLORS['RESET']}"


class LoggerManager:
    """Handles all logging-related functionality."""

    @staticmethod
    def setup_console_logging():
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        formatter = ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logging.getLogger().addHandler(console_handler)
        logging.getLogger().setLevel(logging.DEBUG)

    @staticmethod
    def setup_logger(email):
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

    @staticmethod
    def capture_screenshot(driver, email):
        return
        """Capture a screenshot."""
        try:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            driver.save_screenshot(f'screenshots/{email}_{timestamp}.png')
        except Exception as e:
            logging.error(f"Error capturing screenshot: {str(e)}")

    @staticmethod
    def capture_browser_logs(driver, email):
        return
        """Capture browser logs."""
        try:
            browser_logs = driver.get_log('browser')
            with open(f'logs/{email}_browser_logs.txt', 'w') as f:
                for entry in browser_logs:
                    f.write(str(entry))
        except Exception as e:
            logging.error(f"Error capturing browser logs: {str(e)}")
