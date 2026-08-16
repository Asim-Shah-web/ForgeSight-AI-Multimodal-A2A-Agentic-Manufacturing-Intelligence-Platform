# ADR 002: Agent-to-Agent (A2A) Protocol Boundaries

## Status
Accepted

## Context
Clarify when agents should communicate via A2A vs direct internal Python method invocation.

## Decision
Use A2A whenever an agent acts as an autonomous capability with its own identity, card, and lifecycle.
