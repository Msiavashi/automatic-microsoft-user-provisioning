import sys
import os


class Config:
    # Static method to get the base directory of the application
    @staticmethod
    def get_base_dir():
        if getattr(sys, 'frozen', False):
            # If the application is run as a PyInstaller bundle, this is the path to the bundle
            return sys._MEIPASS
        else:
            # The application is not bundled, so the path is the directory of this script
            return os.path.dirname(os.path.abspath(__file__))

    # Static method to get the path to chromedriver.exe
    @staticmethod
    def get_chrome_driver_path():
        return os.path.join(Config.get_base_dir(), 'chromedriver.exe')

    # Static method to get the path to makeCredential.js
    @staticmethod
    def get_make_credential_path():
        return os.path.join(Config.get_base_dir(), 'makeCredential.js')

    # Static method to get the path to .env
    @staticmethod
    def get_env_path():
        return os.path.join(Config.get_base_dir(), '.env')
