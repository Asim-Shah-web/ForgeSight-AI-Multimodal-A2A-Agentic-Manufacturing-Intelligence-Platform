"""Manufacturing maintenance tools for MCP."""


def get_machine_history(machine_id: str):
    return {
        "machine_id": machine_id,
        "last_serviced": "2026-08-01",
        "health_score": 92.5,
    }
