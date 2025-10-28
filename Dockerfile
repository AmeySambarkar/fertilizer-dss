FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (for psycopg2, postgis/gdal)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the *new* requirements file
COPY requirements_updated.txt .

# Install packages
RUN pip install --no-cache-dir -r requirements_updated.txt

# Copy the rest of the application code
COPY . .

EXPOSE 8000

# Default command is in docker-compose.yml
CMD ["uvicorn", "backend_app:app", "--host", "0.0.0.0", "--port", "8000"]
