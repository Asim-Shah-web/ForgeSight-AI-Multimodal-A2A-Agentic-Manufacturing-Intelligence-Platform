"""Manufacturing quality tools for MCP."""


def get_quality_incidents(line_id: str):
    return {"line_id": line_id, "recent_incidents": 2}
