# Use the specified base image
FROM mcr.microsoft.com/devcontainers/python:1-3.11-bullseye

# other system libraries
RUN apt-get update \
    && apt-get install -y graphviz graphviz-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements.txt into the image
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code (optional, if needed)
# COPY . .

# Command to run the application (optional, if needed)
# CMD ["python", "app.py"]