# Fraud Rule Engine Service (Flask)

## Features
- Ingest categorized transaction events
- Apply fraud rules + heuristics
- Store transactions + rule hits in PostgreSQL
- Retrieve results via REST API
- Simple GUI dashboard
- Prometheus metrics (/metrics)
- Docker + Compose + CI + Kubernetes manifests
- Tests with pytest

## Run with Docker Compose
```bash
cp .env.example .env
docker compose up --build -d