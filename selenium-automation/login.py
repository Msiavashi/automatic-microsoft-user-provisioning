import os
import time
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import json
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from text_ui import TextUI

load_dotenv()

class LoginServer(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        try:
            if path.strip() == '/favicon.ico':
                self.send_response(204)  # Send a 204 No Content response for favicon requests
                self.end_headers()
                return
            if path.strip() == '/login-result':
                query_params = parse_qs(parsed_url.query)
                api_key = query_params.get('apikey', [None])[0]
                azure_id = query_params.get('azureId', [None])[0]
                if api_key:
                    Login.store_credentials(api_key, Login.DURATION, azure_id)
                    response_message = "Login successful! Session retrieved. You may now use the tool."
                    TextUI.success(response_message)
                    self.send_response(200, "Login successful")
                else:
                    response_message = "Login failed. Missing APIKey."
                    TextUI.error(response_message)
                    self.send_response(400, "Login failed: Missing APIKey")

                self.send_response_headers()
                self.send_html_response(response_message)
            else:
                print(f"Invalid path: {path}")
                self.send_response(404, "Not Found: Invalid Path")
        except Exception as e:
            print(f"Error in LoginServer: {e}")
            self.send_response(500, "Internal Server Error")
        finally:
            Login.shutdown_flag = True

    def send_response_headers(self):
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def send_html_response(self, response_message):
        html_response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta http-equiv="refresh" content="3;url=https://panel.idmelon.com">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f5f5f5;
                    text-align: center;
                    padding: 20px;
                }}
                .container {{
                    background-color: #fff;
                    border-radius: 5px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
                    padding: 20px;
                }}
                .message {{
                    font-size: 18px;
                    margin-bottom: 20px;
                }}
                .redirect {{
                    font-size: 14px;
                    color: #555;
                }}
                a {{
                    text-decoration: none;
                    color: #007bff;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <p class="message">{response_message}</p>
                <p class="redirect">Redirecting to <a href="https://panel.idmelon.com">https://panel.idmelon.com</a> in 3 seconds...</p>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html_response.encode())

class Login:
    SECRET_KEY = os.getenv("SECRET_KEY")
    VERSION = os.getenv("VERSION")
    CREDENTIALS_FILE = "app_data.dat"
    DURATION = 43200  # 12 hours in seconds

    http_server = None
    server_thread = None
    shutdown_flag = False

    @staticmethod
    def start():
        Login.clear_console()
        print(Login.logo)
        print(f"Version: {Login.VERSION}\n")

        TextUI.warning("Please ensure that you are logged into your workspace at the following URL before proceeding: https://panel.idmelon.com")
        print("Once you have logged in, please return to this window.\n")
        input("Press any key to proceed...\n")

        print("Waiting for you to login...")

        threading.Thread(target=Login.open_browser, args=(os.getenv("LOGIN_URL"),)).start()
        Login.server_thread = threading.Thread(target=Login.start_http_server)
        Login.server_thread.start()

        try:
            while not Login.shutdown_flag:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nKeyboard Interrupt received, shutting down server...")
        finally:
            Login.shutdown_flag = True
            Login.shutdown_server()

    @staticmethod
    def clear_console():
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def open_browser(url):
        webbrowser.open(url)

    @staticmethod
    def start_http_server():
        server_address = ('localhost', 8080)
        Login.http_server = HTTPServer(server_address, LoginServer)
        Login.http_server.serve_forever()

    @staticmethod
    def load_credentials():
        try:
            cipher_suite = Fernet(Login.SECRET_KEY.encode())
            with open(Login.CREDENTIALS_FILE, "rb") as file:
                decrypted_data = cipher_suite.decrypt(file.read())
                return json.loads(decrypted_data.decode("utf-8"))
        except Exception as e:
            return None

    @staticmethod
    def validate_api_key(credentials):
        try:
            if credentials:
                current_time = int(time.time())
                expiration_time = credentials["GeneratedTime"] + credentials["Duration"]
                return current_time <= expiration_time
            return False
        except KeyError:
            return False

    @staticmethod
    def store_credentials(api_key, duration, azure_id):
        try:
            cipher_suite = Fernet(Login.SECRET_KEY.encode())
            credentials = {
                "APIKey": api_key,
                "Duration": duration,
                "GeneratedTime": int(time.time()),
                "AzureId": azure_id
            }
            encrypted_data = cipher_suite.encrypt(json.dumps(credentials).encode())
            with open(Login.CREDENTIALS_FILE, "wb") as file:
                file.write(encrypted_data)
        except Exception as e:
            print(f"Error storing credentials: {e}")

    @staticmethod
    def shutdown_server():
        if Login.http_server:
            Login.http_server.shutdown()

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