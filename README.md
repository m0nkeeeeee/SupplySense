# SupplySense Agent Network

> **An AI-powered Multi-Agent Supply Chain Assistant built for the MongoDB × Accenture Agentic AI Hackathon (July 2026).**

SupplySense Agent Network is a production-inspired multi-agent AI platform that helps organizations monitor inventory, track shipments, identify operational risks, retrieve business knowledge, and generate actionable recommendations through natural language conversations.

Instead of switching between multiple dashboards and reports, users can simply ask questions like:

> *"Which products are below their reorder level?"*

> *"Are there any delayed shipments that could affect production?"*

> *"Generate a report summarizing current supply chain risks."*

The system automatically coordinates multiple AI agents to analyze live operational data and return a complete business-ready response.

---

# ✨ Features

* 🤖 Multi-Agent AI Architecture
* 📦 Inventory Monitoring
* 🚚 Shipment Tracking
* 📚 Knowledge Base Search using MongoDB Atlas Vector Search
* ⚠️ Risk Detection & Analysis
* 💡 AI-generated Recommendations
* 📄 Automated Report Generation
* 📊 Interactive Dashboard
* 💬 Conversational AI Chat Interface

---


# Screenshots
<img width="785" height="400" alt="image" src="https://github.com/user-attachments/assets/bb05a270-bbc2-4a5c-a2ae-f8a2af5f056f" />
<img width="1560" height="765" alt="image" src="https://github.com/user-attachments/assets/a1ab42b5-c804-4194-824a-120e29f1dee0" />
<img width="604" height="284" alt="image" src="https://github.com/user-attachments/assets/770dc255-ec39-4e01-b5a0-0ba025f586c8" />
<img width="722" height="413" alt="image" src="https://github.com/user-attachments/assets/29591bd3-4048-44ef-8c69-661aa3862051" />
<img width="779" height="404" alt="image" src="https://github.com/user-attachments/assets/8561cd42-2346-4a37-b4f6-4c7c252e8e34" />
<img width="782" height="400" alt="image" src="https://github.com/user-attachments/assets/beb56258-f361-4f90-a3ff-e4f2f2117d2f" />
<img width="780" height="401" alt="image" src="https://github.com/user-attachments/assets/0f654f04-40e0-475e-991b-59481d00e30e" />








# 🏗 Architecture

```
User
   │
   ▼
Planner Agent
   │
   ├── Inventory Agent
   ├── Shipment Agent
   ├── Knowledge Agent
   ├── Risk Agent
   ▼
Recommendation Agent
   │
   ▼
Report Agent (Optional)
```

Each agent performs one specialized task and shares its findings with the Recommendation Agent, which produces the final response.

---

# 🧠 Why Multi-Agent AI?

Traditional chatbots rely on a single model to answer every question.

SupplySense instead uses **specialized AI agents**, each responsible for a different aspect of the supply chain.

This results in:

* Better reasoning
* More reliable responses
* Easier scalability
* Explainable AI workflows

---

# ⚙ Tech Stack

## Frontend

* React
* Vite
* Tailwind CSS
* Recharts

## Backend

* FastAPI
* Python
* LangGraph

## AI

* Amazon Bedrock (Claude)
* Voyage AI Embeddings

## Database

* MongoDB Atlas
* MongoDB Atlas Vector Search

## DevOps

* Docker
* Docker Compose

---

# 📂 Project Structure

```
SupplySense-Agent-Network

backend/
frontend/
docker-compose.yml
README.md
```

---

# 🚀 Getting Started

## 1. Clone the repository

```bash
git clone https://github.com/yourusername/SupplySense-Agent-Network.git

cd SupplySense-Agent-Network
```

---

## 2. Backend Setup

```bash
cd backend

python -m venv venv

# Windows
venv\Scripts\activate

# Linux / Mac
source venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file and configure:

```
MONGODB_URI=

AWS_ACCESS_KEY_ID=

AWS_SECRET_ACCESS_KEY=

AWS_REGION=

VOYAGE_API_KEY=
```

Run the backend:

```bash
uvicorn app.main:app --reload
```

Backend runs on

```
http://localhost:8000
```

---

## 3. Frontend Setup

```bash
cd frontend

npm install

npm run dev
```

Frontend runs on

```
http://localhost:5173
```

---

# 🐳 Run with Docker

```bash
docker compose up --build
```

---

# 💬 Example Questions

* Which inventory items need replenishment?
* Show delayed shipments.
* Are there any high-risk suppliers?
* Generate a supply chain report.
* What products are below the safety stock level?

---

# 🎯 Use Cases

* Inventory Management
* Supply Chain Monitoring
* Procurement
* Logistics
* Risk Analysis
* Executive Reporting

---

# 📖 Future Improvements

* Real-time ERP integration
* Supplier performance analytics
* Demand forecasting
* Predictive inventory planning
* Notification & alert system
* Voice-enabled AI assistant

---

# 👨‍💻 Team

Built during the **MongoDB × Accenture Agentic AI Hackathon (July 2026)**.

---

# ⭐ If you found this project interesting, don't forget to star the repository!
