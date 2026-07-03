# SupplySense Agent Network — Hackathon Presentation Brief

## Hero Feature

- **Multi-Agent Orchestration for Supply Chain Resilience**
- The app uses a Planner agent to dynamically route a natural language request through specialist agents for inventory, shipment, knowledge, risk, and recommendations.
- This design enables context-aware, grounded reasoning across live operations, external policy knowledge, and risk events in one cohesive workflow.

## Novelty

- **Dynamic agent routing** — Unlike single-model assistants, the Planner decides which specialist workflows are required for each question.
- **Specialist agent pipeline** — Inventory, Shipment, Knowledge, and Risk agents each inspect different operational layers and feed a final Recommendation agent.
- **Grounded retrieval + synthesis** — The Knowledge agent ingests policy and SOP documents into MongoDB Atlas with Voyage AI embeddings and returns evidence-backed context.
- **Report export** — The system is capable of generating structured, professional reports from the same multi-agent reasoning pipeline.

## Customer Relevance

- **Supply chain operators** want rapid decision support for stock shortages, delayed shipments, customs risk, and operational recommendations.
- **Logistics teams** need a single pane of glass for inventory health, shipment status, and compliance guidance.
- **Procurement and planning** benefit from prioritized action items, risk scoring, and executive-ready summaries.
- **Executives** can use the report feature to quickly capture AI-driven status insights and next steps.

## Data Descriptions

- **Inventory records**: SKU, warehouse, quantity, reorder point, safety stock, supplier, lead time.
- **Shipment records**: Shipment ID, origin, destination, carrier, expected arrival, status, customs hold, delay reason.
- **Knowledge documents**: SOPs, supplier contracts, customs policies, compliance guides, process playbooks.
- **Risk events**: Categorized incidents with severity tags, title, rationale, and affected SKUs or shipments.
- **Recommendations**: Actionable suggestions with priority labels and rationale.

## Assumptions

- Users want a conversational interface rather than manual dashboard queries.
- Real-world supply chains require reasoning across multiple data sources, not just one dataset.
- Safety and reliability demand grounded retrieval from documented policies and current operational data.
- Model hallucination risk is mitigated by using evidence from Atlas Vector Search and structured agent outputs.
- A multi-agent architecture improves explainability by showing the agent pipeline and trace.

## Solution Architecture

- **Frontend**: React + Vite + Tailwind drives a conversational UI and admin dashboards.
- **Backend**: FastAPI exposes the chat endpoint, data APIs, and PDF report export.
- **Agent Graph**: LangGraph coordinates a stateful pipeline of specialist agents.
- **AI Reasoning**: Amazon Bedrock Claude powers planning and synthesis.
- **Retrieval**: Voyage AI embeddings plus MongoDB Atlas Vector Search stores and queries knowledge documents.
- **Persistence**: MongoDB Atlas holds inventory, shipments, risks, recommendations, reports, and knowledge metadata.

## Architecture Block Diagram

```
                        +---------------------------------+
                        |     SupplySense Frontend       |
                        |  React UI, chat, dashboards     |
                        +---------------+----------------+
                                        |
                                        v
                        +---------------+----------------+
                        |      FastAPI Backend            |
                        | - /api/v1/chat                  |
                        | - /inventory, /shipments, etc.  |
                        +---------------+----------------+
                                        |
                                        v
                        +---------------+----------------+
                        |       LangGraph Agent Graph     |
                        |  Planner -> Inventory           |
                        |           -> Shipment           |
                        |           -> Knowledge          |
                        |           -> Risk               |
                        |           -> Recommendation     |
                        |           -> Report (optional)  |
                        +---------------+----------------+
                                        |
        +-------------------------------+-------------------------------+
        |                               |                               |
        v                               v                               v
+---------------+              +----------------------+        +-------------------------+
| Amazon Bedrock|              | MongoDB Atlas        |        | Voyage AI Embeddings     |
| (Claude)      |              | - inventory          |        | - semantic knowledge     |
|               |              | - shipments          |        |   embeddings             |
|               |              | - risks              |        +-------------------------+
|               |              | - recommendations    |
+---------------+              | - reports            |
                               +----------------------+
```

## Presentation Talking Points

1. **What it does**: Conversationally answers supply chain queries and generates executive reports using a multi-agent decision pipeline.
2. **Why it matters**: It turns fragmented operational data into actionable guidance and risk-aware decisions.
3. **Why it’s novel**: The Planner dynamically chooses specialist agents, and the Recommendation agent synthesizes grounded findings from live data and policy documents.
4. **Demo flow**: Ask for inventory shortages, track delayed shipments, evaluate customs risk, and export a report.
5. **Customer value**: Faster decisions, better risk visibility, reduced manual triage, and one unified AI-driven command center.

## Best Slide Headlines

- "SupplySense Agent Network: Conversational Supply Chain Orchestration"
- "AI-Driven Specialist Agents for Inventory, Shipment, Knowledge, Risk, and Recommendations"
- "Grounded Reasoning with MongoDB Atlas and Voyage AI Embeddings"
- "Executive Reports from the Same Multi-Agent Workflow"
- "Built for Real Operations, Not Just Chat"