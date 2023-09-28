import json
import hug
from rabbitmq_manager import RabbitMQConnectionError
from app import rabbitmq_manager

# Define a decorator to check RabbitMQ connection and handle errors


def rabbitmq_connected(func):
    def wrapper(*args, **kwargs):
        print("Args received in decorator:", args)
        print("Kwargs received in decorator:", kwargs)

        if rabbitmq_manager.connection is None:
            raise RabbitMQConnectionError(
                "Failed to connect to RabbitMQ. Please check the RabbitMQ server.")
        return func(*args, **kwargs)
    return wrapper


@hug.exception(RabbitMQConnectionError)
def handle_rabbitmq_connection_error(exception, response):
    response.status = hug.HTTP_500
    return {"error": str(exception)}


@hug.post("/automatic-user-provisioning")
def auto_user_provisioning_with_email(_input: dict):
    try:
        request_data = json.loads(_input)

        issuer_id = request_data.get("issuerId")
        users = request_data.get("users")

        if not issuer_id:
            return hug.HTTP_400({"error": "Missing 'issuerId' in the request."})

        if not users or not isinstance(users, list):
            return hug.HTTP_400({"error": "Invalid or empty 'users' field in the request."})

        for user in users:
            if not isinstance(user, dict) or "uid" not in user or "email" not in user:
                return hug.HTTP_400({"error": "Invalid user format in the 'users' field."})

            user_data = {
                "userId": user["uid"],
                "email": user["email"],
                "issuerId": issuer_id
            }

            message_body = json.dumps(user_data)
            rabbitmq_manager.channel.basic_publish(
                exchange='', routing_key=rabbitmq_manager.queue_name, body=message_body
            )

        return hug.HTTP_200({"message": "User data added to RabbitMQ for processing"})
    except Exception as e:
        return hug.HTTP_500({"error": f"Internal Server Error: {str(e)}"})


@rabbitmq_connected
@hug.get("/queue-status")
def get_queue_status(response):
    try:
        queue_info = rabbitmq_manager.channel.queue_declare(
            queue=rabbitmq_manager.queue_name, durable=True
        )
        message_count = queue_info.method.message_count

        return {"queue_status": "OK", "message_count": message_count}
    except Exception as e:
        response.status = hug.HTTP_500
        return {"queue_status": "Error", "error_message": str(e)}
