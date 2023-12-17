import sys
import time
import threading
from colorama import init, Fore, Style


class TextUI:
    _colorama_initialized = False
    _loading_stack = []
    _loading_lock = threading.Condition()  # Changed to a Condition for finer control

    @classmethod
    def _initialize_colorama(cls):
        if not cls._colorama_initialized:
            init(convert=True)  # Use Win32 API for better performance
            cls._colorama_initialized = True

    @staticmethod
    def clear_line():
        # Clear current line in Windows Terminal
        sys.stdout.write("\033[K")

    @staticmethod
    def print_message(message, color, style=Style.NORMAL):
        with TextUI._loading_lock:
            TextUI.clear_line()
            print(f"{style}{color}{message}{Style.RESET_ALL}")

    @staticmethod
    def error(message):
        TextUI.print_message(f"Error: {message}", Fore.RED)

    @staticmethod
    def success(message):
        TextUI.print_message(f"Success: {message}", Fore.GREEN)

    @staticmethod
    def info(message):
        TextUI.print_message(f"Info: {message}", Fore.CYAN)

    @staticmethod
    def warning(message):
        TextUI.print_message(f"Warning: {message}", Fore.YELLOW)

    @staticmethod
    def loading(message, duration=0.2, animation_chars="|/-\\", hide_previous=False):
        TextUI._initialize_colorama()

        def animate_loading():
            while True:
                with TextUI._loading_lock:
                    if len(TextUI._loading_stack) == 0:
                        return
                    # Hide previous line if necessary
                    if hide_previous:
                        TextUI.clear_line()
                    for char in animation_chars:
                        sys.stdout.write(f"\r{Fore.YELLOW}{message} {char}{Style.RESET_ALL}")
                        sys.stdout.flush()
                        time.sleep(duration)

        loading_thread = threading.Thread(target=animate_loading)
        loading_thread.daemon = True

        with TextUI._loading_lock:
            TextUI._loading_stack.append((loading_thread, hide_previous))
            loading_thread.start()

        return loading_thread

    @staticmethod
    def stop_loading(loading_thread):
        with TextUI._loading_lock:
            if loading_thread in TextUI._loading_stack:
                TextUI._loading_stack.remove((loading_thread, loading_thread.hide_previous))
            TextUI._loading_lock.notify_all()

