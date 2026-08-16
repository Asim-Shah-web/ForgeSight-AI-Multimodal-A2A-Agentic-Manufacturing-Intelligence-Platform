# 03 — Agent Cards

## Agent Identity
An Agent Card is a JSON manifest served at `/.well-known/agent-card.json` or `/a2a/card`.

```json
{
  "name": "Vision Agent",
  "description": "Analyzes manufacturing PCB images for visual defects.",
  "version": "1.0.0",
  "skills": [
    {
      "id": "inspect_pcb",
      "name": "Inspect PCB Image",
      "description": "Detects solder bridges, missing components, and alignment issues."
    }
  ]
}
```
