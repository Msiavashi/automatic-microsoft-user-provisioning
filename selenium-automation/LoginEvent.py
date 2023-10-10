import threading


class LoginEvent:
    def __init__(self):
        self.event = threading.Event()
        self.successful_thread_id = None
        self.lock = threading.Lock()  # Lock to ensure thread safety

    def set(self, thread_id):
        with self.lock:
            self.successful_thread_id = thread_id
            self.event.set()

    def is_set(self):
        with self.lock:
            return self.event.is_set()

    def clear(self):
        with self.lock:
            self.successful_thread_id = None
            self.event.clear()

    def is_set_by_this_thread(self):
        """
        Check whether the calling thread is the one that set the event.

        Returns:
            bool: True if the calling thread set the event, False otherwise.
        """
        with self.lock:
            return threading.get_ident() == self.successful_thread_id
