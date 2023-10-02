#!/bin/bash

# Deactivate virtual environment (if active)
if command -v deactivate &> /dev/null; then
    deactivate
fi

# Remove virtual environment
rm -rf myenv

echo 'Cleaned up virtual environment!'

# Stop RQ worker
pkill -f 'rq worker'
echo 'Stopped RQ worker!'

# Restart configurations
./setup_project.sh
echo 'Restarted configurations!'
