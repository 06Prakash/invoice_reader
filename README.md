# Invoice Reader Application

## Overview

The Invoice Reader Application is a powerful tool designed to extract and process data from invoice PDFs. It utilizes modern web technologies and machine learning techniques to automate the extraction process, making it efficient and reliable.

## Features

- **User Authentication**: Secure login and registration functionality with JWT-based authentication.
- **Template Management**: Create, save, and manage extraction templates specific to your company's needs.
- **PDF Upload and Extraction**: Upload PDF files and extract data based on predefined templates.
- **Progress Tracking**: Monitor the extraction progress in real-time.
- **Data Download**: Download the extracted data in JSON, CSV, or text formats.

## Tech Stack

- **Backend**: Flask, SQLAlchemy, Flask-JWT-Extended, PostgreSQL
- **Frontend**: React, Axios, Material-UI
- **Containerization**: Docker, Docker Compose

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### Installation

1. **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd invoice_reader
    ```

2. **Set up environment variables**:
    Create a `.env` file in the root directory and add the following variables:
    ```plaintext
    FLASK_ENV=development
    DATABASE_URI=postgresql://<db_user>:<db_password>@db/invoice_extractor
    SECRET_KEY=<your_secret_key>
    JWT_SECRET_KEY=<your_jwt_secret_key>
    POSTGRES_USER=<db_user>
    POSTGRES_PASSWORD=<db_password>
    POSTGRES_DB=invoice_extractor
    ```

3. **Build and run the application using Docker Compose**:
    ```bash
    docker-compose up --build
    ```

    This command will build the Docker images, set up the containers, and start the application.

### Usage

1. **Access the application**:
    Open your web browser and navigate to `http://localhost:5001`.

2. **Register and login**:
    - Register a new user with your company name.
    - Login with the registered credentials.

3. **Template Management**:
    - Create a new template by specifying the template name and field details.
    - Save the template to make it available for data extraction.

4. **Upload and Extract**:
    - Upload PDF files for extraction.
    - Select the desired template and initiate the extraction process.
    - Monitor the extraction progress and download the results in the preferred format.

## Folder Structure

```plaintext
invoice_reader/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── extensions.py
│   ├── init_db.py
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── routes.py
│   │   ├── template.py
│   │   ├── extract.py
│   │   └── user_routes.py
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── App.js
│   │   ├── index.js
│   │   └── ...
│   └── package.json
├── resources/
│   ├── json_templates/
│   │   └── default_template.json
│   └── ...
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh
└── README.md

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

- **POST /extract**: Upload PDFs and extract data.
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




