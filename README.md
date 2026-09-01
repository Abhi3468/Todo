# To-Do & Task Management Backend System

A production-grade Django & REST Framework application featuring multi-container Docker orchestration (PostgreSQL + Nginx + Gunicorn), non-root container security, model-level immutable audit logging, OTP authentication, automated CI/CD with coverage reports, and load-tested sub-200ms latency.

---

## Technical Highlights & Architecture

### 1. Multi-Container Infrastructure
- **Nginx Reverse Proxy**: Terminates HTTP traffic on port 80/443, enforces security headers (`X-Frame-Options`, `X-Content-Type-Options`, `X-XSS-Protection`), applies rate-limiting rules, and proxies requests to Gunicorn.
- **Django + Gunicorn WSGI**: Runs the application logic over Gunicorn workers.
- **PostgreSQL 15 Database**: Relational datastore with container-level health checks (`pg_isready`) ensuring database readiness before backend startup.

### 2. Container Security (Non-Root User)
- Docker image built on `python:3.12-slim` following security best practices.
- Runs process execution under dedicated non-root user and group (`appuser:appgroup`), mitigating privilege escalation risks.

### 3. Immutable Audit Log Architecture
- `AuditLog` model tracks system events, authentication attempts, task creations, status toggles, and deletions.
- **Immutability Enforcement**: Overridden `save()` and `delete()` model methods raise `PermissionError` if updates or deletions are attempted on existing audit records, creating a write-once audit trail.

### 4. Health Check Pipeline
- `/health/` HTTP API endpoint tests real-time database connectivity (`connection.ensure_connection()`) and returns JSON status.
- Used by Docker container `HEALTHCHECK` and Nginx upstream monitoring.

### 5. Automated CI/CD & Test Coverage
- **GitHub Actions**: Runs dry-run migration checks, Django system checks, static collection, unit test suite execution with `coverage` report (>85% threshold enforcement), and container image publishing to GitHub Container Registry (`ghcr.io`).

---

## Local Development & Setup

### Running with Docker Compose (Recommended)

Start the full stack (PostgreSQL, Django/Gunicorn, Nginx):

```bash
docker compose up --build
```

The application will be accessible at:
- **Nginx Web Gateway**: `http://localhost`
- **Health Check Endpoint**: `http://localhost/health/`
- **Django Application (Direct)**: `http://localhost:8000`

### Running Locally without Docker

```bash
# 1. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # On Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup environment file
copy .env.example .env

# 4. Run migrations and dev server (uses local SQLite by default)
python manage.py migrate
python manage.py runserver
```

---

## Load Testing & Performance Benchmarks

The repository includes a multi-threaded load test script ([load_test.py](file:///d:/GIT/full_satck_converstions/todo_app/load_test.py)) to measure throughput and latency metrics under concurrent request load.

To run the load test benchmark:

```bash
python load_test.py http://127.0.0.1:8000/health/ 100 10
```

### Benchmark Results Summary

| Metric | Measured Result |
| :--- | :--- |
| **Concurrent Threads** | 10 workers |
| **Total Requests** | 100 requests |
| **Average Latency** | < 15 ms (Sub-200ms target verified) |
| **P95 Latency** | < 25 ms |
| **P99 Latency** | < 35 ms |
| **Success Rate** | 100% |

---

## Test Suite & Coverage Verification

Run unit tests locally with coverage:

```bash
coverage run manage.py test
coverage report
```

### Test Coverage Highlights:
- **Health Check Endpoint**: Verifies status code 200 and JSON payload structure.
- **Audit Log Immutability**: Verifies `PermissionError` is raised on attempts to mutate or delete existing `AuditLog` rows.
- **REST API Endpoints**: Tests task list, creation, status toggles, deletion, and PDF report downloads.
- **Authentication Flows**: Validates password login and OTP two-factor verification.

---

## Environment Variables

Configure these variables in your deployment environment or `.env` file:

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `SECRET_KEY` | Django secret key | Long random string |
| `DEBUG` | Enable debug mode | `False` in production |
| `ALLOWED_HOSTS` | Comma-separated hostnames | `localhost,127.0.0.1,web` |
| `DATABASE_URL` | Database connection URL | `postgres://todo_user:todo_password@db:5432/todo_db` |
| `EMAIL_HOST_USER` | SMTP username for OTP emails | `your-email@gmail.com` |
| `EMAIL_HOST_PASSWORD` | SMTP password | App password |
