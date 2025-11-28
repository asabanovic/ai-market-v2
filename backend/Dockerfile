FROM python:3.11-slim

# Install PostgreSQL client libraries for psycopg2
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=5000
ENV PYTHONUNBUFFERED=1

# Use shell form to ensure $PORT is expanded at runtime
CMD ["sh", "-c", "echo 'Running Alembic migrations...' && alembic upgrade head && echo 'Starting gunicorn on port $PORT...' && gunicorn main:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120"]
