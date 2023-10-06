import pika
import threading
import logging
import os


class RabbitMQConnectionError(Exception):
    pass


class RabbitMQManager:
    _instances = {}
    _lock = threading.Lock()  # Lock for thread-safe singleton instance creation

    def __new__(cls, host, port, queue_name):
        with cls._lock:
            if (host, port, queue_name) in cls._instances:
                return cls._instances[(host, port, queue_name)]

            instance = super(RabbitMQManager, cls).__new__(cls)
            cls._instances[(host, port, queue_name)] = instance
            return instance

    def __init__(self, host, port, queue_name):
        with self._lock:
            if hasattr(self, 'initialized') and self.initialized:
                return

            self.host = host
            self.port = port
            self.queue_name = queue_name
            self.connection = None
            self.channel = None
            self.initialized = True

    def connect(self):
        with self._lock:
            try:
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=self.host, port=self.port, heartbeat=580))
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue=self.queue_name, durable=True)
            except pika.exceptions.AMQPConnectionError as rabbitmq_error:
                logging.exception(
                    f"Error connecting to RabbitMQ: {rabbitmq_error}")
                raise RabbitMQConnectionError(
                    f"Error connecting to RabbitMQ: {rabbitmq_error}")

    def close(self):
        with self._lock:
            try:
                if self.connection:
                    self.connection.close()
            except pika.exceptions.AMQPConnectionError as e:
                logging.exception(f"Error closing RabbitMQ connection: {e}")

    def is_connected(self):
        with self._lock:
            return bool(self.connection and self.connection.is_open)


# Usage
rabbitmq_manager = RabbitMQManager(
    host=os.environ.get("RABBITMQ_HOSTNAME", "localhost"), port=5672, queue_name='obr'
)
