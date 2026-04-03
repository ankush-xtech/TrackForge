FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

# Application code
COPY . .

# Expose port
EXPOSE 8000

# Default command: run FastAPI with hot reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
