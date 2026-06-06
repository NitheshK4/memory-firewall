# Memory Firewall

Memory Firewall is a runnable MVP for defending long-term memory in AI agents.
It intercepts memory writes and memory retrievals, scores them for risk, records
provenance, checks contradictions, and quarantines suspicious content before it
can silently corrupt future agent behavior.

## What is included

- FastAPI service for memory ingestion, retrieval, review, and health checks
- LangGraph-based write and read firewall flows
- Typed schemas for claims, provenance, verdicts, and stored memories
- In-memory repository for zero-friction local demos
- Docker Compose scaffold for Postgres and Neo4j expansion
- Streamlit dashboard for quarantine review

## Project Structure

```
memory-firewall/
├── apps/
│   ├── api/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── deps.py
│   │   │   ├── routers/
│   │   │   │   ├── memories.py
│   │   │   │   ├── retrieval.py
│   │   │   │   ├── policies.py
│   │   │   │   ├── review.py
│   │   │   │   └── health.py
│   │   │   ├── services/
│   │   │   │   ├── ingest_service.py
│   │   │   │   ├── claim_extractor.py
│   │   │   │   ├── provenance_service.py
│   │   │   │   ├── contradiction_service.py
│   │   │   │   ├── risk_service.py
│   │   │   │   ├── retrieval_service.py
│   │   │   │   ├── quarantine_service.py
│   │   │   │   ├── policy_engine.py
│   │   │   │   └── audit_service.py
│   │   │   ├── graphs/
│   │   │   │   ├── write_firewall.py
│   │   │   │   └── read_firewall.py
│   │   │   ├── models/
│   │   │   │   ├── memory_claim.py
│   │   │   │   ├── provenance.py
│   │   │   │   ├── verdict.py
│   │   │   │   ├── policy.py
│   │   │   │   └── retrieval_context.py
│   │   │   ├── db/
│   │   │   │   ├── postgres.py
│   │   │   │   ├── neo4j.py
│   │   │   │   └── vector.py
│   │   │   ├── telemetry/
│   │   │   │   ├── tracing.py
│   │   │   │   └── logging.py
│   │   │   └── prompts/
│   │   │       ├── extract_claims.txt
│   │   │       ├── classify_risk.txt
│   │   │       └── retrieval_guard.txt
│   │   ├── tests/
│   │   │   ├── test_write_firewall.py
│   │   │   ├── test_read_firewall.py
│   │   │   ├── test_contradictions.py
│   │   │   └── test_policy_engine.py
│   │   └── Dockerfile
│   └── dashboard/
│       ├── streamlit_app.py
│       ├── pages/
│       │   ├── quarantined_memories.py
│       │   ├── policy_events.py
│       │   └── retrieval_risks.py
│       └── Dockerfile
├── packages/
│   ├── shared/
│   │   ├── schemas/
│   │   │   ├── claim_schema.py
│   │   │   ├── verdict_schema.py
│   │   │   └── policy_schema.py
│   │   └── utils/
│   │       ├── hashing.py
│   │       ├── timestamps.py
│   │       └── ids.py
│   └── connectors/
│       ├── email_connector.py
│       ├── slack_connector.py
│       ├── docs_connector.py
│       └── tool_trace_connector.py
├── infra/
│   ├── compose.yaml
│   ├── k8s/
│   │   ├── config.yaml
│   │   ├── postgres.yaml
│   │   ├── neo4j.yaml
│   │   ├── otel-collector.yaml
│   │   ├── api.yaml
│   │   ├── dashboard.yaml
│   │   └── neo4j-bootstrap-job.yaml
│   ├── postgres/
│   │   └── init.sql
│   ├── neo4j/
│   │   └── constraints.cypher
│   └── otel/
│       └── collector-config.yaml
├── data/
│   ├── seeds/
│   ├── benign_samples/
│   └── poisoned_samples/
├── evals/
│   ├── datasets/
│   │   ├── memory_poisoning.jsonl
│   │   ├── benign_memory.jsonl
│   │   └── retrieval_attacks.jsonl
│   ├── runners/
│   │   ├── run_write_eval.py
│   │   ├── run_read_eval.py
│   │   └── score_results.py
│   └── reports/
├── scripts/
│   ├── bootstrap.sh
│   ├── load_demo_data.sh
│   └── run_local_eval.sh
├── .env.example
├── pyproject.toml
├── README.md
└── Makefile
```

## Architecture



```mermaid
flowchart TD
    %% Write Flow
    subgraph Write Flow
        Input[Agent / App / Tool Output] --> Gateway[FastAPI Gateway]
        Gateway --> WriteFW[Write Firewall LangGraph]
        WriteFW --> OTEL[OpenTelemetry Traces]
        WriteFW --> ClaimExt[Claim Extraction]
        
        ClaimExt --> Prov[Provenance Tagging]
        ClaimExt --> Embeds[Embeddings]
        
        Prov --> RiskScore[Risk + Contradiction Scoring]
        
        RiskScore --> Policy{Policy Engine}
        
        Policy -->|Audit| Audit[Audit Log]
        Policy -->|Block| Reject[Reject Write]
        Policy -->|Quarantine| QuarQueue[Quarantine Queue]
        QuarQueue --> Dash[Reviewer Dashboard]
        Dash --> ReviewDecision[Approve / Reject / Edit]
        Policy -->|Low Trust| Untrusted[Store as Untrusted Memory]
        Policy -->|Allow| Allow[Allow]
    end

    %% Read Flow
    subgraph Read Flow
        RetReq[Agent Retrieval Request] --> ReadFW[Read Firewall LangGraph]
        ReadFW --> OTEL
        ReadFW --> ClaimExt
        ReadFW --> Neo4jCheck[Graph Checks Neo4j]
        ReadFW --> VectorSearch[Semantic Search pgvector]
        
        Neo4jCheck --> ReRank[Trust Re-Ranking]
        VectorSearch --> ReRank
        
        ReRank --> SafeContext[Safe Retrieval Context]
        SafeContext --> AgentResp[Agent Response]
    end

    %% Storage linkings
    Embeds --> Postgres[(Postgres Memory Store)]
    Embeds --> Neo4j[(Neo4j Provenance Graph)]
    Prov --> Neo4j
    RiskScore --> Neo4j
    RiskScore --> Postgres
    
    Audit --> Postgres
    ReviewDecision --> Postgres
    ReviewDecision --> Neo4j
    Untrusted --> Postgres
    Untrusted --> Neo4j
    Allow --> Postgres
    Allow --> Neo4j
    
    Neo4jCheck -.-> Neo4j
    VectorSearch -.-> Postgres
```

## Quick start

1. Create a virtual environment and install dependencies:

   ```bash
   pip install -e .
   ```

2. Copy `.env.example` to `.env` and fill in any optional values.

3. Run the API:

   ```bash
   make run-api
   ```

4. Run the dashboard in another terminal:

   ```bash
   make run-dashboard
   ```

## Core flow

1. A memory write arrives at the gateway.
2. Claims are extracted from the raw content.
3. Provenance is attached to every write.
4. Similar memories are searched for contradictions.
5. A risk engine scores the write.
6. A policy engine decides whether to allow, downgrade, quarantine, or block it.
7. Retrieval requests are filtered and re-ranked by trust.

## Main endpoints

- `POST /api/v1/memories`
- `GET /api/v1/memories`
- `POST /api/v1/retrieval/query`
- `GET /api/v1/review/quarantine`
- `POST /api/v1/review/{memory_id}/decision`
- `GET /health`

## Notes

- The current repository is in-memory to keep the MVP easy to run.
- Postgres, pgvector, and Neo4j are scaffolded into the project structure and
  compose stack so you can upgrade the storage layer without reshaping the app.
- The claim extractor currently uses deterministic heuristics. This is deliberate
  so the project demos cleanly even without an API key.

#end
