#!/bin/bash

# Define the Docker Compose file
COMPOSE_FILE="docker-compose.yml"

# Function to bring up the containers
up() {
    docker-compose -f $COMPOSE_FILE up -d
}

# Function to bring down the containers
down() {
    docker-compose -f $COMPOSE_FILE down
}

# Function to destroy the containers and volumes
destroy() {
    docker-compose -f $COMPOSE_FILE down -v
}

# Function to restart the containers
restart() {
    down
    up
}

# Function to rebuild the containers
rebuild() {
    docker-compose -f $COMPOSE_FILE down
    docker-compose -f $COMPOSE_FILE build
    up
}

# Function to display the status of the containers
status() {
    docker-compose -f $COMPOSE_FILE ps
}

# Display usage information
usage() {
    echo "Usage: $0 [up|down|destroy|restart|rebuild|status]"
    exit 1
}

# Check the number of arguments
if [ $# -eq 0 ]; then
    usage
fi

# Parse the command-line argument
case "$1" in
    up)
        up
        ;;
    down)
        down
        ;;
    destroy)
        destroy
        ;;
    restart)
        restart
        ;;
    rebuild)
        rebuild
        ;;
    status)
        status
        ;;
    *)
        usage
        ;;
esac

exit 0
