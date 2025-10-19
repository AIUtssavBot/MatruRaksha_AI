### Note: Frontend dist is prebuilt locally - we skip the build stage and copy dist directly

### Stage 2: Install backend dependencies
FROM python:3.11-slim AS backend-build
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build dependencies for wheels
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev build-essential curl ca-certificates && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r /app/requirements.txt

# Copy backend source
COPY backend/ /app/

### Stage 3: Final image with nginx + supervisord + app
FROM python:3.11-slim
WORKDIR /app

# Install runtime packages: nginx and supervisor
RUN apt-get update && apt-get install -y --no-install-recommends nginx supervisor curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy backend from build stage
COPY --from=backend-build /app /app

# Copy installed Python runtime and console scripts from backend-build
# (this brings site-packages and scripts like uvicorn into the final image)
COPY --from=backend-build /usr/local /usr/local

# Copy prebuilt frontend dist
COPY frontend/dist /usr/share/nginx/html

# Copy configs
COPY infra/nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY infra/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose HTTP
EXPOSE 80

# (run as root in container so supervisord can start nginx and bind to privileged ports)

# Start supervisord which will run nginx and uvicorn
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
