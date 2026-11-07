# Stage 1: Build Desktop HUD UI
FROM node:22-alpine AS frontend-builder
WORKDIR /app/apps/desktop-ui
COPY apps/desktop-ui/package*.json ./
RUN npm ci
COPY apps/desktop-ui ./
RUN npm run build

# Stage 2: Python Engine Runtime
FROM python:3.11-slim AS runtime
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/backend

# Install runtime utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements.txt

# Copy source code and built frontend
COPY backend ./backend
COPY aegis.py pyproject.toml ./
COPY --from=frontend-builder /app/apps/desktop-ui/dist ./apps/desktop-ui/dist

# Expose Aegis HTTP & WebSocket port
EXPOSE 8420

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8420/api/system/diagnostics || exit 1

# Start the core engine daemon
CMD ["python", "-m", "uvicorn", "aegis_core.main:app", "--host", "0.0.0.0", "--port", "8420"]
