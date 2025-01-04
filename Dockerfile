# Step 1: Build the frontend
FROM node:18-alpine AS build-frontend
WORKDIR /frontend

# Increase Node.js memory limit
ENV NODE_OPTIONS="--max-old-space-size=4096"

# Copy package.json and package-lock.json for dependency resolution
COPY frontend/package*.json ./

# Install frontend dependencies with no optional packages
RUN npm install --omit=optional

# Expose the React development server port
EXPOSE 3000

# Copy the rest of the frontend code and build it
COPY frontend/ .
RUN npm run build

# Step 2: Backend and runtime setup
FROM python:3.9-slim
WORKDIR /app

# Install app-specific dependencies first
COPY backend/app-requirements.txt .
RUN pip install --no-cache-dir -r app-requirements.txt

# Install base dependencies
COPY backend/base-requirements.txt .
RUN pip install --no-cache-dir -r base-requirements.txt

# Install additional tools and libraries
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libgl1-mesa-glx \
    postgresql-client \
    dos2unix \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the backend code into the container
COPY backend /app

# Copy the frontend build artifacts from the previous stage
COPY --from=build-frontend /frontend/build /app/static

# Copy the entrypoint script
COPY entrypoint.sh /app/entrypoint.sh

# Convert entrypoint to Unix format
RUN dos2unix /app/entrypoint.sh

# Create the logs directory
RUN mkdir -p /app/logs

# Make entrypoint.sh executable
RUN chmod +x /app/entrypoint.sh

# Expose the port the app runs on
EXPOSE 5000

# Set the entrypoint to the script
ENTRYPOINT ["python", "app.py"]
