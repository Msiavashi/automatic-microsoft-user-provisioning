#!/bin/bash

# Create and activate virtual environment
python3 -m venv venv
source myenv/bin/activate

# Upgrade pip and install necessary packages from requirements.txt
pip install --upgrade pip
pip install -r requirements.txt

# Check if Redis is installed and running
if ! command -v redis-server &> /dev/null; then
    echo 'Error: Redis is not installed. Please install Redis and start the service.'
    exit 1
fi

# Initialize the Selenium project
# Placeholder for any additional initialization steps

echo 'Project initialized!'

# Start the RQ worker for the queue system
rq worker my_queue &
echo 'RQ worker started for my_queue!'
