# TaskMaster Agent Orchestrator (Free‑Tier Edition)

## Overview

A zero-cost, hobby-scale autonomous task agent that:

- Accepts high-level instructions (e.g., “fetch AAPL, MSFT, GOOGL prices; compute 20‑day SMA; store in DB”)
- Decomposes them with LangChain + AutoGen planner
- Executes Alpha Vantage API calls (≤ 5 req/min, free tier)
- Persists results to local SQLite
- Returns JSON via a C# ASP.NET Core Web API
- Ships as a single Docker image deployable to a free Hugging Face Space
- Exposes Prometheus metrics for latency, success %, error %
- Includes a basic Grafana dashboard JSON

## Stack

- **LLM**: Mistral-7B-Instruct-v0.2 (Q4_K_M) via llama.cpp (CPU, 8GB RAM)
- **LangChain**: Python 3.11, Chroma in-memory
- **Planner**: AutoGen’s AssistantAgent
- **API**: C# ASP.NET Core 8 minimal API
- **Storage**: SQLite file in container volume
- **Container**: Multi-stage Dockerfile
- **Deploy**: Hugging Face Space (CPU basic tier)
- **Observability**: Prometheus, Grafana
- **CI/CD**: GitHub Actions

## Milestones

1. Scaffold repo & CI skeleton
2. Python agent working locally
3. C# wrapper returns static JSON
4. Wire agent → API
5. Prometheus metrics
6. Dockerfile multi-stage build
7. HF Space deploy via CI
8. Grafana dashboard JSON
9. README with setup & limits

## Directory Structure

```
.
├── agent/
│   ├── requirements.txt
│   ├── main.py
│   └── models/
├── src/
│   └── TaskMaster.Api/
├── dashboards/dashboard.json
├── Dockerfile
├── .github/workflows/deploy.yml
└── README.md
```
