# ADR 001: Overall Project Architecture

## Status
Accepted

## Context
ForgeSight AI requires a modular architecture separating agent delegation (A2A), tool access (MCP), knowledge search (RAG), visual reasoning (CV), and web delivery (FastAPI/React).

## Decision
Adopt a decoupled Python package (`src/forgesight`) backed by clear service and protocol boundaries.
