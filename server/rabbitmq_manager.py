import pika
import threading


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
        self.heartbeat_timer = None
        self.initialized = True

    def connect(self):
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host, port=self.port, heartbeat=360))
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            self.start_heartbeat()
        except Exception as rabbitmq_error:
            raise RabbitMQConnectionError(
                f"Error connecting to RabbitMQ: {rabbitmq_error}")

    def close(self):
        if self.connection:
            self.connection.close()
            self.stop_heartbeat()

    def send_heartbeat(self):
        try:
            self.connection.process_data_events()
        except Exception as e:
            print(f"Error sending heartbeat: {e}")

    def is_connected(self):
        """Check if the connection to RabbitMQ is open."""
        return bool(self.connection and self.connection.is_open)

    def send_heartbeat(self):
        try:
            if self.connection and self.connection.is_open:  # Check if the connection is open before sending heartbeat
                self.connection.process_data_events()
                self.start_heartbeat()  # Reschedule the next heartbeat
        except Exception as e:
            print(f"Error sending heartbeat: {e}")
            self.close()  # Close the connection on error, if needed

    def start_heartbeat(self):
        if self.heartbeat_timer:
            self.heartbeat_timer.cancel()
        self.heartbeat_timer = threading.Timer(10, self.send_heartbeat)
        self.heartbeat_timer.daemon = True
        self.heartbeat_timer.start()

    def stop_heartbeat(self):
        if self.heartbeat_timer:
            self.heartbeat_timer.cancel()
