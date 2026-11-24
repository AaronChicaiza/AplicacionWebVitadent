FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN DJANGO_DEBUG=False \
    DJANGO_SECRET_KEY=build-only-placeholder-not-used-at-runtime-0123456789 \
    POSTGRES_DB=build_only REDIS_URL=redis://127.0.0.1:6379/0 \
    python manage.py collectstatic --noinput
RUN addgroup --system app && adduser --system --ingroup app app \
    && chown -R app:app /app
USER app
EXPOSE 8000
CMD ["gunicorn", "vitadent.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60"]
