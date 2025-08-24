# Pay Buddy

**Pay Buddy** is a personal finance app designed to help users track their finances, especially when lending money to friends. The app allows you to record, manage, and monitor loans, repayments, and outstanding balances, making it easy to stay organized and maintain transparency in your personal transactions.

## Requirements

- Python 3.12
- PostgreSQL 16
- pip

## Running with Docker

1. Make sure you have Docker and Docker Compose installed.
2. Create an `entrypoint.sh` script in the project root with the necessary startup commands. Format for `entrypoint.sh` is as follows
    ```sh
    #!/bin/sh
    python manage.py runserver 0.0.0.0:8000
    ```
3. Start the app with:

   ```bash
   docker compose up --build
   ```

This will build the Docker images and launch the application.

## Running Locally (Without Docker)

1. Install Python 3.12 and PostgreSQL 16 on your system.
2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   ```
3. Activate Virtual Environment
   ```bash
   source venv/bin/activate
   ```
4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Set up your PostgreSQL database and update your environment variables or settings as needed.
6. Generate Migration files
   ```bash
   python manage.py makemigrations
   ```
7. Apply database migrations:

   ```bash
   python manage.py migrate
   ```

8. Start the development server:

   ```bash
   python manage.py runserver
   ```

The app will be available at `http://localhost:8000/`.