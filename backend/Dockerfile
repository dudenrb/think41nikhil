# backend/Dockerfile

# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for MongoDB client tools and others (optional but good practice)
# python-dev, build-essential are often needed for compiling certain Python packages
# curl is useful for health checks or debugging within the container
# libpq-dev for psycopg2 if you switch to PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the Python dependency files (requirements.txt) first
# This allows Docker to cache the layer if requirements don't change
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port that FastAPI will run on
EXPOSE 8000

# Command to run the application
# --host 0.0.0.0 makes the server accessible from outside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]