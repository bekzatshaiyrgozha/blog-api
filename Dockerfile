FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies (gettext for translations, build tools)
RUN apt-get update && apt-get install -y \
    gettext \
    netcat-openbsd \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy requirements
COPY requirements/base.txt requirements/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements/base.txt

# Copy entrypoint script outside /app so bind mount does not hide it
COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Copy project code
COPY --chown=appuser:appuser . /app/

USER appuser

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "settings.asgi:application"]