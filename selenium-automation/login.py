import os
import time
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()


class Login:
    SECRET_KEY = os.getenv("SECRET_KEY")
    VERSION = os.getenv("VERSION")
    CREDENTIALS_FILE = "app_data.dat"

    http_server = None
    server_thread = None
    shutdown_flag = False

    @staticmethod
    def start():
        """Starts the login process."""
        Login.clear_console()
        print(Login.logo)
        print(f"Version: {Login.VERSION}")
        print("Waiting for you to login...")

        threading.Thread(target=Login.open_browser, args=(os.getenv("LOGIN_URL"),)).start()
        Login.server_thread = threading.Thread(target=Login.start_http_server)
        Login.server_thread.start()

        # Continually check if the server should be shut down
        while not Login.shutdown_flag:
            time.sleep(1)

        Login.shutdown_server()

    @staticmethod
    def clear_console():
        """Clears the console screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def open_browser(url):
        """Opens a web browser with the given URL."""
        webbrowser.open(url)

    @staticmethod
    def start_http_server():
        """Starts the HTTP server for handling login."""
        server_address = ('localhost', 8001)
        Login.http_server = HTTPServer(server_address, Login.LoginServer)
        Login.http_server.serve_forever()

    @staticmethod
    def load_credentials():
        """Loads and decrypts the credentials from the file."""
        try:
            cipher_suite = Fernet(Login.SECRET_KEY.encode())
            with open(Login.CREDENTIALS_FILE, "rb") as file:
                decrypted_data = cipher_suite.decrypt(file.read())
                return json.loads(decrypted_data.decode("utf-8"))
        except Exception as e:
            print(f"Error loading credentials: {e}")
            return None

    @staticmethod
    def validate_api_key(credentials):
        """Validates the API key."""
        try:
            if credentials:
                current_time = int(time.time())
                expiration_time = credentials["GeneratedTime"] + credentials["Duration"]
                return current_time <= expiration_time
            return False
        except KeyError:
            return False

    @staticmethod
    def store_credentials(api_key, duration):
        """Encrypts and stores credentials in a file."""
        try:
            cipher_suite = Fernet(Login.SECRET_KEY.encode())
            credentials = {
                "APIKey": api_key,
                "Duration": duration,
                "GeneratedTime": int(time.time())
            }
            encrypted_data = cipher_suite.encrypt(json.dumps(credentials).encode())
            with open(Login.CREDENTIALS_FILE, "wb") as file:
                file.write(encrypted_data)
            print("Credentials stored successfully.")
        except Exception as e:
            print(f"Error storing credentials: {e}")

    @staticmethod
    def shutdown_server():
        """Shuts down the HTTP server."""
        if Login.http_server:
            Login.http_server.shutdown()

    class LoginServer(BaseHTTPRequestHandler):
        def do_POST(self):
            """Handles POST requests for login."""
            try:
                content_length = int(self.headers['Content-Length'])
                data = json.loads(self.rfile.read(content_length).decode('utf-8'))
                if data.get('APIKey') and data.get('Duration', -1) >= 0:
                    Login.store_credentials(data['APIKey'], data['Duration'])
                    print("Login successful! Credentials stored.")
                else:
                    print("Login failed. Please try again.")
                # Set the shutdown flag
                Login.shutdown_flag = True
            except Exception as e:
                print(f"Error in LoginServer: {e}")

    logo = r"""
 ______  _______   __       __            __                     
|      \|       \ |  \     /  \          |  \                    
 \$$$$$$| $$$$$$$\| $$\   /  $$  ______  | $$  ______   _______  
  | $$  | $$  | $$| $$$\ /  $$$ /      \ | $$ /      \ |       \ 
  | $$  | $$  | $$| $$$$\  $$$$|  $$$$$$\| $$|  $$$$$$\| $$$$$$$\
  | $$  | $$  | $$| $$\$$ $$ $$| $$    $$| $$| $$  | $$| $$  | $$
 _| $$_ | $$__/ $$| $$ \$$$| $$| $$$$$$$$| $$| $$__/ $$| $$  | $$
|   $$ \| $$    $$| $$  \$ | $$ \$$     \| $$ \$$    $$| $$  | $$
 \$$$$$$ \$$$$$$$  \$$      \$$  \$$$$$$$ \$$  \$$$$$$  \$$   \$$
    """


# if __name__ == "__main__":
#     Login.start()
#     credentials = Login.load_credentials()
#     if Login.validate_api_key(credentials):
#         print("API key is valid.")
#     else:
#         print("API key is invalid or expired.")
