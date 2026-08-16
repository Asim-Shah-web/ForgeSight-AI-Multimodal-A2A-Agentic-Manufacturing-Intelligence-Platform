# 01 — Why Agent-To-Agent (A2A)?

## 1. What problem does this solve?
As AI systems evolve from monolithic LLM wrappers into multi-agent systems, agents must communicate across service boundaries. A2A establishes a standardized protocol for autonomous agent interoperability.

## 2. Intuition
Instead of function calling inside a single process, agents communicate like microservices over HTTP/JSON RPC.

## 3. Key Takeaway
A2A enables independent ownership, modular deployment, and interoperability between agents built using different frameworks.
