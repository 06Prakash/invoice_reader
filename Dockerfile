# Step 1: Build the frontend
FROM node:14 AS build-frontend
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

# Install necessary packages for PDF processing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils

# Copy the rest of the backend code into the container
COPY backend /app

# Copy the frontend build artifacts from the previous stage
COPY --from=build-frontend /frontend/build /app/static

# Expose the port the app runs on
EXPOSE 5000

# Run the application
CMD ["python", "invoice_reader_app.py"]
