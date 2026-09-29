# Load/Smoke Testing

Manual, on-demand only — not run in CI, since a CI runner's limited
resources produce numbers that don't represent real capacity.

## Run

```bash
pip install locust
# Ensure the app + seeded data are running first (docker compose up -d, seeder run).
locust -f tests/load/locustfile.py --host http://localhost:8000
```

Open http://localhost:8089, set concurrent users/spawn rate, start the run.
Watch for response time degradation and error rates, particularly on
`/documents/search` (embedding + rerank inference happens on every call —
the most compute-heavy read path in this system).