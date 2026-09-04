# ForgeSight AI — A2A-Powered Multimodal Manufacturing Intelligence Platform

> **Portfolio project:** A production-oriented, educational implementation of a multimodal agentic manufacturing-quality platform built to deeply learn and demonstrate **A2A, MCP, RAG, Computer Vision, multimodal AI, FastAPI, React, evaluation, observability, and production engineering**.

---

## 1. Project Identity

### Project name

# **ForgeSight AI**

**Tagline:**  
> *Collaborative AI agents for visual quality inspection, root-cause investigation, and manufacturing operations.*

The name is intentionally broad enough to support a complete manufacturing intelligence platform rather than a single defect-detection model.

### Portfolio description

ForgeSight AI is a multimodal agentic AI platform for manufacturing quality operations. It combines computer vision, multimodal reasoning, RAG, MCP, and A2A to allow specialized AI agents to collaborate on production-quality incidents.

A typical workflow starts with an operator submitting an image, video, document, or text description of a manufacturing issue. A vision agent analyzes visual evidence, a quality agent investigates the issue, RAG provides relevant manufacturing knowledge, MCP exposes enterprise tools and data, and specialized agents communicate through A2A to perform investigation, root-cause analysis, and reporting.

The project is deliberately built as an **A2A learning laboratory**. Every major A2A concept is first studied in a dedicated Markdown learning note, then implemented in a progressively more realistic version of the platform.

---

# 2. The Core Learning Philosophy

This project is not intended to be:

> "Build a huge multi-agent application as quickly as possible."

Instead, it follows this principle:

> **Learn the problem → understand the protocol concept → implement the smallest experiment → integrate it into ForgeSight → test it → document it.**

Every important technology should therefore have two layers:

### Learning layer

```text
learning/
    a2a/
    mcp/
    rag/
    computer_vision/
    multimodal/
    architecture/
    backend/
    frontend/
    production/
```

### Implementation layer

```text
src/
    agents/
    a2a/
    mcp/
    rag/
    vision/
    multimodal/
    api/
```

The learning notes explain **why** something exists.

The implementation demonstrates **how** it works.

The tests prove **whether** it works.

---

# 3. Technology Stack

## AI / Agentic

- Python
- LangGraph where orchestration/stateful workflows are useful
- Google ADK where appropriate for agent implementation experiments
- CrewAI for comparative experiments, not as the core architectural dependency
- A2A for agent-to-agent communication
- MCP for agent-to-tool/resource communication

## AI capabilities

- LLMs
- Vision-language models
- Computer vision models
- Embeddings
- RAG
- Multimodal reasoning
- Structured output
- Tool calling

## Backend

- FastAPI
- Pydantic
- Uvicorn
- Async Python
- REST APIs
- WebSockets or streaming endpoints where useful

## Frontend

- React
- TypeScript
- Vite
- Component-based UI
- Chat interface
- Inspection dashboard
- Agent/task visualization
- Evidence viewer
- Incident timeline

## Data

- PostgreSQL
- Vector database or PostgreSQL vector extension
- Object storage/local object store for images and documents
- Redis where useful
- Synthetic manufacturing datasets

## DevOps

- Docker
- Docker Compose
- Environment-based configuration
- CI
- Automated tests
- Logging
- Metrics
- Tracing

---

# 4. What ForgeSight Actually Solves

ForgeSight focuses on a manufacturing-quality incident workflow.

A manufacturing operator might submit:

```text
Text:
"The solder joint on component C17 looks abnormal."

Image:
component_c17.jpg

Optional:
- production batch
- machine ID
- line ID
- timestamp
- operator notes
```

ForgeSight should eventually be able to:

1. Receive the incident.
2. Analyze the image/video.
3. Identify possible visual defects.
4. Extract structured observations.
5. Search manufacturing documentation.
6. Query operational systems through MCP.
7. Delegate investigation to specialized agents through A2A.
8. Correlate evidence.
9. Perform root-cause analysis.
10. Recommend corrective action.
11. Produce a human-reviewable report.
12. Track the complete task lifecycle.
13. Show the reasoning workflow and evidence in the UI.
14. Preserve an audit trail.

The system should **not** blindly make high-impact production decisions. Recommendations should be presented for human review where appropriate.

---

# 5. The Architectural Mental Model

One of the most important learning outcomes is understanding the difference between A2A and MCP.

## A2A

A2A answers:

> **How can one agent communicate with another agent?**

```text
Agent A
   |
   | A2A
   v
Agent B
   |
   | A2A
   v
Agent C
```

Agents should be independently understandable services/capabilities.

---

## MCP

MCP answers:

> **How can an agent access tools, resources, and external context?**

```text
                 +----------------+
                 |     Agent      |
                 +-------+--------+
                         |
                        MCP
          +--------------+--------------+
          |              |              |
          v              v              v
       Database       Inventory       ERP/API
```

---

## RAG

RAG answers:

> **How does an agent retrieve relevant knowledge?**

```text
Question
   |
   v
Retriever
   |
   v
Knowledge Base
   |
   v
Relevant Context
   |
   v
LLM
```

---

## Computer Vision

CV answers:

> **How does the system understand visual evidence?**

```text
Image / Video
      |
      v
Vision Model
      |
      v
Visual Observations
      |
      v
Agent reasoning
```

---

## Multimodal AI

Multimodal reasoning combines:

```text
Text
Images
Video
PDFs
Tables
Sensor data
Structured records
       |
       v
Multimodal Agent
```

---

# 6. Target Agent Topology

The final system should contain specialized agents rather than a single giant agent.

Recommended agents:

```text
                        +----------------------+
                        |   Supervisor /       |
                        |   Investigation      |
                        |   Agent              |
                        +----------+-----------+
                                   |
                     A2A           |
              +--------------------+--------------------+
              |                    |                    |
              v                    v                    v
       Vision Agent          Quality Agent       Production Agent
              |                    |                    |
              |                    |                    |
              v                    v                    v
        CV Pipeline              RAG             MCP Tools
                                   |
                                   |
                 +-----------------+-----------------+
                 |                 |                 |
                 v                 v                 v
          Maintenance        Root Cause         Supplier
             Agent             Agent             Agent
                 |                 |                 |
                 +-----------------+-----------------+
                                   |
                                   v
                           Reporting Agent
                                   |
                                   v
                           Human Approval
```

Do not implement all of these at once.

The topology should grow throughout the phases.

---

# 7. Industry Scenario

ForgeSight will use a fictional manufacturing organization so that the project can be demonstrated without proprietary company data.

Example organization:

**ForgeWorks Electronics**

Manufactures electronic control modules and PCB assemblies.

Example quality incidents:

- Solder bridging
- Missing components
- Incorrect component placement
- Damaged components
- Surface defects
- Connector damage
- Label mismatch
- Packaging damage
- Assembly anomalies

Example enterprise systems:

```text
Production Management System
Quality Management System
Inventory System
Maintenance System
Supplier System
Document Repository
```

Initially these systems can be mocked.

Later they can be represented by realistic APIs/database tables.

---

# 8. Repository Structure

The repository should evolve toward this structure:

```text
forgesight-ai/
│
├── README.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── .gitignore
├── .env.example
├── docker-compose.yml
├── Makefile
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── tests.yml
│
├── .vscode/
│   └── settings.json
│
├── venv/
│   └── # local Python virtual environment - NEVER commit
│
├── docs/
│   ├── architecture/
│   │   ├── system-overview.md
│   │   ├── agent-topology.md
│   │   ├── a2a-architecture.md
│   │   ├── mcp-architecture.md
│   │   ├── rag-architecture.md
│   │   ├── vision-architecture.md
│   │   └── deployment-architecture.md
│   │
│   ├── api/
│   │   └── api-overview.md
│   │
│   ├── decisions/
│   │   └── adr/
│   │       ├── 001-project-architecture.md
│   │       ├── 002-a2a-boundaries.md
│   │       └── 003-mcp-boundaries.md
│   │
│   └── diagrams/
│
├── learning/
│   ├── README.md
│   │
│   ├── a2a/
│   │   ├── 00-a2a-learning-map.md
│   │   ├── 01-why-agent-to-agent.md
│   │   ├── 02-a2a-mental-model.md
│   │   ├── 03-agent-cards.md
│   │   ├── 04-agent-discovery.md
│   │   ├── 05-tasks.md
│   │   ├── 06-task-lifecycle.md
│   │   ├── 07-messages.md
│   │   ├── 08-parts.md
│   │   ├── 09-artifacts.md
│   │   ├── 10-streaming.md
│   │   ├── 11-push-notifications.md
│   │   ├── 12-authentication.md
│   │   ├── 13-errors-and-retries.md
│   │   ├── 14-agent-discovery-patterns.md
│   │   ├── 15-a2a-vs-mcp.md
│   │   ├── 16-a2a-security.md
│   │   ├── 17-a2a-production-patterns.md
│   │   └── 18-a2a-project-integration.md
│   │
│   ├── mcp/
│   │   ├── 01-mcp-mental-model.md
│   │   ├── 02-tools.md
│   │   ├── 03-resources.md
│   │   ├── 04-prompts.md
│   │   ├── 05-server-client-architecture.md
│   │   └── 06-mcp-in-forgesight.md
│   │
│   ├── rag/
│   ├── computer_vision/
│   ├── multimodal/
│   ├── backend/
│   ├── frontend/
│   └── production/
│
├── src/
│   └── forgesight/
│       ├── __init__.py
│       │
│       ├── config/
│       │   ├── settings.py
│       │   └── logging.py
│       │
│       ├── agents/
│       │   ├── base/
│       │   ├── supervisor/
│       │   ├── vision/
│       │   ├── quality/
│       │   ├── production/
│       │   ├── maintenance/
│       │   ├── root_cause/
│       │   ├── supplier/
│       │   └── reporting/
│       │
│       ├── a2a/
│       │   ├── clients/
│       │   ├── servers/
│       │   ├── models/
│       │   ├── discovery/
│       │   ├── tasks/
│       │   ├── messaging/
│       │   └── transport/
│       │
│       ├── mcp/
│       │   ├── clients/
│       │   ├── servers/
│       │   └── tools/
│       │
│       ├── rag/
│       │   ├── ingestion/
│       │   ├── chunking/
│       │   ├── embeddings/
│       │   ├── retrieval/
│       │   ├── reranking/
│       │   └── evaluation/
│       │
│       ├── vision/
│       │   ├── preprocessing/
│       │   ├── detection/
│       │   ├── classification/
│       │   ├── inspection/
│       │   └── postprocessing/
│       │
│       ├── multimodal/
│       │   ├── inputs/
│       │   ├── preprocessing/
│       │   └── reasoning/
│       │
│       ├── workflows/
│       │   ├── inspection.py
│       │   ├── investigation.py
│       │   └── root_cause.py
│       │
│       ├── domain/
│       │   ├── incidents.py
│       │   ├── inspections.py
│       │   ├── production.py
│       │   └── quality.py
│       │
│       └── api/
│           ├── main.py
│           ├── dependencies.py
│           ├── routes/
│           │   ├── chat.py
│           │   ├── incidents.py
│           │   ├── inspections.py
│           │   ├── agents.py
│           │   └── health.py
│           └── schemas/
│
├── frontend/
│   └── forgesight-web/
│       ├── package.json
│       ├── src/
│       │   ├── components/
│       │   ├── pages/
│       │   ├── hooks/
│       │   ├── services/
│       │   ├── types/
│       │   └── app/
│       └── public/
│
├── mcp_servers/
│   ├── manufacturing/
│   │   ├── server.py
│   │   └── tools/
│   │       ├── production.py
│   │       ├── inventory.py
│   │       ├── maintenance.py
│   │       └── quality.py
│   │
│   └── documents/
│       └── server.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── documents/
│   ├── images/
│   ├── videos/
│   ├── synthetic/
│   └── evaluation/
│
├── experiments/
│   ├── a2a/
│   ├── vision/
│   ├── rag/
│   ├── multimodal/
│   └── agents/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── a2a/
│   ├── mcp/
│   ├── rag/
│   ├── vision/
│   ├── api/
│   └── evaluation/
│
├── scripts/
│   ├── seed_data.py
│   ├── ingest_documents.py
│   ├── run_inspection.py
│   └── run_evaluation.py
│
└── notebooks/
    └── exploration/
```

---

# 9. Virtual Environment

Use the following local virtual-environment directory:

```text
venv/
```

Create it with:

```bash
python -m venv venv
```

Activate on Linux/macOS:

```bash
source venv/bin/activate
```

Activate on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

The `venv/` directory must be in `.gitignore`.

The project should eventually use a proper dependency manager such as `uv`, but the learning environment can begin with the familiar Python `venv`.

---

# 10. The Learning Harness

The **Learning Harness** is one of the most important parts of ForgeSight.

It is the mechanism that turns the project from an ordinary portfolio application into an A2A learning laboratory.

The harness should force a repeatable process:

```text
Concept
   ↓
Question
   ↓
Theory Note
   ↓
Minimal Experiment
   ↓
Implementation
   ↓
Test
   ↓
Failure / Observation
   ↓
Integration
   ↓
Reflection
   ↓
Updated Markdown
```

Every major A2A topic should have a corresponding learning record.

---

# 11. The A2A Concept Harness

Each A2A topic should use a standard Markdown template.

Example:

```text
learning/a2a/05-tasks.md
```

Template:

```markdown
# A2A Tasks

## 1. What problem does this solve?

## 2. Intuition

Explain the concept without protocol terminology.

## 3. Protocol-level understanding

Explain the actual A2A concept.

## 4. Important objects

## 5. Lifecycle

## 6. Minimal example

## 7. Code walkthrough

Explain every important line.

## 8. ForgeSight implementation

## 9. What can go wrong?

## 10. Testing

## 11. Experiment

## 12. Lessons learned

## 13. Questions I still have

## 14. Interview questions

## 15. Production considerations
```

This format should be used consistently.

---

# 12. The Teaching Chatbot

The project should include a development/learning chatbot conceptually called the:

# ForgeSight Learning Copilot

Its job is not simply to generate code.

It should behave like a technical mentor.

For every A2A topic it should:

1. Explain the concept.
2. Explain why it exists.
3. Give intuition.
4. Show the protocol structure.
5. Show the smallest possible code example.
6. Walk through each important line.
7. Generate/update the relevant `.md` file.
8. Create a tiny experiment.
9. Ask the learner to inspect the result.
10. Explain errors.
11. Connect the concept to ForgeSight.
12. Help implement the production version.
13. Add tests.
14. Update the learning note.
15. Record lessons learned.

The chatbot should therefore operate as a **learning orchestrator**.

---

# 13. Harness Rules

The harness should enforce these rules:

### Rule 1 — No concept without an explanation

Before implementation, create the corresponding Markdown note.

### Rule 2 — No implementation without an experiment

Build a tiny isolated experiment first whenever practical.

### Rule 3 — No generated code without understanding

The learner should be able to explain:

- inputs
- outputs
- state
- protocol objects
- control flow
- failure paths
- dependencies

### Rule 4 — Every major feature gets tests

At minimum:

```text
unit test
integration test
failure-path test
```

where applicable.

### Rule 5 — Every major architecture decision gets an ADR

Example:

```text
docs/decisions/adr/002-a2a-boundaries.md
```

### Rule 6 — The chatbot should prefer incremental code

Avoid dumping a 500-line implementation.

Implement in small pieces.

### Rule 7 — Explain before abstracting

The learner should first understand the low-level mechanism before relying on framework abstractions.

---

# 14. Phase 0 — Project Initialization

## Objective

Create a professional repository and development environment.

### Tasks

- Create Git repository.
- Create `venv/`.
- Create Python package.
- Configure `pyproject.toml`.
- Configure linting.
- Configure formatting.
- Configure testing.
- Create `.env.example`.
- Create initial README.
- Establish project conventions.
- Create `learning/`.
- Create `docs/`.
- Create initial architecture diagram.
- Create initial ADR.

### Deliverable

A clean empty architecture that can be committed before any AI functionality exists.

---

# 15. Phase 1 — Understand the Business Problem

## Objective

Understand the manufacturing workflow before introducing agents.

Study:

- Manufacturing quality workflow
- Inspection
- Defect classification
- Quality incidents
- Production batches
- Work orders
- Maintenance
- Root-cause analysis
- Corrective actions
- Human approval

### Build

Create synthetic business entities:

```text
Product
Batch
ProductionLine
Machine
Inspection
QualityIncident
Defect
MaintenanceEvent
Supplier
WorkOrder
```

### Learning outcome

You should understand the domain independently of AI.

---

# 16. Phase 2 — Build the Non-Agent Baseline

Before building a multi-agent system, build a conventional baseline.

Pipeline:

```text
Image
  ↓
CV model
  ↓
Defect result
  ↓
Rule-based workflow
  ↓
Report
```

This is extremely important.

You need a baseline to compare the agentic system against.

### Deliverables

- Image upload
- CV inference
- Defect classification
- Structured output
- Basic report
- Tests

---

# 17. Phase 3 — Build the First Agent

Create a single Quality Investigation Agent.

It should receive:

```text
inspection result
operator description
production metadata
```

and produce:

```text
investigation summary
possible causes
recommended next steps
```

Learn:

- Agent loop
- Prompt
- Context
- Tools
- Structured outputs
- State
- Memory
- Error handling

Do not introduce A2A yet.

The purpose is to understand the agent itself before understanding agent-to-agent protocols.

---

# 18. Phase 4 — Two Agents Without A2A

Build:

```text
Vision Agent
      ↓
Quality Agent
```

Initially use a simple local function/service boundary.

The point is to experience the problem:

> "What happens when the Vision Agent and Quality Agent become independently deployed capabilities?"

Study:

- Contracts
- Serialization
- Request/response boundaries
- Timeouts
- Errors
- Versioning
- Service discovery

This phase creates the motivation for A2A.

---

# 19. Phase 5 — A2A Introduction

Now begin the serious A2A learning journey.

Create:

```text
learning/a2a/01-why-agent-to-agent.md
learning/a2a/02-a2a-mental-model.md
```

Understand:

- Why agent-to-agent communication needs standardization.
- Difference between function calls and agent communication.
- Agent as a network-accessible capability.
- Independent agent ownership.
- Protocol boundaries.
- Interoperability.

Then implement the smallest A2A experiment.

The experiment should be completely separate from the main application first.

---

# 20. Phase 6 — Agent Cards and Discovery

Study:

- Agent identity
- Agent capabilities
- Skills
- Agent Card
- Endpoint information
- Discovery

Create:

```text
learning/a2a/03-agent-cards.md
learning/a2a/04-agent-discovery.md
```

Implement:

```text
Vision Agent Card
Quality Agent Card
```

Then build a small discovery mechanism.

The learner should be able to answer:

> "How does an agent know what another agent can do?"

---

# 21. Phase 7 — Tasks, Messages, Parts, and Artifacts

This is one of the most important A2A phases.

Study individually:

```text
Task
Message
Part
Artifact
```

Do not learn them as one giant abstraction.

For every concept:

```text
intuition
→ protocol meaning
→ minimal example
→ code
→ experiment
→ ForgeSight integration
```

Create separate Markdown notes.

Then implement a complete quality-investigation task.

Example conceptual flow:

```text
Client
  |
  | task
  v
Quality Agent
  |
  | processing
  v
Artifact
  |
  v
Client
```

---

# 22. Phase 8 — Task Lifecycle and Long-Running Work

Manufacturing investigation may take time.

Study task states and lifecycle behavior.

Explore concepts such as:

```text
submitted
working
input-required
completed
failed
canceled
```

The exact protocol semantics should be verified against the current A2A specification during implementation.

Build:

- Task persistence
- Task status
- Task polling
- Failure handling
- Cancellation
- Retry strategy

Create integration tests for every meaningful state transition.

---

# 23. Phase 9 — Streaming and Real-Time Agent Communication

Study streaming.

A quality investigation should eventually be able to expose progress such as:

```text
Task started
↓
Vision evidence received
↓
Quality agent investigating
↓
Maintenance agent consulted
↓
RAG evidence retrieved
↓
Root cause analysis completed
↓
Report generated
```

Do not confuse user-facing UI streaming with protocol-level agent communication.

Study both separately.

---

# 24. Phase 10 — Multi-Agent Collaboration

Now expand the topology.

Introduce:

```text
Vision Agent
Quality Agent
Production Agent
Maintenance Agent
Root Cause Agent
Reporting Agent
```

The agents should communicate through A2A where the boundary makes sense.

The supervisor should coordinate rather than contain every capability.

The project should demonstrate:

```text
Agent A
   |
   +----> Agent B
   |
   +----> Agent C
   |
   +----> Agent D
```

and potentially:

```text
Agent B
   |
   +----> Agent E
```

This is where the project becomes a true multi-agent system.

---

# 25. Phase 11 — MCP Integration

Now introduce MCP deeply.

The key learning question is:

> Why is this MCP instead of A2A?

Create a manufacturing MCP server exposing realistic tools.

Potential tools:

```text
get_production_batch()
get_machine_status()
get_machine_history()
get_inventory()
get_component_history()
get_quality_incidents()
create_work_order()
get_supplier_information()
search_internal_documents()
```

Possible MCP resources:

```text
production records
machine manuals
quality records
supplier documents
```

The Quality Agent should use MCP to access business information.

The Root Cause Agent should use MCP to retrieve operational evidence.

The system should demonstrate the architecture:

```text
             A2A
Agent A --------------> Agent B
  |
  |
 MCP
  |
  +---- Database
  +---- Inventory
  +---- Production API
  +---- Maintenance API
```

---

# 26. Phase 12 — RAG Knowledge System

Build a manufacturing knowledge base.

Documents:

```text
SOPs
Quality manuals
Maintenance manuals
Machine documentation
Inspection procedures
Defect catalogs
Troubleshooting guides
Safety procedures
Supplier documentation
```

Pipeline:

```text
Documents
   ↓
Parsing
   ↓
Cleaning
   ↓
Chunking
   ↓
Embedding
   ↓
Vector storage
   ↓
Retrieval
   ↓
Reranking
   ↓
Agent context
```

Evaluate:

- Retrieval precision
- Recall
- Relevance
- Citation correctness
- Groundedness

The RAG system should return evidence, not simply context.

---

# 27. Phase 13 — Computer Vision Integration

Now connect the real CV pipeline to the agent architecture.

Possible pipeline:

```text
Image
  ↓
Preprocessing
  ↓
Detection / Classification
  ↓
Defect observations
  ↓
Confidence
  ↓
Evidence
  ↓
Vision Agent
```

The CV system should produce structured information.

Example:

```json
{
  "defect_type": "solder_bridge",
  "confidence": 0.94,
  "bounding_boxes": [],
  "severity": "high",
  "evidence": "..."
}
```

The agent should reason over CV results instead of pretending the LLM itself is the detector.

---

# 28. Phase 14 — Multimodal Investigation

Introduce multimodal input.

An incident may contain:

```text
Image
+
Text
+
PDF
+
Inspection metadata
+
Production data
+
Maintenance history
```

The multimodal investigation workflow becomes:

```text
User
 |
 +-- image
 +-- text
 +-- document
 +-- metadata
 |
 v
Supervisor
 |
 +---- Vision Agent
 |
 +---- RAG Agent
 |
 +---- Production Agent
 |
 +---- Maintenance Agent
 |
 v
Root Cause Agent
 |
 v
Report
```

Study multimodal context management carefully.

Do not blindly send every artifact to every agent.

---

# 29. Phase 15 — Full Investigation Workflow

Create the complete workflow:

```text
Incident Created
      ↓
Evidence Validation
      ↓
Vision Analysis
      ↓
Knowledge Retrieval
      ↓
Production Context
      ↓
Maintenance Context
      ↓
Root Cause Investigation
      ↓
Confidence Assessment
      ↓
Corrective Action
      ↓
Human Approval
      ↓
Work Order / Report
```

This becomes the main ForgeSight business workflow.

---

# 30. Phase 16 — Backend API with FastAPI

Only after the agent architecture is stable should the main public backend be introduced.

Create:

```text
src/forgesight/api/
```

Endpoints should eventually include:

```text
GET    /health
POST   /incidents
GET    /incidents/{id}
POST   /incidents/{id}/investigate
GET    /incidents/{id}/tasks
GET    /agents
GET    /agents/{id}
POST   /chat
POST   /inspections
GET    /inspections/{id}
```

Potential streaming endpoint:

```text
GET /incidents/{id}/events
```

or a WebSocket endpoint where appropriate.

FastAPI should be a clean application boundary, not the place where all agent logic is embedded.

Recommended separation:

```text
FastAPI
   |
   v
Application Services
   |
   v
Agent System
   |
   +---- A2A
   +---- MCP
   +---- RAG
   +---- CV
```

---

# 31. Phase 17 — React Frontend

Build a professional React frontend.

Major screens:

## Dashboard

Show:

- Open incidents
- Defect statistics
- Investigation status
- Recent activity

## Incident Creation

Allow:

- Image upload
- Video upload
- Text description
- Metadata

## Investigation View

Show:

```text
Incident
   ↓
Agent activity
   ↓
A2A tasks
   ↓
Evidence
   ↓
RAG citations
   ↓
CV findings
   ↓
Root-cause analysis
   ↓
Recommendation
```

## Agent View

Display:

- Agent identity
- Capabilities
- Skills
- Status
- Recent tasks

## Knowledge View

Show retrieved documents and evidence.

## Chat

Allow the operator to ask questions about the incident.

---

# 32. Phase 18 — Observability

A serious portfolio project needs observability.

Track:

```text
request latency
agent latency
A2A task duration
MCP tool duration
RAG retrieval latency
CV inference latency
LLM latency
token usage
errors
retries
task states
```

Add structured logs.

Eventually add:

- distributed tracing
- correlation IDs
- task IDs
- incident IDs
- agent IDs

A useful trace should look conceptually like:

```text
incident_id
   |
   +-- supervisor_task
         |
         +-- vision_agent_task
         |
         +-- quality_agent_task
         |      |
         |      +-- rag_retrieval
         |
         +-- production_agent_task
                |
                +-- mcp:get_batch
                +-- mcp:get_machine_history
```

---

# 33. Phase 19 — Evaluation Harness

This is another critical part of the project.

Do not evaluate the system only by asking:

> "Does the answer look good?"

Create datasets.

Example:

```text
evaluation/
    incidents.jsonl
    expected_defects.jsonl
    expected_retrievals.jsonl
    expected_workflows.jsonl
```

Evaluate:

## CV

- Precision
- Recall
- F1
- mAP where applicable

## RAG

- Retrieval relevance
- Recall@K
- Precision@K
- Citation correctness

## Agents

- Task success rate
- Tool selection accuracy
- Structured output validity
- Groundedness

## A2A

- Successful task completion
- Correct agent selection
- Error recovery
- Task lifecycle correctness

## System

- End-to-end success rate
- Latency
- Cost
- Reliability

---

# 34. Phase 20 — Security

Study:

- Authentication
- Authorization
- Agent identity
- Tool permissions
- Input validation
- File upload security
- Prompt injection
- RAG poisoning
- Malicious documents
- Tool abuse
- Secrets management

The security model should distinguish:

```text
User
Agent
A2A peer
MCP server
Tool
Database
```

Each should have appropriate trust boundaries.

---

# 35. Phase 21 — Reliability Engineering

Introduce failure intentionally.

Simulate:

```text
Agent unavailable
MCP timeout
RAG unavailable
CV model failure
LLM timeout
Malformed task
Invalid artifact
Network failure
Database failure
```

Build:

- retries
- exponential backoff
- timeout policies
- circuit breaking where appropriate
- fallback behavior
- task recovery
- idempotency
- dead-letter handling where appropriate

A portfolio project becomes much more credible when it demonstrates how the system behaves when things go wrong.

---

# 36. Phase 22 — Production Architecture

Move from:

```text
localhost
```

toward:

```text
                    React
                      |
                      v
                 API Gateway
                      |
                    FastAPI
                      |
        +-------------+-------------+
        |             |             |
        v             v             v
   Supervisor     Incident       Auth
      Agent        Service       Service
        |
        +--------------------------+
        |             |            |
       A2A           RAG          MCP
        |             |            |
        v             v            v
   Agent Services  Vector DB   Enterprise APIs
        |
        v
   Specialized Agents
```

Containerize major services.

Use Docker Compose locally.

Prepare for cloud deployment later.

---

# 37. Phase 23 — Documentation and Portfolio Polish

Create:

```text
README.md
ARCHITECTURE.md
CONTRIBUTING.md
SECURITY.md
LEARNING.md
```

README should contain:

- Problem
- Solution
- Architecture
- Demo
- Technologies
- Agent topology
- A2A explanation
- MCP explanation
- RAG explanation
- CV explanation
- Screenshots
- Installation
- Running locally
- Testing
- Evaluation
- Limitations
- Future work

Add architecture diagrams.

Add demo videos/GIFs.

Add example incidents.

---

# 38. Phase 24 — Final Portfolio Demo

The final demo should tell a story.

### Scenario

A factory operator notices a defect.

They upload an image.

The system says:

```text
Incident #1042 created
```

Vision Agent:

```text
Possible solder bridge detected.
Confidence: 94%
```

Quality Agent:

```text
Investigating defect.
```

Production Agent:

```text
Batch 1042 originated from Line 3.
```

Maintenance Agent:

```text
Machine M-17 had two similar incidents in the previous shift.
```

RAG:

```text
Relevant SOP and maintenance documentation found.
```

Root Cause Agent:

```text
Most likely cause:
temperature instability during soldering.
```

System:

```text
Recommended action:
inspect machine M-17 and review thermal calibration.
```

Human approves.

System:

```text
Maintenance work order generated.
Quality report generated.
```

This is the final portfolio story.

---

# 39. Recommended Final Architecture

```text
                           USER
                            |
                            v
                    React Frontend
                            |
                            v
                       FastAPI API
                            |
                            v
                  Investigation Service
                            |
                            v
                  Supervisor Agent
                            |
              +-------------+-------------+
              |             |             |
             A2A           A2A           A2A
              |             |             |
              v             v             v
        Vision Agent   Quality Agent  Production Agent
              |             |             |
              |             |             |
             CV            RAG           MCP
              |             |             |
              |             |             |
              +-------------+-------------+
                            |
                            v
                     Root Cause Agent
                            |
                            v
                     Reporting Agent
                            |
                            v
                     Human Approval
                            |
                            v
                    Corrective Action
```

---

# 40. What You Should Learn vs What the Chatbot Should Do

The chatbot can generate:

- Boilerplate
- Project files
- Test scaffolding
- Markdown templates
- Initial implementations
- Documentation
- Example datasets
- Refactoring suggestions
- Debugging hypotheses

But you should personally understand:

- A2A concepts
- Agent Cards
- Task semantics
- Message structure
- Parts
- Artifacts
- Streaming
- Discovery
- Authentication
- A2A vs MCP
- Agent boundaries
- Distributed-system tradeoffs
- Failure modes
- Why a protocol is needed
- Why a particular architecture was selected

The chatbot should never become a substitute for understanding.

---

# 41. The "Explain Every Line" Protocol

Whenever the learning chatbot generates a new A2A implementation, it should follow this sequence:

```text
1. Show the smallest implementation.
2. Explain imports.
3. Explain data structures.
4. Explain protocol objects.
5. Explain control flow.
6. Explain network boundaries.
7. Explain serialization.
8. Explain async behavior.
9. Explain error handling.
10. Run the example.
11. Modify one thing.
12. Observe the result.
13. Integrate into ForgeSight.
```

This is how the project becomes an actual learning system.

---

# 42. A2A Learning Sequence

The recommended A2A curriculum is:

```text
01. Why A2A?
        ↓
02. Mental model
        ↓
03. Agent identity
        ↓
04. Agent Cards
        ↓
05. Discovery
        ↓
06. Tasks
        ↓
07. Task lifecycle
        ↓
08. Messages
        ↓
09. Parts
        ↓
10. Artifacts
        ↓
11. Streaming
        ↓
12. Push notifications
        ↓
13. Authentication
        ↓
14. Errors / retries
        ↓
15. Multi-agent patterns
        ↓
16. A2A vs MCP
        ↓
17. Security
        ↓
18. Production patterns
```

Always verify protocol-specific details against the current official A2A specification when implementing them because protocol schemas and recommended practices can evolve.

---

# 43. Suggested Git Strategy

Use feature branches:

```text
main
develop
feature/a2a-agent-card
feature/a2a-task
feature/a2a-streaming
feature/mcp-manufacturing-server
feature/rag-pipeline
feature/cv-inspection
feature/fastapi
feature/react-dashboard
```

Commit examples:

```text
feat(a2a): add first agent card experiment
feat(a2a): implement task lifecycle
feat(mcp): add manufacturing inventory tools
feat(rag): add document ingestion pipeline
feat(vision): add defect classification
feat(api): expose incident investigation endpoint
feat(ui): add investigation dashboard
test(a2a): add task lifecycle tests
docs(a2a): explain artifacts and parts
```

---

# 44. Testing Strategy

Use multiple levels.

## Unit

Test individual functions.

## Contract

Test A2A message/task structures.

## Integration

Test:

```text
Agent → A2A → Agent
Agent → MCP → Tool
Agent → RAG → Knowledge
```

## End-to-End

Test:

```text
Upload incident
→ CV
→ Agent collaboration
→ RAG
→ MCP
→ root cause
→ report
```

## Failure Tests

Intentionally break dependencies.

## Evaluation Tests

Run datasets and measure quality.

---

# 45. Definition of Done for Each Phase

A phase is not complete merely because the code runs.

A phase is complete when:

```text
[ ] Concept understood
[ ] Learning Markdown created
[ ] Minimal experiment completed
[ ] Implementation integrated
[ ] Tests written
[ ] Failure case explored
[ ] Architecture documented
[ ] Git commit created
[ ] Reflection written
```

This checklist should be embedded into the learning harness.

---

# 46. Final Repository Learning Record

At the end of the project, the repository should contain a chronological learning trail.

Example:

```text
learning/
    a2a/
        01-why-agent-to-agent.md
        02-a2a-mental-model.md
        ...
        18-a2a-project-integration.md
```

Each file should contain:

```text
What I thought before
What I learned
What I implemented
What confused me
What failed
What fixed it
How the protocol works
How ForgeSight uses it
What I would change in production
```

This turns the repository itself into evidence of your engineering learning process.

---

# 47. Final Skills Demonstrated

When complete, ForgeSight should demonstrate practical understanding of:

### Agentic AI

- Multi-agent architecture
- Agent orchestration
- Stateful workflows
- Tool use
- Agent specialization

### A2A

- Agent Cards
- Discovery
- Tasks
- Messages
- Parts
- Artifacts
- Lifecycle
- Streaming
- Authentication
- Agent interoperability
- Failure handling
- Production boundaries

### MCP

- MCP clients
- MCP servers
- Tools
- Resources
- External system integration
- Tool security

### RAG

- ingestion
- chunking
- embeddings
- retrieval
- reranking
- citations
- evaluation

### Computer Vision

- preprocessing
- detection/classification
- structured visual evidence
- confidence
- multimodal integration

### Multimodal AI

- image + text
- documents
- structured data
- multimodal reasoning

### Backend

- FastAPI
- REST
- async Python
- WebSockets/streaming
- validation
- service architecture

### Frontend

- React
- TypeScript
- dashboards
- chat
- real-time task updates
- evidence visualization

### Production Engineering

- Docker
- testing
- observability
- security
- retries
- evaluation
- CI/CD
- architecture documentation

---

# 48. Final Portfolio Positioning

Do not present this project as:

> "I built a chatbot using A2A."

Present it as:

> **ForgeSight AI is a multimodal manufacturing intelligence platform that uses A2A for interoperable agent-to-agent collaboration, MCP for standardized access to enterprise tools and resources, RAG for manufacturing knowledge retrieval, and computer vision for visual quality inspection. The platform exposes its agentic workflows through FastAPI and provides a React-based operational dashboard.**

Then explain the educational engineering layer:

> **The project was developed as an A2A learning laboratory in which every major protocol concept was first studied through isolated experiments, documented in Markdown, tested, and then integrated into the production-style architecture.**

That is a much stronger portfolio narrative.

---

# 49. Final Development Order

The complete journey should therefore be:

```text
PHASE 0
Project initialization
        ↓
PHASE 1
Manufacturing domain
        ↓
PHASE 2
Non-agent CV baseline
        ↓
PHASE 3
First agent
        ↓
PHASE 4
Two agents without A2A
        ↓
PHASE 5
A2A fundamentals
        ↓
PHASE 6
Agent Cards + Discovery
        ↓
PHASE 7
Tasks + Messages + Parts + Artifacts
        ↓
PHASE 8
Task lifecycle
        ↓
PHASE 9
Streaming
        ↓
PHASE 10
Multi-agent A2A
        ↓
PHASE 11
MCP
        ↓
PHASE 12
RAG
        ↓
PHASE 13
Computer Vision integration
        ↓
PHASE 14
Multimodal AI
        ↓
PHASE 15
Complete manufacturing workflow
        ↓
PHASE 16
FastAPI backend
        ↓
PHASE 17
React frontend
        ↓
PHASE 18
Observability
        ↓
PHASE 19
Evaluation harness
        ↓
PHASE 20
Security
        ↓
PHASE 21
Reliability
        ↓
PHASE 22
Production architecture
        ↓
PHASE 23
Documentation + portfolio
        ↓
PHASE 24
Final demo
```

---

# 50. The Ultimate Goal

At the end of ForgeSight, you should be able to explain — without relying on a framework abstraction:

```text
What is an agent?

Why do agents need to communicate?

Why can't ordinary function calls always solve the problem?

What problem does A2A solve?

What is an Agent Card?

How does discovery work?

What is a task?

What is a message?

What is a part?

What is an artifact?

How does task state work?

How does streaming work?

How do agents authenticate?

How are failures handled?

How is A2A different from MCP?

When should I use A2A?

When should I use MCP?

How does RAG fit into an agent?

How does CV fit into an agent?

How do multimodal inputs move through the system?

How do I expose the system through FastAPI?

How does the React frontend observe agent work?

How do I evaluate the entire system?

How do I monitor it?

How do I secure it?

How do I deploy it?
```

If you can answer those questions and demonstrate them through the ForgeSight codebase, you will have learned considerably more than the syntax of an A2A SDK.

You will have learned the **architecture, protocol thinking, distributed-agent concepts, implementation details, and production tradeoffs behind agent-to-agent systems**.

---

# 51. Immediate Next Step
####
Do not start coding the full system yet.

Start with:

```text
PHASE 0
    ↓
Create repository
    ↓
Create venv/
    ↓
Create project structure
    ↓
Create learning harness
    ↓
Create first ADR
    ↓
Create manufacturing domain model
    ↓
Build the non-agent CV baseline
```

Only after the baseline exists should the A2A learning sequence begin.

The project should grow organically so that each A2A abstraction solves a problem you have actually encountered while building ForgeSight.

[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "forgesight"
version = "0.1.0"
description = "A2A-Powered Multimodal Manufacturing Intelligence Platform"
readme = "README.md"
authors = [{ name = "Asim Shah" }]
license = { text = "MIT" }
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.28.0",
    "pydantic>=2.6.0",
    "pydantic-settings>=2.2.0",
    "httpx>=0.27.0",
    "jinja2>=3.1.3",
    "python-multipart>=0.0.9",
    "pyyaml>=6.0.1",
]

[project.optional-dependencies]
ai = [
    "langgraph>=0.0.30",
    "langchain-core>=0.1.30",
    "google-adk>=0.1.0",
    "mcp>=0.1.0",
]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.5",
    "pytest-cov>=4.1.0",
    "ruff>=0.3.0",
    "black>=24.2.0",
    "mypy>=1.8.0",
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.black]
line-length = 100
target-version = ['py310']

#####