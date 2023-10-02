#!/bin/bash

# Define the Dockerfile path and image name (adjust if necessary)
DOCKER_FILE="Dockerfile"
IMAGE_NAME="selenium-automation"
CONTAINER_NAME="selenium-automation-container"

function build {
    echo "Building Docker image..."
    docker build -t $IMAGE_NAME -f $DOCKER_FILE .
}

function rebuild {
    echo "Rebuilding Docker image..."
    docker rmi $IMAGE_NAME
    build
}

function start {
    echo "Starting Docker container..."
    docker run -d --name $CONTAINER_NAME $IMAGE_NAME
}

function stop {
    echo "Stopping Docker container..."
    docker stop $CONTAINER_NAME
}

function force_stop {
    echo "Force stopping and removing Docker container..."
    docker rm -f $CONTAINER_NAME
}

function status {
    echo "Checking Docker container status..."
    docker ps -a | grep $CONTAINER_NAME
}

function restart {
    echo "Restarting Docker container..."
    stop
    start
}

function docker_logs {
    echo "Displaying Docker logs..."
    docker logs $CONTAINER_NAME
}

function console_logs {
    echo "Displaying console logs..."
    docker exec -it $CONTAINER_NAME bash -c "cat /app/console.log"
}

# Check the command-line arguments
case "$1" in
    build)
        build
        ;;
    rebuild)
        rebuild
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    force-stop)
        force_stop
        ;;
    status)
        status
        ;;
    restart)
        restart
        ;;
    logs)
        docker_logs
        ;;
    console)
        console_logs
        ;;
    *)
        echo "Usage: $0 {build|rebuild|start|stop|force-stop|status|restart|logs|console}"
        exit 1
esac
