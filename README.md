# Pay Buddy

**Pay Buddy** is a personal finance app designed to help users track their finances, especially when lending money to friends. The app allows you to record, manage, and monitor loans, repayments, and outstanding balances, making it easy to stay organized and maintain transparency in your personal transactions.

## Requirements

- Python 3.12
- PostgreSQL 16
- pip

## Running with Docker

1. Make sure you have Docker and Docker Compose installed.
2. Create an `Dokcerfile` file in the project root with the necessary startup commands. Format for `Dockerfile` is as follows
   ```Dokckerfile
   FROM python:3.12-slim

   ENV PYTHONDONTWRITEBYTECODE=1
   ENV PYTHONUNBUFFERED=1

   WORKDIR /app

   COPY requirements.txt .
   COPY dev-requirements.txt .
   RUN pip install --upgrade pip
   RUN pip install -r requirements.txt
   RUN pip install -r dev-requirements.txt

   COPY . .

   CMD ["gunicorn", "myproject.wsgi:application", "--bind", "0.0.0.0:8000"]
   ```
4. Create a docker-compose.yaml file with the following format:
   ```yaml
   version: "3.9"

   services:
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
5. Create a `.env` file with the following format:
   ```
   SECRET_KEY = django-insecure-pvl*_ypzk)2bzhl77u2y$q801vus)+r6xik3+@f&frn3s-$^f
   ALLOWED_HOSTS=*
   DEBUG=1

   POSTGRES_DB=postgres
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=dbpassword
   DB_PORT=5432
   DB_HOST=db

   AUTH_TOKEN_EXPIRY_SECONDS=0
   AUTH_TOKEN_EXPIRY_MINUTES=0
   AUTH_TOKEN_EXPIRY_HOURS=0
   AUTH_TOKEN_EXPIRY_DAYS=0

   CORS_ALLOWED_ORIGINS=http://127.0.0.1:3000,http://localhost:3000
   CORS_ALLOW_ALL_ORIGINS=0

   EMAIL_HOST
   EMAIL_PORT
   EMAIL_HOST_USER
   EMAIL_HOST_PASSWORD
   DEFAULT_FROM_EMAIL

   RESET_PASSWORD_LINK_EXPIRY_SECONDS
   RESET_PASSWORD_URL

   EMAIL_VERIFICATION_URL

   REDIS_HOST=redis
   REDIS_PORT=6379
   REDIS_CACHE_DB=1
   ```
  
      Tip: you can copy the provided example file and update values:

      ```bash
      cp .env.example .env
      # then edit .env to set secure passwords / secrets
      ```
6. Start the app with:

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