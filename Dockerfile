# Step 1: Build the frontend
FROM node:18 AS build-frontend
WORKDIR /frontend

# Copy package.json and package-lock.json for dependency resolution
COPY frontend/package*.json ./

# Install frontend dependencies
RUN npm install

# Copy the rest of the frontend code and build it
COPY frontend/ .
RUN npm run build

# Step 2: Build the backend and create the final image
FROM python:3.9-slim
WORKDIR /app

# Copy the backend requirements file and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

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

# Copy the default template to the appropriate location
COPY resources /app/resources

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
ENTRYPOINT ["/app/entrypoint.sh", "db", "python", "app.py"]