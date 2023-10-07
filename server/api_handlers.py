import json
import hug
from rabbitmq_manager import RabbitMQConnectionError
from app import rabbitmq_manager


def rabbitmq_connected(func):
    # Define a decorator to check RabbitMQ connection and handle errors
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


@rabbitmq_connected
@hug.post("/automatic-user-provisioning")
def auto_user_provisioning_with_email(body: hug.types.json, response):
    try:
        issuer_id = body.get("issuer")
        users = body.get("users")
        request_id = body.get("requestId")

        if not request_id:
            response.status = hug.HTTP_400
            return {"error": "Missing 'requestId' in the request."}

        if not issuer_id:
            response.status = hug.HTTP_400
            return {"error": "Missing 'issuer' in the request."}

        if not users or not isinstance(users, list):
            response.status = hug.HTTP_400
            return {"error": "Invalid or empty 'users' field in the request."}

        for user in users:
            if not isinstance(user, dict) or "uid" not in user or "email" not in user:
                response.status = hug.HTTP_400
                return {"error": "Invalid user format in the 'users' field."}

            user_data = {
                "requestId": request_id,
                "userId": user["uid"],
                "email": user["email"],
                "issuerId": issuer_id
            }

            message_body = json.dumps(user_data)
            rabbitmq_manager.channel.basic_publish(
                exchange='', routing_key=rabbitmq_manager.queue_name, body=message_body
            )

        response.status = hug.HTTP_200
        return {"message": "User data added to RabbitMQ for processing"}
    except Exception as e:
        response.status = hug.HTTP_500
        return {"error": f"Internal Server Error: {str(e)}"}


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


@rabbitmq_connected
@hug.patch("/azureAutoOBR")
def update_request_status_api(body: hug.types.json, response):
    # This is only implemented for internal test environment and should not be used in production.
    try:
        # Extract data from the request JSON body
        user_id = body.get("userId")
        requestId = body.get("requestId")
        status: str = body.get("status")
        description = body.get("description")

        # Your logic to update the request status here
        if status.lower() == "failed":
            response.status = hug.HTTP_400
        else:
            response.status = hug.HTTP_200
        return {"message": description}
    except Exception as e:
        response.status = hug.HTTP_500
        return {"error": f"Internal Server Error: {str(e)}"}
