# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file from the project root and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all necessary source code directories
COPY ./agents /app/agents
COPY ./config /app/config
COPY ./libs /app/libs

# Add __init__.py to make 'agents' an importable package
RUN touch /app/agents/__init__.py

# The command to run the agent as a module from the WORKDIR
CMD ["python", "-m", "agents.query_planner_agent.agent"] 