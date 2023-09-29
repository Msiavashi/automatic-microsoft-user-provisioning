import pika
import atexit
import time
import threading


class RabbitMQConnectionError(Exception):
    pass


class RabbitMQManager:
    _instances = {}

    def __new__(cls, host, port, queue_name, consumer_callback):
        if (host, port, queue_name) in cls._instances:
            return cls._instances[(host, port, queue_name)]

        instance = super(RabbitMQManager, cls).__new__(cls)
        cls._instances[(host, port, queue_name)] = instance
        return instance

    def __init__(self, host, port, queue_name, consumer_callback):
        if hasattr(self, 'initialized') and self.initialized:
            return

        self.host = host
        self.port = port
        self.queue_name = queue_name
        self.consumer_callback = consumer_callback
        self.connection = None
        self.channel = None
        self.initialized = True
        self._consumer_thread = None

    def connect(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host, port=self.port, heartbeat=30))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue_name, durable=True)

    def close(self):
        if self.connection:
            self.connection.close()
            self.stop_heartbeat()

    def is_connected(self):
        """Check if the connection to RabbitMQ is open."""
        return bool(self.connection and self.connection.is_open)

    def send_heartbeat(self):
        try:
            # Check if the connection is open before sending heartbeat
            if self.connection and self.connection.is_open:
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

    def process_message(self, ch, method, properties, body):
        # A sample consumer. This is not used for production.
        print(f"Received message: {body}")
        time.sleep(5)
        # Acknowledge message processing
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def consume(self):
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self.consumer_callback,
            auto_ack=False
        )
        self.channel.start_consuming()

    def start(self):
        self.connect()
        self._consumer_thread = threading.Thread(target=self.consume)
        self._consumer_thread.daemon = True
        self._consumer_thread.start()

    def stop(self):
        if self.connection:
            self.connection.close()
