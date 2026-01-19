FROM docker.io/python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

ENV HF_HOME=/app/models
ENV TRANSFORMERS_CACHE=/app/models

EXPOSE 11435

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "11435"]
