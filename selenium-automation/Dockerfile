# Start with a base image containing Python 3.8 and necessary tools
FROM python:3.8-slim

# The application's jar file
ARG APP_FILE=main.py

# Make port 80 available to the world outside this container
EXPOSE 80

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory's contents into the container at /app
COPY . /app

# Install wget, unzip, and gnupg for downloading, extracting, and managing keys
RUN apt-get update && \
    apt-get install -y wget unzip gnupg

# Download and install Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make sure ChromeDriver is in the PATH
ENV PATH /app:$PATH

# Run main.py when the container launches
CMD ["python", "main.py"]
