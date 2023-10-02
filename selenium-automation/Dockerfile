# Start with a base image containing Java runtime
FROM python:3.8-slim

# The application's jar file
ARG APP_FILE=main.py

# Make port 80 available to the world outside this container
EXPOSE 80

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory's contents into the container at /app
COPY . /app

# Install Chrome and required libraries
RUN apt-get update && \
    apt-get install -y wget unzip && \
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i google-chrome-stable_current_amd64.deb; apt-get -fy install

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make sure ChromeDriver is in the PATH
ENV PATH /app:$PATH

# Run main.py when the container launches
CMD ["python", "main.py"]
