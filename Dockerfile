# Use Python 3.11 as base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV REDIS_HOST=localhost
ENV REDIS_PORT=6379

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy uv configuration files
COPY pyproject.toml uv.lock README.md ./

# Install dependencies using uv
RUN uv sync --frozen

# Copy the entire project
COPY . .

# Change to example directory
WORKDIR /app/example

# Collect static files
RUN uv run python manage.py collectstatic --noinput

# Apply database migrations
RUN uv run python manage.py migrate

# Expose port
EXPOSE 8000
