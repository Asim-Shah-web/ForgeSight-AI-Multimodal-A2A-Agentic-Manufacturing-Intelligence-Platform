# A2A Protocol Architecture

## Overview

Agent-to-Agent (A2A) protocol handles inter-agent communication, discovery, state delegation, and artifact generation.

## Key Primitives

1. **Agent Cards**: Standard JSON manifests describing agent capability and skill endpoints.
2. **Tasks**: State-tracked work requests with clear lifecycle states (submitted, working, completed, failed).
3. **Messages & Parts**: Multimodal message parts passed between peer agents.
4. **Artifacts**: Structured outputs returned upon task completion.
