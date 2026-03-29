# Pay Buddy

**Pay Buddy** is a personal finance app designed to help users track their finances, especially when lending money to friends. The app allows you to record, manage, and monitor loans, repayments, and outstanding balances, making it easy to stay organized and maintain transparency in your personal transactions.

## Requirements

- Python 3.12
- PostgreSQL 16
- pip

## Running with Docker

1. Make sure you have Docker and Docker Compose installed.
2. Create a docker-compose.yaml file with the following format:
   ```yaml
   version: "3.9"

   services:
      rabbitmq:
         image: rabbitmq:3-management
         ports:
            - "5672:5672"
            - "15672:15672"
         env_file:
            - ./.env
         networks:
            - pay-first-network

      redis:
         image: redis:8.2.3
         container_name: redis
         ports:
            - "6379:6379"
         networks:
            - pay-first-network

      db:
         image: postgres:16
         env_file:
            - ./.env
         volumes:
            - postgres_data:/var/lib/postgresql/data
         ports:
            - "5432:5432"
         networks:
            - pay-first-network

      web:
         image: pay-first-web-app
         build: .
         # command: python -m debugpy --listen 0.0.0.0:5678 --wait-for-client manage.py runserver 0.0.0.0:8000 # For debugging with VSCode
         command: python manage.py runserver 0.0.0.0:8000
         volumes:
            - .:/app
         ports:
            - "8000:8000"
            - "5678:5678"
         depends_on:
            - db
         env_file:
            - ./.env
         networks:
            - pay-first-network

      worker:
         build: .
         command: celery -A root worker -l info --concurrency=4
         volumes:
            - .:/app
         depends_on:
            - rabbitmq
            - redis
         networks:
            - pay-first-network

      celery-beat:
         build: .
         command: celery -A root beat -l info
         volumes:
         - .:/app
         ports:
         - "5681:5681"
         depends_on:
         - rabbitmq
         - redis
         networks:
         - pay-first-network

      tests:
         build: .
         command: python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m pytest -v
         volumes:
            - .:/app
         ports:
            - "5679:5678"
         restart: always
         depends_on:
            - db
         env_file:
            - ./.env
         networks:
            - pay-first-network

   volumes:
      postgres_data:
   networks:
      pay-first-network:
   ```
3. Create a `.env` file similar to `.env.example`
4. Start the app with:

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