# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y build-essential python3-dev libffi-dev

# Copy the requirements file from the project root and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all necessary source code directories
COPY ./api-gateway/app /app/api_gateway/app
COPY ./config /app/config
COPY ./libs /app/libs

# Add __init__.py files to make directories importable packages
RUN touch /app/__init__.py /app/api_gateway/__init__.py

# The command to run the agent as a module from the WORKDIR
CMD ["python", "-m", "api_gateway.app.main"] 