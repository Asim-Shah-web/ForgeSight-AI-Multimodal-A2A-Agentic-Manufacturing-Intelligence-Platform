# Learning Note: Human Personas vs. AI Agents

## 1. Concept Overview

In industrial software engineering and multi-agent systems design, it is vital to distinguish between a **Human Organizational Persona** and an **AI Agent Software Component**.

```text
+------------------------------------+       +------------------------------------+
|       HUMAN PERSONA (ROLE)         |       |         AI AGENT (SOFTWARE)        |
+------------------------------------+       +------------------------------------+
| - Real employee (e.g. Quality Eng) |       | - Autonomous software capability   |
| - Accountable for factory decisions|       | - Executes specific task logic     |
| - Holds legal & ISO sign-off authority     | - Uses tools (RAG, MCP, CV)        |
| - Interacts via UI Workspaces      |       | - Communicates via A2A or APIs     |
+------------------------------------+       +------------------------------------+
```

---

## 2. Key Architectural Distinctions

| Aspect | Human Persona | AI Agent |
| :--- | :--- | :--- |
| **Identity** | User Account / Corporate Identity (OAuth/JWT) | Service Account / Protocol Identity (Agent ID) |
| **Accountability** | Legal, financial, and operational liability | None (Software component under system audit) |
| **Primary Interface** | Web UI (React Dashboard), Mobile App | API endpoints, A2A messaging, gRPC/HTTP |
| **Function** | Defines business goals, reviews, approves | Gathers data, extracts features, ranks hypotheses |
| **Permission Scope** | Role-Based Access Control (RBAC) | Tool/Capability Scopes (MCP Read/Write tokens) |

---

## 3. Common Anti-Pattern: 1-to-1 Persona-to-Agent Mapping

### The Anti-Pattern
Beginner multi-agent applications often create one agent for every human job title:
- `OperatorAgent`
- `QualityEngineerAgent`
- `QualityManagerAgent`

### Why This Fails in Production
1. **Misplaces Accountability**: Software agents cannot legally approve an ISO 9001 incident closure or take liability for a field product recall.
2. **Creates Unnecessary Agency**: An operator submitting an inspection image requires a clean HTML form upload, not an autonomous conversational agent.
3. **Obfuscates Software Boundaries**: Software agents should be designed around **technical domains & tools** (e.g., Vision Processing, Document Retrieval, Telemetry Correlation), not around corporate hierarchy titles.

---

## 4. How ForgeSight Applies This Distinction
In ForgeSight:
- **Quality Engineer (Persona)** is the human authority who reviews evidence and signs off on root-cause investigations.
- **Supervisor Agent / RAG Service / CV Service (Software)** are backend capabilities that assist the Quality Engineer by cross-correlating data across factory silos.
