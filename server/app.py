import atexit
import time
import hug
import os
from rabbitmq_manager import RabbitMQManager, RabbitMQConnectionError


# Read the HOSTNAME environment variable to get the hostname
hostname = os.environ.get('RABBITMQ_HOSTNAME', 'localhost')

rabbitmq_manager = RabbitMQManager(hostname, 5672, 'obr')

api = hug.API(__name__)


@hug.extend_api()
def import_api_handlers():
    import api_handlers
    return [api_handlers]


def init():
    max_retries = 5
    delay = 5
    for attempt in range(1, max_retries + 1):
        try:
            rabbitmq_manager.start()
            print("Connected to RabbitMQ")
            break
        except RabbitMQConnectionError as e:
            print(f"Failed to connect to RabbitMQ on attempt {attempt}: {e}")
            if attempt < max_retries:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("Max retries reached. Exiting...")
                exit(1)


def close_rabbitmq_connection():
    rabbitmq_manager.close()


atexit.register(close_rabbitmq_connection)

if __name__ == '__main__':
    init()
    api.http.serve(port=8080)
