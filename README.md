# ForgeSight AI — A2A-Powered Multimodal Manufacturing Intelligence Platform

> **Collaborative AI agents for visual quality inspection, root-cause investigation, and manufacturing operations.**

ForgeSight AI is a production-oriented, educational multi-agent manufacturing intelligence platform built to deeply learn and demonstrate **Agent-to-Agent (A2A) protocol, Model Context Protocol (MCP), Retrieval-Augmented Generation (RAG), Computer Vision (CV), Multimodal Reasoning, FastAPI, and React**.

---

## 🌟 Core Architecture & Mental Model

- **A2A (Agent-to-Agent)**: Peer-to-peer task delegation and collaboration between specialized AI agents (Supervisor, Vision, Quality, Production, Maintenance, Root Cause, Supplier, Reporting).
- **MCP (Model Context Protocol)**: Standardized integration between agents and enterprise tools/data sources (ERP, QMS, inventory, maintenance history).
- **RAG System**: Manufacturing knowledge base incorporating SOPs, defect catalogs, and equipment manuals.
- **Vision Pipeline**: Inspection analysis for electronic assemblies (solder bridging, missing components, assembly anomalies).

---

## 📁 Repository Structure

```text
.
├── docs/                 # System architecture, API specs, and ADRs
├── learning/             # Step-by-step learning harness notes (A2A, MCP, RAG, CV)
├── src/forgesight/       # Core Python backend package
│   ├── config/           # App settings & logging
│   ├── agents/           # Specialized agent implementations
│   ├── a2a/              # Agent-to-Agent protocol layer
│   ├── mcp/              # Model Context Protocol clients/tools
│   ├── rag/              # Ingestion, vector retrieval & reranking
│   ├── vision/           # Preprocessing & CV inference
│   ├── multimodal/       # Multimodal input processing & reasoning
│   ├── workflows/        # LangGraph stateful orchestration
│   ├── domain/           # Core domain models
│   └── api/              # FastAPI application & routes
├── mcp_servers/          # Independent MCP server processes
├── frontend/forgesight-web/# React + Vite web user interface
├── data/                 # Raw, processed, and synthetic datasets
├── experiments/          # Isolated experiments for A2A and CV
├── tests/                # Unit and integration test suite
├── scripts/              # Data ingestion and evaluation utilities
└── notebooks/            # Exploratory research notebooks
```

---

## 🚀 Quickstart Guide

### 1. Environment Setup

```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows PowerShell
source venv/bin/activate      # Linux/macOS

# Install package dependencies
pip install -e .[dev,ai]
```

### 2. Run Backend API

```bash
uvicorn forgesight.api.main:app --reload
```

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
