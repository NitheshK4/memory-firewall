# Memory Firewall Examples & Integration Recipes

This directory contains standalone Python scripts demonstrating how to integrate Memory Firewall with AI agent frameworks, RAG pipelines, and conversational memory stores.

---

## Available Recipes

### 1. `quickstart.py`
The fastest way to test Memory Firewall in Python without external services. Demonstrates initializing the write pipeline, assessing risk, running heuristic claim extraction, and storing verified memories.

```bash
python examples/quickstart.py
```

### 2. `langchain_agent_firewall.py`
Demonstrates wrapping LangChain agent conversation history and tool traces to intercept indirect prompt injections and unauthorized policy override attempts before they enter long-term storage.

```bash
python examples/langchain_agent_firewall.py
```

### 3. `llamaindex_rag_firewall.py`
Demonstrates document ingestion guardrails and retrieval context sanitization for RAG knowledge bases, preventing malicious file uploads from poisoning context windows.

```bash
python examples/llamaindex_rag_firewall.py
```
