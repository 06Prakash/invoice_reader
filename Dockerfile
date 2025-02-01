# ==================================
# Step 1: Build the frontend
# ==================================
FROM node:18-alpine AS build-frontend
WORKDIR /frontend

# Increase Node.js memory limit for large builds
ENV NODE_OPTIONS="--max-old-space-size=4096"

# Install dependencies separately for better caching
COPY frontend/package*.json ./
RUN npm install --omit=optional

# Copy the frontend code and build it
COPY frontend/ .
RUN npm run build

# ==================================
# Step 2: Backend Base Setup
# ==================================
FROM python:3.9-slim AS base
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    libgl1-mesa-glx \
    postgresql-client \
    dos2unix \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/app-requirements.txt .
RUN pip install --no-cache-dir -r app-requirements.txt

# Copy backend code
COPY backend /app

# Copy frontend build artifacts into backend for production
COPY --from=build-frontend /frontend/build /app/static

# Copy the entrypoint script and ensure it's executable
COPY entrypoint.sh /app/entrypoint.sh
RUN dos2unix /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Create logs directory
RUN mkdir -p /app/logs

# ==================================
# Step 3: Development Mode
# ==================================
FROM base AS dev
ENV FLASK_ENV=development
ENV FLASK_DEBUG=1
ENV DEBUG=True

# Mount backend code as a volume for live reload
VOLUME ["/app"]

# Expose Flask's development port
EXPOSE 5000

# Run Flask in development mode with auto-reload
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000", "--reload"]

# ==================================
# Step 4: Production Mode
# ==================================
FROM base AS prod
EXPOSE 80

# Run Gunicorn with optimized thread settings for better performance
CMD ["gunicorn", "-w", "4", "-k", "gthread", "--threads", "4", "-b", "0.0.0.0:80", "app:app"]

# ==================================
# Step 5: Celery Worker
# ==================================
FROM base AS celery_worker
ENV C_FORCE_ROOT=true
CMD ["celery", "-A", "celery_worker.celery_app", "worker", "--loglevel=info"]
