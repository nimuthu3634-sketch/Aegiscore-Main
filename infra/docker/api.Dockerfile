# API container image for the FastAPI backend.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /srv/apps/api

# Copy backend source code, migrations, tests, and startup script.
COPY apps/api/pyproject.toml ./pyproject.toml
COPY apps/api/alembic.ini ./alembic.ini
COPY apps/api/alembic ./alembic
COPY apps/api/app ./app
COPY apps/api/tests ./tests
COPY infra/docker/api-entrypoint.sh /usr/local/bin/api-entrypoint.sh

# Install backend dependencies and make the entrypoint executable.
RUN pip install --upgrade pip && pip install .[dev]
RUN chmod +x /usr/local/bin/api-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["api-entrypoint.sh"]
