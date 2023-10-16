#!/bin/bash

# Check if Chrome is already installed
if dpkg -l | grep google-chrome-stable &>/dev/null; then
  echo "Google Chrome is already installed."
else
  # Add Google Chrome repository and key
  wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
  echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list

  # Update the package manager and install Chrome
  sudo apt update
  sudo apt install google-chrome-stable -y

  # Check installation success
  if dpkg -l | grep google-chrome-stable &>/dev/null; then
    echo "Google Chrome has been successfully installed."
  else
    echo "Error: Google Chrome installation failed."
  fi
fi
