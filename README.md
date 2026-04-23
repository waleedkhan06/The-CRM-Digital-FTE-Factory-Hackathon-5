# 🏭 Customer Success Digital FTE — AI-Powered 24/7 Support Agent

> **Hackathon:** The CRM Digital FTE Factory Final Hackathon 5
> **Team:** 1 Student | **Status:** Production-Ready
> **Score Target:** 100/100 Points

---

## 📋 Overview

A production-grade **omnichannel AI customer support agent** (Digital Full-Time Equivalent) that replaces a $75,000/year human FTE with a < $1,000/year autonomous system. Handles customer inquiries across **Email (Gmail)**, **WhatsApp (Twilio)**, and **Web Form** — 24/7, without breaks.

### Key Capabilities

| Feature | Description |
|---------|-------------|
| 🤖 **AI-Powered Responses** | Uses OpenAI GPT-4o to understand and respond to customer queries |
| 📧 **Email Channel** | Receives and replies via Gmail API with Pub/Sub notifications |
| 📱 **WhatsApp Channel** | Receives and replies via Twilio WhatsApp API |
| 💬 **Web Support Form** | Beautiful Next.js form with real-time validation and ticket tracking |
| 🧠 **Smart Escalation** | Automatically detects when human intervention is needed |
| 📊 **Sentiment Analysis** | Monitors customer emotions in real-time |
| 🔄 **Cross-Channel Memory** | Recognizes customers across all channels with unified history |
| 🗄️ **Built-in CRM** | PostgreSQL-based customer, ticket, and conversation tracking |
| ⚡ **Event Streaming** | Kafka-powered message queue for reliable processing |
| 🚀 **Kubernetes Ready** | Full K8s manifests with auto-scaling (HPA) |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     MULTI-CHANNEL INTAKE LAYER                       │
│                                                                      │
│  ┌──────────┐    ┌───────────┐    ┌──────────────┐                 │
│  │  Gmail   │    │ WhatsApp  │    │  Web Form    │                 │
│  │   API    │    │  Twilio   │    │  (Next.js)   │                 │
│  └────┬─────┘    └─────┬─────┘    └──────┬───────┘                 │
│       │                │                  │                          │
│       ▼                ▼                  ▼                          │
│  ┌─────────────────────────────────────────────────┐                │
│  │              FastAPI Webhook Endpoints           │                │
│  │  /webhooks/gmail  /webhooks/whatsapp  /support  │                │
│  └──────────────────────┬──────────────────────────┘                │
│                         │                                             │
│                         ▼                                             │
│              ┌─────────────────────┐                                 │
│              │   Kafka (Events)    │                                 │
│              │  fte.tickets.incoming │                                │
│              └──────────┬──────────┘                                 │
│                         │                                             │
│              ┌──────────▼──────────┐                                 │
│              │  Message Processor  │                                 │
│              │     Worker          │                                 │
│              └──────────┬──────────┘                                 │
│                         │                                             │
│              ┌──────────▼──────────┐                                 │
│              │  OpenAI GPT-4o      │                                 │
│              │  Customer Success   │                                 │
│              │       Agent         │                                 │
│              └──────────┬──────────┘                                 │
│                         │                                             │
│              ┌──────────▼──────────┐                                 │
│              │  PostgreSQL (CRM)   │                                 │
│              │  Customers, Tickets │                                 │
│              │  Messages, KB       │                                 │
│              └─────────────────────┘                                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL 16 (or Docker)
- Apache Kafka (or Docker)

### 1. Clone & Install Backend

```bash
cd "The CRM Digital FTE Factory Hackathon 5"

# Install Python dependencies
pip install -r production/requirements.txt

# Or individually:
pip install fastapi uvicorn pydantic[email] asyncpg aiokafka openai
pip install google-api-python-client twilio python-multipart
```

### 2. Configure Environment

```bash
# Copy and edit .env
cp .env.example .env

# Fill in your credentials (see Setup Guide below)
```

### 3. Start Backend

```bash
# Option A: With Docker (recommended)
docker compose up -d

# Option B: Direct Python (no Docker)
python3 -m uvicorn production.api.main:app --host 0.0.0.0 --port 8000
```

### 4. Start Frontend

```bash
cd web-form
npm install
npm run dev
```

### 5. Access

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:3000 |
| **API Server** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |
| **Health Check** | http://localhost:8000/health |

---

## 🔧 Setup Guide — Getting Credentials

### PostgreSQL Database

**Option A: Supabase (Free, 2 min)**
1. Go to [supabase.com](https://supabase.com) → New Project
2. Copy: Host, Database, User, Password
3. Run `production/database/schema.sql` in the SQL editor

**Option B: Local Docker**
```bash
docker run -d --name fte-postgres \
  -e POSTGRES_PASSWORD=fte_password \
  -e POSTGRES_DB=fte_db \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

### Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create project → Enable **Gmail API**
3. **Credentials** → Create **Service Account** (NOT OAuth Client ID)
4. Download JSON key → Save as `credentials/gmail-credentials.json`
5. In Gmail Settings → Enable IMAP → Delegate access to service account email

### Twilio WhatsApp

1. Go to [Twilio Console](https://console.twilio.com)
2. Sign up → Messaging → Try it Out → Send a WhatsApp message
3. Copy: Account SID, Auth Token, WhatsApp Sandbox number
4. Send the sandbox code from your WhatsApp to activate

### OpenAI API Key

1. Go to [platform.openai.com](https://platform.openai.com)
2. Dashboard → API Keys → Create new secret key
3. Copy and set as `OPENAI_API_KEY` in `.env`

---

## 📁 Project Structure

```
crm-digital-fte-factory/
│
├── context/                          # Incubation context files
│   ├── company-profile.md            # TechCorp company details
│   ├── product-docs.md               # Product documentation
│   ├── sample-tickets.json           # 55 sample customer tickets
│   ├── escalation-rules.md           # Escalation decision rules
│   └── brand-voice.md                # Communication guidelines
│
├── specs/                            # Requirements & specifications
│   ├── discovery-log.md              # Requirements discovered
│   ├── customer-success-fte-spec.md  # Full system specification
│   └── transition-checklist.md       # General → Custom Agent checklist
│
├── incubation/                       # Phase 1: Prototype
│   ├── prototype.py                  # Core interaction loop
│   ├── memory_manager.py             # Conversation state management
│   ├── mcp_server.py                 # MCP server with 7 tools
│   └── agent_skills.py               # 5 skill definitions
│
├── production/                       # Phase 2: Production system
│   ├── agent/                        # AI agent definition
│   │   ├── customer_success_agent.py # Main agent (OpenAI SDK + fallback)
│   │   ├── tools.py                  # 7 production tools
│   │   ├── prompts.py                # System prompts
│   │   └── formatters.py             # Channel formatting
│   ├── channels/                     # Channel integrations
│   │   ├── gmail_handler.py          # Gmail API integration
│   │   ├── whatsapp_handler.py       # Twilio WhatsApp integration
│   │   └── web_form_handler.py       # FastAPI web form endpoints
│   ├── workers/                      # Background workers
│   │   └── message_processor.py      # Kafka consumer + agent runner
│   ├── api/                          # API layer
│   │   └── main.py                   # FastAPI (16 endpoints)
│   ├── database/                     # Database
│   │   ├── schema.sql                # PostgreSQL schema (9 tables)
│   │   └── queries.py                # Async database queries
│   ├── kafka_client.py               # Kafka producer/consumer
│   ├── config.py                     # Configuration management
│   └── requirements.txt              # Python dependencies
│
├── web-form/                         # Phase 2: Next.js frontend
│   ├── app/                          # Next.js App Router
│   │   ├── page.tsx                  # Landing page + routing
│   │   ├── layout.tsx                # Root layout + SEO
│   │   └── globals.css               # Custom design system
│   ├── components/
│   │   ├── SupportForm.tsx           # Main support form
│   │   ├── TicketStatus.tsx          # Ticket status checker
│   │   ├── Header.tsx                # Premium header
│   │   └── AnimatedBackground.tsx    # Particle network background
│   └── lib/utils.ts                  # Utility functions
│
├── k8s/                              # Phase 2: Kubernetes manifests
│   ├── namespace.yaml                # Namespace definition
│   ├── configmap.yaml                # Environment config
│   ├── secrets.yaml                  # Sensitive credentials
│   ├── deployment-api.yaml           # API deployment (3 replicas)
│   ├── deployment-worker.yaml        # Worker deployment (3 replicas)
│   ├── service.yaml                  # ClusterIP service
│   ├── ingress.yaml                  # Ingress with TLS
│   └── hpa.yaml                      # Auto-scaling (3-20 / 3-30)
│
├── tests/                            # Phase 3: Testing
│   ├── test_e2e.py                   # End-to-end multi-channel tests
│   └── load_test.py                  # Locust load tests
│
├── Dockerfile                        # Multi-stage Docker build
├── docker-compose.yml                # Local dev stack
├── .env                              # Environment variables
└── README.md                         # This file
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check (K8s liveness probe) |
| `GET` | `/health/ready` | Readiness check (K8s readiness probe) |
| `POST` | `/support/submit` | Submit web support form |
| `GET` | `/support/ticket/{id}` | Check ticket status |
| `GET` | `/support/ticket/{id}/messages` | Get ticket conversation |
| `POST` | `/webhooks/gmail` | Gmail Pub/Sub webhook |
| `POST` | `/webhooks/whatsapp` | Twilio WhatsApp webhook |
| `POST` | `/webhooks/whatsapp/status` | WhatsApp delivery status |
| `GET` | `/conversations/{id}` | Full conversation history |
| `GET` | `/customers/lookup` | Customer lookup by email/phone |
| `GET` | `/metrics/channels` | Channel performance metrics |
| `POST` | `/agent/process` | Manual agent processing trigger |

---

## 📊 Database Schema

| Table | Purpose | Key Columns |
|-------|---------|------------|
| `customers` | Unified customer database | id, email, phone, name, avg_sentiment |
| `customer_identifiers` | Cross-channel identity | customer_id, type, value |
| `conversations` | Conversation threads | id, customer_id, initial_channel, status |
| `messages` | Individual messages | id, conversation_id, channel, role, content |
| `tickets` | Support ticket lifecycle | id, conversation_id, source_channel, status |
| `knowledge_base` | Product docs with vectors | id, title, content, category, keywords |
| `channel_configs` | Per-channel settings | channel, config, max_response_length |
| `agent_metrics` | Performance tracking | metric_name, metric_value, channel |
| `escalations` | Human escalations | ticket_id, reason, priority, route_to |

---

## 🎯 Scoring Rubric Coverage

| Criteria | Points | Status |
|----------|--------|--------|
| Incubation Quality | 10 | ✅ Discovery log, patterns found |
| Agent Implementation | 10 | ✅ 7 tools, channel-aware, error handling |
| Web Support Form | 10 | ✅ Complete React UI with validation |
| Channel Integrations | 10 | ✅ Gmail + WhatsApp + Web Form |
| Database & Kafka | 5 | ✅ 9 tables, event streaming |
| Kubernetes Deployment | 5 | ✅ 8 manifests, HPA, health checks |
| 24/7 Readiness | 10 | ✅ Stateless, auto-scaling, no SPOF |
| Cross-Channel Continuity | 10 | ✅ Customer ID across channels |
| Monitoring | 5 | ✅ Channel metrics, sentiment alerts |
| Customer Experience | 10 | ✅ Channel responses, escalation, sentiment |
| Documentation | 5 | ✅ README, API docs, runbook |
| Creative Solutions | 5 | ✅ Particle UI, glass morphism, animations |
| Evolution Demonstration | 5 | ✅ Clear incubation → production path |
| **TOTAL** | **100** | |

---

## 🧪 Testing

### Run All Tests

```bash
# Unit + E2E tests
pytest tests/ -v

# Load testing
locust -f tests/load_test.py --host=http://localhost:8000
```

### Manual Testing

1. **Web Form:** Go to `localhost:3000` → Submit a request → Track ticket
2. **API:** Go to `localhost:8000/docs` → Test any endpoint
3. **Agent:** POST `/agent/process` with a customer message

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [Discovery Log](specs/discovery-log.md) | Requirements found during incubation |
| [System Spec](specs/customer-success-fte-spec.md) | Full technical specification |
| [Transition Checklist](specs/transition-checklist.md) | General → Custom Agent checklist |
| [Escalation Rules](context/escalation-rules.md) | When to involve humans |
| [Brand Voice](context/brand-voice.md) | Communication guidelines |

---

## 🚀 Deployment

### Local Development
```bash
docker compose up -d
cd web-form && npm run dev
```

### Kubernetes Production
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployment-api.yaml
kubectl apply -f k8s/deployment-worker.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml
```

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| **AI Agent** | OpenAI GPT-4o + Agents SDK (with fallback prototype) |
| **API** | FastAPI (Python 3.12) |
| **Database/CRM** | PostgreSQL 16 + pgvector |
| **Event Streaming** | Apache Kafka (aiokafka) |
| **Frontend** | Next.js 16 + React 19 + Tailwind CSS 4 + Framer Motion |
| **Email** | Gmail API + Google Cloud Pub/Sub |
| **WhatsApp** | Twilio WhatsApp API |
| **Containerization** | Docker (multi-stage build) |
| **Orchestration** | Kubernetes + HPA |
| **Testing** | pytest + Locust |

---

## 📝 License

Built for The CRM Digital FTE Factory Final Hackathon 5

---

> **"Welcome to the future of customer support. Now build it."**
