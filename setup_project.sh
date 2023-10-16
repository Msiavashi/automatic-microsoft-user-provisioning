#!/bin/bash

# Navigate to the project directory (if not already there)
cd "$(dirname "$0")"

sudo apt-get update
sudo apt-get install python3-venv

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

echo 'Project initialized!'

sudo apt-get install -y libnss3
sudo ./selenium-automation/install_chrome.sh
