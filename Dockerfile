# ---------- Stage 1: builder ----------
# Compilers and pip caches live here and never reach the final image.
FROM python:3.12-slim AS builder

WORKDIR /app

# Build the dependencies into their own virtualenv so we can copy just
# that folder into the runtime stage.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy ONLY the requirements first. Docker caches this layer, so editing
# app.py later does not re-install every dependency.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# ---------- Stage 2: runtime ----------
FROM python:3.12-slim AS runtime

# Never run as root inside a container.
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_VERSION=0.1.0

COPY --chown=appuser:appuser app.py .

USER appuser
EXPOSE 8000

# Docker polls this so `docker ps` can say healthy / unhealthy.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status==200 else 1)"

# gunicorn is a real production server. `flask run` is not.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "app:app"]
