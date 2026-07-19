FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirement files and install
COPY pyproject.toml ./

# Install standard dependencies using pip since it doesn't have uv.lock
# However, if pip install . doesn't work, we'll install dependencies manually
RUN pip install --no-cache-dir aio-pika pydantic pydantic-settings redis

# Copy application code
COPY . .

# Run the worker
CMD ["python", "main.py"]
