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
# Database initialization steps:
# 1. Initialize DB schema (creates base tables from SQLAlchemy models)
# 2. Check alembic current - if no version, stamp head to skip migrations for existing schema
# 3. Run Alembic upgrade (will be no-op if already at head)
# 4. Start gunicorn server
CMD ["sh", "-c", "echo 'Initializing database schema...' && python init_db_schema.py && echo 'Checking Alembic version...' && (alembic current 2>&1 | grep -q head && echo 'Already at head' || (echo 'No version found, stamping head...' && alembic stamp head)) && echo 'Running Alembic migrations...' && alembic upgrade head && echo 'Starting gunicorn on port $PORT...' && gunicorn main:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120"]
