#!/bin/bash

# Navigate to the project directory (if not already there)
cd "$(dirname "$0")"

# Set up virtual environments and dependencies for both sub-projects
for SUB_PROJECT in selenium-automation server; do
    cd "$SUB_PROJECT"
    
    # Create and activate virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip and install necessary packages from requirements.txt
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Deactivate virtual environment before moving to next sub-project
    deactivate
    
    cd ..
done

# Placeholder for any additional initialization steps like starting docker-compose, etc.
# docker-compose up -d

echo 'Project initialized!'

# Start the RQ worker for the queue system
# Note: Ensure that this is required and the RQ worker is set up correctly
# rq worker my_queue &
# echo 'RQ worker started for my_queue!'
