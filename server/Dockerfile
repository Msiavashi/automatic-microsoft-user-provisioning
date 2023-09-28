# Use the official Python image as a parent image
FROM python:3.8-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/

# Expose port 8080 for your Hug API
EXPOSE 8080

# Define the command to run your application, pointing to the new entry point
CMD ["python", "/app/app.py"]
