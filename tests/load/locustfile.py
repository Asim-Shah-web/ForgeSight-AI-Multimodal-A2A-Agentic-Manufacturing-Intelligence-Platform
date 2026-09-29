"""
Basic smoke/load test simulating a Quality Engineer's read-heavy usage
pattern. Manual/on-demand only — not part of CI (see tests/load/README.md).

Usage:
    locust -f tests/load/locustfile.py --host http://localhost:8000
"""

from __future__ import annotations

from locust import HttpUser, between, task


class QualityEngineerUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self) -> None:
        response = self.client.post(
            "/api/v1/auth/token",
            data={"username": "qe1", "password": "ForgeSight!Test123"},
        )
        token = response.json().get("access_token", "")
        self.client.headers.update({"Authorization": f"Bearer {token}"})

    @task(3)
    def list_incidents(self) -> None:
        self.client.get("/api/v1/incidents")

    @task(2)
    def get_incident_detail(self) -> None:
        self.client.get("/api/v1/incidents/INCIDENT-2026-00421")

    @task(1)
    def search_documents(self) -> None:
        self.client.get("/api/v1/documents/search", params={"query": "placement tolerance C17"})