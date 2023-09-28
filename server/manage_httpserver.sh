#!/bin/bash

# Define the Docker image name
IMAGE_NAME="obr-http-server"

# Define the Docker container name
CONTAINER_NAME="obr-http-container"

# Build the Docker image
build_image() {
    docker build -t $IMAGE_NAME .
}

# Rebuild the Docker image
rebuild_image() {
    docker build -t $IMAGE_NAME . --no-cache
}

# Start the Docker container
start_container() {
    docker run -d -p 8080:8080 --name $CONTAINER_NAME $IMAGE_NAME
}

# Stop the Docker container
stop_container() {
    docker stop $CONTAINER_NAME
}

# Restart the Docker container
restart_container() {
    stop_container
    start_container
}

# Forcefully stop and remove the Docker container
force_stop_container() {
    docker rm -f $CONTAINER_NAME
}

# Display usage information
usage() {
    echo "Usage: $0 [build|rebuild|start|stop|restart|force-stop]"
    exit 1
}

# Check the number of arguments
if [ $# -eq 0 ]; then
    usage
fi

# Parse the command-line argument
case "$1" in
    build)
        build_image
        ;;
    rebuild)
        rebuild_image
        ;;
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
    *)
        usage
        ;;
esac

exit 0
