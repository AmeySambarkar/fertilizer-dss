FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential libpq-dev gdal-bin libgdal-dev && rm -rf /var/lib/apt/lists/*
COPY requirements_updated.txt .
RUN pip install --no-cache-dir -r requirements_updated.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "backend_app:app", "--host", "0.0.0.0", "--port", "8000"]
