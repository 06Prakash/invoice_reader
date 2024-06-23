# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install Tesseract OCR and Poppler
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    poppler-utils

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run invoice_reader_app.py when the container launches
CMD ["python", "invoice_reader_app.py"]
