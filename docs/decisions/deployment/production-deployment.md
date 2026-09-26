# ForgeSight AI — Production Deployment

## Prerequisites

- Docker + Docker Compose v2
- A domain with TLS termination in front of this stack (Traefik, Caddy, or
  a cloud load balancer). **This document does not configure TLS** — that
  is expected to sit in front of the `app` (port 8000) and `frontend`
  (port 3000) services, terminating HTTPS and forwarding plain HTTP inward.
- A real Groq API key.
- The fixture CV checkpoint at `models/vision/checkpoints/yolov8-forgesight-synthetic-v1.pt`
  (or your own real-dataset checkpoint at the path you configure in
  `config/vision/vision.yaml`).

## Deploy

```bash
git clone <repo-url> && cd ForgeSight-AI-...
cp .env.production.example .env.production
# Edit .env.production: fill in all REPLACE_WITH_* values.

docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d db redis
# Wait for both to report healthy: docker compose -f docker-compose.prod.yml ps

# Run migrations once, against the now-running production DB:
docker compose -f docker-compose.prod.yml run --rm app alembic upgrade head

docker compose -f docker-compose.prod.yml up -d
```

## Seeding (staging/demo environments ONLY)

`scripts/seed_database.py` inserts synthetic demonstration data
(`INCIDENT-2026-00421`, fixture users with a shared test password, etc.).

**Never run this against a real production dataset.** It is appropriate
only for a staging or demo environment where you want the app populated
with realistic-looking sample data for evaluation purposes:

```bash
docker compose -f docker-compose.prod.yml run --rm app python scripts/seed_database.py
```

## Rollback

Pin image tags rather than always building `latest`. Before deploying a new
version, tag and keep the currently-running image:

```bash
docker tag forgesight-app:latest forgesight-app:rollback-$(date +%Y%m%d)
```

If a new deployment misbehaves:

```bash
docker compose -f docker-compose.prod.yml down
# retag forgesight-app:rollback-YYYYMMDD back to forgesight-app:latest, or
# edit docker-compose.prod.yml's image reference to the rollback tag
docker compose -f docker-compose.prod.yml up -d
```

## What this stack does NOT include

- TLS termination — put a reverse proxy or load balancer in front.
- A production observability backend — set `TRACING_OTLP_ENDPOINT` in
  `.env.production` to your real OTLP collector; the dev-only `jaeger`
  service from `docker-compose.yml` is intentionally absent here.
- Automated backups of the Postgres volume — set these up separately using
  your infrastructure provider's standard tooling against the
  `forgesight_pgdata_prod` volume.