# FastAPI REST API Overview

## Endpoints

- `GET /health`: Service health status.
- `POST /incidents`: Create a new quality incident.
- `GET /incidents/{id}`: Retrieve incident details.
- `POST /incidents/{id}/investigate`: Trigger agent investigation workflow.
- `GET /agents`: List available A2A agents and Agent Cards.
- `POST /chat`: Operator interactive query endpoint.
