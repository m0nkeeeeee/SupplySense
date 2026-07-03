# SupplySense Agent Network

A production-ready, multi-agent AI platform for supply chain operations — built for the **MongoDB & Accenture Agentic AI Hackathon**.

Ask it natural-language questions like *"Which SKUs are below reorder point, and what should we do about it?"* and a team of specialist LangGraph agents (Planner, Inventory, Shipment, Knowledge, Risk, Recommendation, Report) gathers live data from MongoDB Atlas, reasons over it with Amazon Bedrock, retrieves grounded policy context via Voyage AI embeddings + Atlas Vector Search, and returns a synthesized answer with prioritized recommendations.

---

## Architecture

```
┌─────────────┐      ┌──────────────────────────────────────────────────┐
│   React UI  │◄────►│                   FastAPI Backend                 │
│ (Vite+Tail) │ HTTP │                                                    │
└─────────────┘      │   ┌─────────────────────────────────────────┐    │
                      │   │           LangGraph Agent Graph          │    │
                      │   │                                           │    │
                      │   │   Planner ──┬──► Inventory ──┐            │    │
                      │   │             ├──► Shipment  ──┤            │    │
                      │   │             ├──► Knowledge ──┼──► Recommendation ──► Report │
                      │   │             └──► Risk      ──┘            │    │
                      │   └─────────────────────────────────────────┘    │
                      │                                                    │
                      │   Amazon Bedrock (Claude)   Voyage AI Embeddings   │
                      └─────────────────────┬──────────────────────────────┘
                                             │
                                   ┌─────────▼─────────┐
                                   │   MongoDB Atlas    │
                                   │ (data + vector idx)│
                                   └─────────────────────┘
```

### Agents

| Agent | Responsibility |
|---|---|
| **Planner** | Reads the user's request and decides which specialist agents to invoke, and in what order. |
| **Inventory** | Queries live stock levels, flags SKUs at/below reorder point and safety stock. |
| **Shipment** | Tracks shipments, flags delays and customs holds. |
| **Knowledge** | Retrieval-augmented generation over SOPs/contracts/customs rules via MongoDB Atlas Vector Search + Voyage AI embeddings. |
| **Risk** | Synthesizes upstream findings into categorized, severity-scored risk events; persists them. |
| **Recommendation** | Synthesizes everything into the final answer plus prioritized, actionable recommendations. |
| **Report** | Compiles a structured report document (only runs if the user asks for a report/export); exportable as PDF. |

---

## Tech Stack

- **Backend:** Python 3.12, FastAPI, LangGraph, Motor (async MongoDB driver)
- **Database:** MongoDB Atlas (collections + Atlas Vector Search)
- **AI:** Amazon Bedrock (Claude via Converse API), Voyage AI embeddings
- **Frontend:** React 18, Vite, Tailwind CSS, Recharts, React Router
- **Infra:** Docker, Docker Compose

---

## Project Structure

```
SupplySense-Agent-Network/
├── backend/
│   ├── app/
│   │   ├── agents/            # Planner, Inventory, Shipment, Knowledge, Risk, Recommendation, Report + LangGraph wiring
│   │   ├── routers/           # FastAPI route handlers
│   │   ├── services/          # Bedrock client, Voyage client, vector-search retrieval
│   │   ├── models/            # Pydantic schemas
│   │   ├── utils/             # Structured logging
│   │   ├── config.py          # Environment-driven settings
│   │   ├── database.py        # MongoDB connection + indexes
│   │   └── main.py            # FastAPI app entrypoint
│   ├── scripts/
│   │   ├── seed_data.py            # Populates demo inventory/shipments/suppliers/risks/knowledge base
│   │   └── create_vector_index.py  # Provisions the Atlas Vector Search index
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/              # Dashboard, Copilot, Inventory, Shipments, Risks, Reports
│   │   ├── components/         # Sidebar, Topbar, Panel, Badge, AgentPipeline
│   │   └── api/client.js       # Axios API client
│   ├── package.json
│   ├── Dockerfile
│   └── .env.example
├── docker-compose.yml
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+
- A MongoDB Atlas cluster (M10+ recommended for Atlas Vector Search; a free M0 tier works for everything except vector search, which falls back to regex search automatically)
- AWS account with Amazon Bedrock model access enabled (e.g. `anthropic.claude-3-5-sonnet-20241022-v2:0`)
- A Voyage AI API key ([voyageai.com](https://www.voyageai.com))
- Docker + Docker Compose (optional, for containerized run)

### 1. Configure environment variables

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Edit `backend/.env` and fill in:
- `MONGODB_URI` — your Atlas connection string
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_REGION` — Bedrock credentials
- `VOYAGE_API_KEY` — Voyage AI key

### 2. Run locally (without Docker)

**Backend:**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m scripts.create_vector_index   # provisions Atlas Vector Search index (idempotent)
python -m scripts.seed_data             # populates demo data
uvicorn app.main:app --reload
```
Backend runs at `http://localhost:8000` (docs at `/docs`).

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at `http://localhost:5173`.

### 3. Run with Docker Compose

```bash
docker compose up --build
```

This starts the backend (port 8000) and frontend (port 5173). To use a local MongoDB instead of Atlas during development:

```bash
docker compose --profile local-mongo up --build
```
...and set `MONGODB_URI=mongodb://mongo:27017` in `backend/.env`.

After the stack is up, seed demo data:
```bash
docker compose exec backend python -m scripts.create_vector_index
docker compose exec backend python -m scripts.seed_data
```

---

## API Overview

All routes are prefixed with `/api/v1`.

| Method | Path | Description |
|---|---|---|
| `POST` | `/chat` | Send a message to the multi-agent copilot |
| `GET` | `/chat/sessions/{id}` | Retrieve a chat session's history |
| `GET` | `/inventory` | List inventory items |
| `POST` | `/inventory` | Upsert an inventory item |
| `GET` | `/shipments` | List shipments |
| `POST` | `/shipments` | Upsert a shipment |
| `GET` | `/risks` | List logged risk events |
| `GET` | `/recommendations` | List generated recommendations |
| `GET` | `/reports` | List generated reports |
| `GET` | `/reports/{id}/pdf` | Export a report as PDF |
| `POST` | `/knowledge/ingest` | Ingest a knowledge document (embedded via Voyage AI) |
| `GET` | `/knowledge/search` | Semantic search over the knowledge base |
| `GET` | `/health` | Service health check |

Full interactive docs: `http://localhost:8000/docs`.

---

## How the Agent Graph Works

1. A user message hits `POST /api/v1/chat`.
2. The **Planner** agent calls Bedrock to decide which specialist agents are needed and in what order (e.g. `["inventory", "shipment", "risk", "recommendation"]`).
3. LangGraph's conditional routing dispatches to each agent in `remaining_agents` in sequence. Each agent reads/writes a shared `CopilotState` and pops itself off the remaining list.
4. **Inventory** / **Shipment** / **Knowledge** agents gather grounded data from MongoDB (and, for Knowledge, Atlas Vector Search).
5. **Risk** synthesizes upstream findings into severity-scored risk events and persists new ones.
6. **Recommendation** synthesizes everything into the final answer and prioritized action items.
7. **Report** (only if requested) compiles a structured, persisted, PDF-exportable report.
8. The full trace, plan, recommendations, and risk events are returned to the frontend and rendered live in the Agent Network UI's agent pipeline visualization.

---

## Additional Documentation

- `PRESENTATION.md` — Hackathon-ready briefing with hero feature, novelty, customer relevance, data descriptions, assumptions, architecture, and block diagram.

## Production Notes

- **Secrets:** never commit `.env`. Use your cloud provider's secrets manager in production (AWS Secrets Manager, etc.).
- **Atlas Vector Search:** requires an Atlas cluster with Search enabled. If unavailable, the Knowledge Agent automatically falls back to a regex-based text search so the rest of the system keeps working.
- **Bedrock model access:** you must explicitly request model access for your chosen model ID in the AWS Bedrock console before first use.
- **Scaling:** the FastAPI app is stateless aside from MongoDB; scale horizontally behind a load balancer. LangGraph's `recursion_limit` and the app's `AGENT_MAX_ITERATIONS` guard against runaway agent loops.

---

## License

Built for the MongoDB & Accenture Agentic AI Hackathon. Provided as-is for demonstration and educational purposes.
