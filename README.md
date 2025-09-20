# Boarding House Management System

This project is a web application for managing a multi-tenant boarding house system. It features a Python FastAPI backend and a Next.js frontend.

## Features

- **Multi-Tenancy:** The system is designed to support multiple, separate boarding houses using a realm-based system (`user@realm`).
- **User Roles:**
    - **Managers:** Can manage rooms, onboard new renters, create contracts, and approve payments.
    - **Renters:** Can view their contract, see their payment history, and upload proof of payment.
- **Secure Passwords:** Passwords are stored using SHA-256 hashing with a `{crypt-sha256}` header, compatible with FreeRADIUS.
- **Backend:** Built with FastAPI, using raw SQL queries with `asyncpg` to connect to a PostgreSQL database.
- **Frontend:** Built with Next.js and configured for static export.

## Project Structure

- `/app`: Contains the FastAPI backend source code.
  - `/app/api`: API routers for different resources.
  - `/app/sql`: Raw SQL queries.
  - `/app/auth`: Authentication logic.
- `/frontend`: Contains the Next.js frontend source code.
- `/uploads`: Directory where proof-of-payment images will be stored.
- `boarding_house_schema_extension.sql`: SQL script to extend a standard FreeRADIUS database schema with the necessary tables for this application.
- `requirements.txt`: Python dependencies.

## Setup and Installation

### 1. Database Setup

1.  This application extends a standard FreeRADIUS PostgreSQL database schema. Ensure you have a working FreeRADIUS setup with a PostgreSQL backend.
2.  Connect to your `radius` database.
3.  Execute the `boarding_house_schema_extension.sql` script to create the necessary tables (`rooms`, `contracts`, `payments`).

### 2. Backend Setup

1.  **Environment Variables:** The backend requires database credentials and a JWT secret. You can set these in your environment or create a `.env` file in the root directory.
    ```
    DB_USER=your_postgres_user
    DB_PASSWORD=your_postgres_password
    DB_NAME=radius
    DB_HOST=localhost
    DB_PORT=5432
    JWT_SECRET_KEY=your_super_secret_key
    JWT_ALGORITHM=HS256
    JWT_EXPIRE_MINUTES=30
    ```
2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### 3. Frontend Setup & Build

**IMPORTANT:** The agent environment had trouble executing the frontend build script. Please run these steps manually.

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```
2.  **Install Dependencies:**
    ```bash
    npm install
    ```
3.  **Build the application:**
    ```bash
    npm run build
    ```
    This will create the static assets in the `frontend/out` directory.

## Running the Application

1.  **Start the Backend Server:** From the root directory, run:
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000
    ```
2.  **Access the Application:** Open your web browser and navigate to `http://localhost:8000`. The FastAPI backend will serve the frontend application.

## First Use

1.  You will need to manually create a manager user in your database to get started. You can use the following Python snippet to generate a password hash.
    ```python
    import hashlib
    password = 'your_strong_password'
    h = hashlib.sha256()
    h.update(password.encode('utf-8'))
    hashed_password = h.hexdigest()
    print(f"{{crypt-sha256}}{hashed_password}")
    ```
2.  Use the generated hash to create the manager user in your database:
    ```sql
    -- Example: Create a manager for 'myhouse.com' realm
    INSERT INTO radcheck (username, attribute, op, value) VALUES ('manager@myhouse.com', 'Password-With-Header', ':=', '{crypt-sha256}PASTE_YOUR_HASH_HERE');
    INSERT INTO radusergroup (username, groupname, priority) VALUES ('manager@myhouse.com', 'boarding_managers', 1);
    ```
3.  Log in with the manager credentials (using the plain text password).
4.  You can now use the UI to create rooms and onboard new renters. The application will handle hashing their passwords automatically.
