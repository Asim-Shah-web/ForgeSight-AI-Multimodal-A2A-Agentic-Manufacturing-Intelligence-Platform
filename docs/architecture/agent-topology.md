# Agent Topology

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
              v                    v                    v
        CV Pipeline              RAG             MCP Tools
                                   |
                  +----------------+----------------+
                  |                |                |
                  v                v                v
           Maintenance        Root Cause        Supplier
              Agent             Agent            Agent
                  |                |                |
                  +----------------+----------------+
                                   |
                                   v
                            Reporting Agent
```
