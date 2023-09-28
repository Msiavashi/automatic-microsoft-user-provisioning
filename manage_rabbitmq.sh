#!/bin/bash

# Define the Docker image name, container name, and RabbitMQ channel name
RABBITMQ_IMAGE="rabbitmq:latest"
RABBITMQ_CONTAINER="my_rabbitmq_container"

# Check if the RabbitMQ Docker image is already pulled
if [[ "$(docker images -q $RABBITMQ_IMAGE 2> /dev/null)" == "" ]]; then
  echo "Pulling the RabbitMQ Docker image..."
  docker pull $RABBITMQ_IMAGE
fi

# Function to create a RabbitMQ queue
create_queue() {
  local queue_name="$1"
  
  if [[ "$(docker ps -q -f name=$RABBITMQ_CONTAINER)" != "" ]]; then
    echo "Creating RabbitMQ queue '$queue_name'..."
    docker exec -it $RABBITMQ_CONTAINER bash -c "rabbitmqadmin declare queue name=$queue_name"
    echo "RabbitMQ queue '$queue_name' created successfully."
  else
    echo "RabbitMQ container is not running."
  fi
}

# Function to destroy (delete) a RabbitMQ queue
destroy_queue() {
  local queue_name="$1"
  
  if [[ "$(docker ps -q -f name=$RABBITMQ_CONTAINER)" != "" ]]; then
    echo "Destroying RabbitMQ queue '$queue_name'..."
    docker exec -it $RABBITMQ_CONTAINER bash -c "rabbitmqadmin delete queue name=$queue_name"
    echo "RabbitMQ queue '$queue_name' destroyed successfully."
  else
    echo "RabbitMQ container is not running."
  fi
}

# Function to start the RabbitMQ container
start_container() {
  if [[ "$(docker ps -a -q -f name=$RABBITMQ_CONTAINER 2> /dev/null)" == "" ]]; then
    echo "Creating and starting RabbitMQ container..."
    docker run -d --name $RABBITMQ_CONTAINER -p 5672:5672 -p 15672:15672 $RABBITMQ_IMAGE
  else
    if [[ "$(docker ps -q -f name=$RABBITMQ_CONTAINER)" == "" ]]; then
      echo "Starting existing RabbitMQ container..."
      docker start $RABBITMQ_CONTAINER
    else
      echo "RabbitMQ container is already running."
    fi
  fi
}

# Function to stop the RabbitMQ container
stop_container() {
  if [[ "$(docker ps -q -f name=$RABBITMQ_CONTAINER)" != "" ]]; then
    echo "Stopping RabbitMQ container..."
    docker stop $RABBITMQ_CONTAINER
  else
    echo "RabbitMQ container is not running."
  fi
}

# Function to restart the RabbitMQ container
restart_container() {
  stop_container
  start_container
}

# Function to forcefully stop and remove the RabbitMQ container
force_stop_container() {
  if [[ "$(docker ps -q -f name=$RABBITMQ_CONTAINER)" != "" ]]; then
    echo "Forcefully stopping RabbitMQ container..."
    docker rm -f $RABBITMQ_CONTAINER
  else
    echo "RabbitMQ container is not running."
  fi
}

# Function to test RabbitMQ by publishing and consuming a message
test_container() {
  if [[ "$(docker ps -q -f name=$RABBITMQ_CONTAINER)" != "" ]]; then
    echo "Testing RabbitMQ container..."
    docker exec -it $RABBITMQ_CONTAINER bash -c "dpkg -l | grep rabbitmq-server" >/dev/null 2>&1
    if [[ $? -ne 0 ]]; then
      echo "Installing rabbitmq-server..."
      docker exec -it $RABBITMQ_CONTAINER bash -c "apt-get update && apt-get install -y rabbitmq-server"
    else
      echo "rabbitmq-server is already installed."
    fi
    docker exec -it $RABBITMQ_CONTAINER rabbitmq-plugins list | grep -q 'rabbitmq_management'
    if [[ $? -ne 0 ]]; then
      echo "Enabling RabbitMQ management plugin..."
      docker exec -it $RABBITMQ_CONTAINER rabbitmq-plugins enable rabbitmq_management
    else
      echo "RabbitMQ management plugin is already enabled."
    fi
    docker exec -it $RABBITMQ_CONTAINER rabbitmqctl wait /var/lib/rabbitmq/mnesia/rabbit\@$HOSTNAME.pid
    docker exec -it $RABBITMQ_CONTAINER bash -c "echo 'Test message' | rabbitmqadmin publish exchange=amq.default routing_key=test"
    message="$(docker exec -it $RABBITMQ_CONTAINER rabbitmqadmin get queue=test count=1)"
    if [[ "$message" == *"Test message"* ]]; then
      echo "RabbitMQ test successful. Received message: $message"
    else
      echo "RabbitMQ test failed. Could not receive the expected message."
    fi
  else
    echo "RabbitMQ container is not running."
  fi
}

# Check the command-line arguments to determine the action
case "$1" in
  start)
    start_container
    ;;
  stop)
    stop_container
    ;;
  restart)
    restart_container
    ;;
  force-stop)
    force_stop_container
    ;;
  test)
    test_container
    ;;
  create-queue)
    if [ -z "$2" ]; then
      echo "Usage: $0 create-queue <queue_name>"
      exit 1
    fi
    create_queue "$2"
    ;;
  destroy-queue)
    if [ -z "$2" ]; then
      echo "Usage: $0 destroy-queue <queue_name>"
      exit 1
    fi
    destroy_queue "$2"
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|force-stop|test|create-channel|destroy-channel|create-queue|destroy-queue}"
    exit 1
esac
