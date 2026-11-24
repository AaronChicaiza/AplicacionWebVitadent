FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app/rasa
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc g++ libffi-dev libssl-dev && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir "rasa==3.6.21" "rasa-sdk==3.6.2" "requests>=2.32,<3"
COPY rasa/ /app/rasa/
EXPOSE 5005 5055
CMD ["rasa", "run", "--enable-api", "--credentials", "credentials.yml", "--endpoints", "endpoints.yml", "--port", "5005", "--host", "0.0.0.0"]
