# NIRA: Transforming PDFs with Cutting-Edge AI

## Overview

NIRA is a sophisticated AI-powered application designed to extract and process data from various types of documents, including invoices, handwritten text, printed receipts, and more. By integrating both custom and prebuilt AI models, NIRA enables flexible and efficient document data extraction methods tailored to user needs.

## Features

- **AI-Powered Extraction Methods**: Supports multiple extraction methods:
  - NIRA Standard Extraction
  - NIRA AI - Handwritten (Custom) Extraction
  - NIRA AI - Invoice (PB) Extraction
  - NIRA AI - Printed Text (PB) Extraction
  - NIRA AI - Printed Business Card (PB) Extraction
  - NIRA AI - Printed Receipt (PB) Extraction
- **User Authentication**: Secure login and registration functionality with JWT-based authentication.
- **Template Management**: Create, save, and manage extraction templates specific to various use cases.
- **Document Upload and Extraction**: Upload files and extract data using predefined templates and AI models.
- **Progress Tracking**: Monitor the extraction progress in real-time.
- **Data Export**: Download the extracted data in JSON, CSV, or text formats.

## Tech Stack

- **Backend**: Flask, SQLAlchemy, Flask-JWT-Extended, PostgreSQL
- **Frontend**: React, Axios, Material-UI
- **AI Models**: Custom and prebuilt models integrated via Azure
- **Containerization**: Docker, Docker Compose

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/06Prakash/invoice_reader.git
    cd invoice_reader
    ```

2. **Set up environment variables**:
    Create a `.env` file in the root directory and add the following variables:
    ```plaintext
    FLASK_ENV=development
    DATABASE_URI=postgresql://<db_user>:<db_password>@db/nira_db
    SECRET_KEY=<your_secret_key>
    JWT_SECRET_KEY=<your_jwt_secret_key>
    POSTGRES_USER=<db_user>
    POSTGRES_PASSWORD=<db_password>
    POSTGRES_DB=nira_db
    AZURE_CLIENT_ID=<azure_client_id>
    AZURE_TENANT_ID=<azure_tenant_id>
    AZURE_CLIENT_SECRET=<azure_client_secret>
    KEY_VAULT_URL=<key_vault_url>
    ```

3. **Start the database**:
    ```bash
    docker-compose -f .\docker-compose-db.yml up --build
    ```

4. **Start the application**:
    ```bash
    docker-compose up --build
    ```

    These commands will build the Docker images, set up the containers, and start the application.

### Usage

1. **Access the application**:
    Open your web browser and navigate to `http://localhost:5001`.

2. **Register and login**:
    - Register a new user.
    - Login with the registered credentials.

3. **Select Extraction Method**:
    - Choose one of the AI-powered extraction methods from the dropdown menu.

4. **Upload and Extract**:
    - Upload documents for extraction.
    - Monitor the extraction progress and download the results in the desired format.

## Folder Structure

### Backend
```plaintext
backend/
├── app.py
├── config.py
├── extensions.py
├── init_db.py
├── modules/
│   ├── __init__.py
│   ├── extract.py
│   ├── extract_with_azure.py
│   ├── extraction.py
│   ├── models.py
│   ├── preprocessing.py
│   ├── routes.py
│   ├── serve.py
│   ├── template.py
│   ├── upload.py
│   ├── user_routes.py
│   ├── utils.py
│   ├── validation.py
│   └── template_pdf_generators/
│       ├── __init__.py
│       └── ...
├── templates/
├── uploads/
├── app-requirements.txt
├── base-requirements.txt
└── Dockerfile
```

### Frontend
```plaintext
frontend/
├── public/
│   ├── favicon.ico
│   ├── logo192.png
│   ├── logo512.png
├── src/
│   ├── assets/
│   ├── components/
│   │   ├── DataReview.js
│   │   ├── JsonTemplateGenerator.js
│   │   ├── LoginComponent.js
│   │   ├── NavBar.js
│   │   ├── OriginalLinesDisplay.js
│   │   ├── RegisterComponent.js
│   │   ├── TemplateEditor.js
│   │   ├── TemplateManager.js
│   │   ├── UploadComponent.js
│   ├── styles/
│   │   ├── DataReview.css
│   │   ├── JsonTemplateGenerator.css
│   │   ├── LoginComponent.css
│   │   ├── NavBar.css
│   │   ├── RegisterComponent.css
│   │   ├── TemplateEditor.css
│   │   ├── TemplateManager.css
│   │   ├── UploadComponent.css
│   ├── App.js
│   ├── App.test.js
│   ├── index.css
│   └── index.js
├── package.json
```

## API Endpoints

### Authentication

- **POST /user/register**: Register a new user.
- **POST /user/login**: Login and retrieve a JWT token.

### Templates

- **POST /templates**: Create or update a template.
- **GET /templates**: Retrieve the list of templates.
- **GET /templates/<name>**: Retrieve a specific template by name.
- **GET /default_template**: Retrieve the default template.

### Extraction

- **POST /extract**: Upload documents and extract data.
- **GET /progress**: Get the progress of the current extraction process.

## Troubleshooting

- Ensure all environment variables are correctly set in the `.env` file.
- Verify that Docker and Docker Compose are properly installed and running.
- Check the logs for any errors during the build or runtime:
    ```bash
    docker-compose logs
    ```

## Contributing

We welcome contributions! Please fork the repository and submit a pull request with your changes.

