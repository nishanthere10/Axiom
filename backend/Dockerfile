# Use a stable, slim Python 3.12 image to keep the container lightweight
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables to prevent Python from writing .pyc files
# and to ensure stdout/stderr are unbuffered (useful for logs)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies (e.g., for cryptography or other native extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port (Railway will provide a PORT environment variable, defaulting to 8000)
EXPOSE ${PORT:-8000}

# Command to run the application using uvicorn
# We use the PORT environment variable injected by Railway
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
