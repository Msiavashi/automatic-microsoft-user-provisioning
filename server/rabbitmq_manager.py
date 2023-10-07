import pika
import threading
import time

class RabbitMQConnectionError(Exception):
    pass

class RabbitMQManager:
    _instances = {}

    def __new__(cls, host, port, queue_name):
        if (host, port, queue_name) in cls._instances:
            return cls._instances[(host, port, queue_name)]

        instance = super(RabbitMQManager, cls).__new__(cls)
        cls._instances[(host, port, queue_name)] = instance
        return instance

    def __init__(self, host, port, queue_name):
        if hasattr(self, 'initialized') and self.initialized:
            return

        self.host = host
        self.port = port
        self.queue_name = queue_name
        self.connection = None
        self.channel = None
        self.initialized = True
        self.heartbeat_thread = None
        self.lock = threading.Lock()

    def _send_heartbeat(self):
        while self.connection and self.connection.is_open:
            with self.lock:
                self.connection.process_data_events()
            time.sleep(10)  # Sleep for 10 seconds between heartbeats

    def _reconnect(self):
        while not self.connection or not self.connection.is_open:
            try:
                self.connect()
            except pika.exceptions.AMQPConnectionError:
                time.sleep(10)  # Sleep for 10 seconds before retrying the connection
            else:
                break  # Exit the loop if the connection was successful

    def connect(self):
        with self.lock:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host, port=self.port, heartbeat=30))
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            if self.heartbeat_thread is None:
                self.heartbeat_thread = threading.Thread(target=self._send_heartbeat)
                self.heartbeat_thread.daemon = True
                self.heartbeat_thread.start()

    def close(self):
        with self.lock:
            if self.connection:
                self.connection.close()

    def is_connected(self):
        """Check if the connection to RabbitMQ is open."""
        return bool(self.connection and self.connection.is_open)

    def start(self):
        self.connect()
        reconnect_thread = threading.Thread(target=self._reconnect)
        reconnect_thread.daemon = True
        reconnect_thread.start()

    def stop(self):
        self.close()

# Usage:
# rabbitmq_manager = RabbitMQManager(host='localhost', port=5672, queue_name='test_queue')
# rabbitmq_manager.start()
# ... do other stuff ...
# rabbitmq_manager.stop()
