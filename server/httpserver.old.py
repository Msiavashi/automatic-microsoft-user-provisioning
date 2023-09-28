import hug
import atexit
import json
import pika
import threading


class RabbitMQManager:
    def __init__(self, host, port, queue_name):
        self.host = host
        self.port = port
        self.queue_name = queue_name
        self.connection = None
        self.channel = None
        self.heartbeat_timer = None

    def connect(self):
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host, port=self.port, heartbeat=5))
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            # Start the heartbeat timer
            self.start_heartbeat()
        except Exception as rabbitmq_error:
            print(f"Error connecting to RabbitMQ: {rabbitmq_error}")
            self.connection = None

    def close(self):
        if self.connection is not None:
            self.connection.close()
            # Stop the heartbeat timer when closing the connection
            self.stop_heartbeat()

    def send_heartbeat(self):
        try:
            self.connection.process_data_events()
        except Exception as e:
            print(f"Error sending heartbeat: {e}")

    def start_heartbeat(self):
        # Schedule the send_heartbeat function to be called every 5 seconds
        self.heartbeat_timer = threading.Timer(5, self.start_heartbeat)
        # Allow the timer to be stopped when the program exits
        self.heartbeat_timer.daemon = True
        self.heartbeat_timer.start()

    def stop_heartbeat(self):
        if self.heartbeat_timer:
            self.heartbeat_timer.cancel()


# Configure RabbitMQ connection parameters
rabbitmq_host = 'localhost'
rabbitmq_port = 5672  # Default RabbitMQ port
rabbitmq_queue_name = 'obr'

# Create a RabbitMQManager instance and connect to RabbitMQ
rabbitmq_manager = RabbitMQManager(
    rabbitmq_host, rabbitmq_port, rabbitmq_queue_name)
rabbitmq_manager.connect()


@hug.post("/automatic-user-provisioning")
def auto_user_provisioning_with_email(_input, api_key=None):
    try:
        if rabbitmq_manager.connection is None:
            raise Exception(
                "Failed to connect to RabbitMQ. Please check the RabbitMQ server.")

        issuer_id = _input.get("issuerId")
        users = _input.get("users")

        if not issuer_id:
            raise ValueError("Missing 'issuerId' in the request.")

        if not users or not isinstance(users, list):
            raise ValueError(
                "Invalid or empty 'users' field in the request.")

        for user in users:
            if not isinstance(user, dict) or "uid" not in user or "email" not in user:
                raise ValueError(
                    "Invalid user format in the 'users' field.")

            user_data = {
                "userId": user["uid"],
                "email": user["email"],
                "issuerId": issuer_id
            }

            # Convert the user_data to JSON and publish it to RabbitMQ
            message_body = json.dumps(user_data)
            rabbitmq_manager.channel.basic_publish(
                exchange='', routing_key=rabbitmq_manager.queue_name, body=message_body)

        return {"message": "User data added to RabbitMQ for processing"}
    except ValueError as e:
        # Return a 400 Bad Request status code for validation errors
        return {"error": f"Bad Request: {str(e)}"}, 400
    except Exception as e:
        # Return a 500 Internal Server Error for other exceptions
        return {"error": f"Internal Server Error: {str(e)}"}, 500


@hug.get("/queue-status")
def get_queue_status():
    try:
        if rabbitmq_manager.connection is None:
            raise Exception(
                "Failed to connect to RabbitMQ. Please check the RabbitMQ server.")

        # Get the number of messages in the queue
        queue_info = rabbitmq_manager.channel.queue_declare(
            queue=rabbitmq_manager.queue_name, durable=True)
        message_count = queue_info.method.message_count

        return {"queue_status": "OK", "message_count": message_count}
    except Exception as e:
        return {"queue_status": "Error", "error_message": str(e)}


# Create an instance of the hug.API class
api = hug.API(__name__)


# Close the RabbitMQ connection when the application is shut down


@hug.local()
def close_rabbitmq_connection():
    rabbitmq_manager.close()


# Ensure the RabbitMQ connection is closed when the program exits
atexit.register(close_rabbitmq_connection)


def is_connected():
    """Check if the connection to RabbitMQ is open."""
    return bool(rabbitmq_manager.connection and rabbitmq_manager.connection.is_open)


print(is_connected())


# Start the server on port 8080
if __name__ == '__main__':
    api.http.serve(port=8080)
