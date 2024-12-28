# Step 1: Build the frontend
FROM node:18-alpine AS build-frontend
WORKDIR /frontend

# Increase Node.js memory limit
ENV NODE_OPTIONS="--max-old-space-size=4096"

# Copy package.json and package-lock.json for dependency resolution
COPY frontend/package*.json ./

# Install frontend dependencies with no optional packages
RUN npm install --omit=optional

# Copy the rest of the frontend code and build it
COPY frontend/ .
RUN npm run build

# Step 2: Build the backend and create the final image
FROM python:3.9-slim
WORKDIR /app

# Install app-specific dependencies first
COPY backend/app-requirements.txt .
RUN pip install --no-cache-dir -r app-requirements.txt

# Install base dependencies
COPY backend/base-requirements.txt .
RUN pip install --no-cache-dir -r base-requirements.txt

# We don't need this if we have Azure
# Create EasyOCR model directory and download models during build
# RUN mkdir -p /root/.EasyOCR/model && \
# python -c "import easyocr; easyocr.Reader(['en'], model_storage_directory='/root/.EasyOCR', download_enabled=True)"

# Verify if models are downloaded correctly
# RUN ls -lh /root/.EasyOCR/model  # This should list the downloaded models

# Install necessary packages for PDF processing, OpenCV, and PostgreSQL client (psql)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    libgl1-mesa-glx \
    postgresql-client \
    dos2unix \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the backend code into the container
COPY backend /app

# Copy the frontend build artifacts from the previous stage
COPY --from=build-frontend /frontend/build /app/static

# Copy the entrypoint script
COPY entrypoint.sh /app/entrypoint.sh

RUN dos2unix /app/entrypoint.sh

# Create the logs directory
RUN mkdir -p /app/logs

# Make entrypoint.sh executable
RUN chmod +x /app/entrypoint.sh

# Expose the port the app runs on
EXPOSE 5000

# Set the entrypoint to the script
ENTRYPOINT ["python", "app.py"]
