# Worker container image for background AegisCore tasks.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /srv/apps/worker

# Copy worker code and install its Python dependencies.
COPY apps/worker/pyproject.toml ./pyproject.toml
COPY apps/worker/app ./app

RUN pip install --upgrade pip && pip install .[dev]

CMD ["python", "-m", "app.main"]
