Fraud Rule Engine Service

A production-ready Fraud Rule Engine Service that ingests transaction events, evaluates them against configurable fraud rules, assigns a fraud score, and exposes results via a REST API.

The service supports Docker Compose, Kubernetes, Prometheus monitoring, CI via GitHub Actions, and automated testing with pytest.

Features

Ingest categorized transaction events via REST API
Rule-based fraud detection (amount, country, channel, etc.)
Configurable fraud score threshold
PostgreSQL for persistence (SQLite for tests)
Prometheus metrics endpoint
Docker & Docker Compose support
Kubernetes manifests (namespace, deployment, service)
CI pipeline using GitHub Actions
Code quality enforced with Ruff
Unit & integration tests with pytest + coverage



Architecture Overview
┌─────────────┐
│  API Client │
└──────┬──────┘
       │
┌──────▼───────────────────────┐
│  Flask API (fraud-api)        │
│  - Validation                 │
│  - Rule Engine                │
│  - Fraud Scoring              │
└──────┬───────────────────────┘
       │
┌──────▼──────────┐     ┌──────────────────┐
│ PostgreSQL DB   │     │ Prometheus        │
│ (fraud-db)      │     │ /metrics endpoint │
└─────────────────┘     └──────────────────┘


Tech Stack

Language: Python 3.11
Framework: Flask
Database: PostgreSQL (prod), SQLite (tests)
ORM: SQLAlchemy
Containerization: Docker, Docker Compose
Orchestration: Kubernetes
Monitoring: Prometheus
CI: GitHub Actions
Testing: pytest, pytest-cov




Configuration

Copy the environment file:

cp .env.example .env

Key environment variables:

Variable	Description
DATABASE_URL	PostgreSQL connection string
FRAUD_SCORE_THRESHOLD	Score required to flag a transaction
TESTING	Enables SQLite in-memory DB for tests




Running with Docker Compose
docker compose up --build

Services:

API → http://localhost:8001

PostgreSQL → localhost:5432

Prometheus → http://localhost:9090




API Usage
Health Check
GET /health

Response:

{ "status": "ok" }
Ingest Transaction
POST /api/v1/transactions
Content-Type: application/json

Example payload:

{
  "id": "tx_001",
  "customer_id": "c_001",
  "category": "CARD",
  "amount": 12000.00,
  "currency": "ZAR",
  "merchant": "Some Shop",
  "country": "NG",
  "channel": "WEB",
  "event_time": "2026-02-07T10:00:00+02:00"
}

Response:

{
  "transaction_id": "tx_001",
  "fraud_score": 85,
  "is_flagged": true,
  "hits": [
    {
      "rule_code": "AMT_10K",
      "rule_name": "Amount >= 10000",
      "score": 50,
      "reason": "Amount 12000 >= 10000"
    }
  ]
}





Monitoring (Prometheus)

Metrics endpoint:

GET /metrics

Configured in monitoring/prometheus.yml.




Running Tests
Local
pip install -r requirements.txt
export TESTING=1
python -m pytest -q --cov=app --cov-report=term-missing
Windows (PowerShell)
$env:TESTING="1"
python -m pytest -q --cov=app --cov-report=term-missing




Code Quality

Run lint checks:

ruff check .



CI Pipeline

GitHub Actions pipeline runs on every push:

 -Ruff linting
 -pytest with coverage
 -Fails build on errors

Defined in:
.github/workflows/ci.yml



Kubernetes Deployment
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/

Check pods:
kubectl get pods -n fraud
