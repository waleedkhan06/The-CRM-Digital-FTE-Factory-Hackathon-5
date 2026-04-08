# 🏭 Customer Success Digital FTE — Implementation Master Plan

> **Hackathon:** The CRM Digital FTE Factory Final Hackathon 5
> **Project:** Build a 24/7 AI Customer Support Employee (Full-Time Equivalent)
> **Duration:** 48-72 Development Hours | **Team:** 1 Student
> **Target:** Replace a $75,000/year human FTE with a < $1,000/year AI system

---

## 📋 Executive Summary

We are building a **production-grade omnichannel customer support AI agent** (Digital FTE) that:

- Accepts support tickets from **3 channels**: Gmail, WhatsApp (via Twilio), and a Web Support Form
- Uses AI (OpenAI GPT-4o via Agents SDK) to understand and respond to customer queries
- Tracks all interactions in a **PostgreSQL-based CRM/ticket system** (built by us)
- Uses **Kafka** for event streaming between components
- Deploys on **Kubernetes** with auto-scaling for 24/7 reliability
- Demonstrates the full **Agent Maturity Model**: from General Agent (incubation) to Custom Agent (production)

### Core Architecture Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     MULTI-CHANNEL INTAKE LAYER                       │
│                                                                      │
│  ┌──────────┐    ┌───────────┐    ┌──────────────┐                 │
│  │  Gmail   │    │ WhatsApp  │    │  Web Form    │                 │
│  │   API    │    │  Twilio   │    │  (React UI)  │                 │
│  └────┬─────┘    └─────┬─────┘    └──────┬───────┘                 │
│       │                │                  │                          │
│       ▼                ▼                  ▼                          │
│  ┌─────────────────────────────────────────────────┐                │
│  │              FastAPI Webhook Endpoints           │                │
│  └──────────────────────┬──────────────────────────┘                │
│                         │                                             │
│                         ▼                                             │
│              ┌─────────────────────┐                                 │
│              │   Kafka (Events)    │                                 │
│              │  fte.tickets.incoming │                                │
│              └──────────┬──────────┘                                 │
└─────────────────────────┼───────────────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────────────┐
│                    PROCESSING LAYER                                  │
│                         ▼                                             │
│              ┌─────────────────────┐                                 │
│              │  Message Processor  │                                 │
│              │   Worker (Kafka     │                                 │
│              │    Consumer)        │                                 │
│              └──────────┬──────────┘                                 │
│                         │                                             │
│                         ▼                                             │
│              ┌─────────────────────┐                                 │
│              │  OpenAI Agents SDK  │                                 │
│              │  Customer Success   │                                 │
│              │       Agent         │                                 │
│              └──────────┬──────────┘                                 │
│                         │                                             │
│            ┌────────────┼────────────┐                               │
│            ▼            ▼            ▼                               │
│     ┌──────────┐ ┌──────────┐ ┌──────────┐                          │
│     │PostgreSQL│ │Knowledge │ │Sentiment │                          │
│     │  (CRM)   │ │  Base    │ │ Analysis │                          │
│     └──────────┘ └──────────┘ └──────────┘                          │
└─────────────────────────┼───────────────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────────────┐
│                    RESPONSE LAYER                                    │
│                         ▼                                             │
│         ┌───────────────┼───────────────┐                            │
│         ▼               ▼               ▼                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐                         │
│  │  Gmail   │   │ Twilio   │   │  Email   │                         │
│  │  Send    │   │  Send    │   │  Notify  │                         │
│  └──────────┘   └──────────┘   └──────────┘                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Scoring Rubric (What We Must Achieve)

| Category | Points | What We Must Deliver |
|----------|--------|---------------------|
| **Incubation Quality** | 10 | Discovery log, iterative exploration, multi-channel patterns |
| **Agent Implementation** | 10 | All tools working, channel-aware responses, error handling |
| **Web Support Form** | 10 | Complete React/Next.js form with validation + status check |
| **Channel Integrations** | 10 | Gmail + WhatsApp handlers with webhook validation |
| **Database & Kafka** | 5 | Normalized schema, channel tracking, event streaming |
| **Kubernetes Deployment** | 5 | All manifests, multi-pod scaling, health checks |
| **24/7 Readiness** | 10 | Survives pod restarts, handles scaling, no SPOF |
| **Cross-Channel Continuity** | 10 | Customer identified across channels, history preserved |
| **Monitoring** | 5 | Channel-specific metrics, alerts configured |
| **Customer Experience** | 10 | Channel-appropriate responses, escalation, sentiment |
| **Documentation** | 5 | Deployment guide, API docs, form integration guide |
| **Creative Solutions** | 5 | Novel approaches, enhanced UX |
| **Evolution Demonstration** | 5 | Clear progression from incubation to specialization |
| **TOTAL** | **100** | |

---

## 📁 Final Project Structure

```
crm-digital-fte-factory/
│
├── context/                          # Incubation context files
│   ├── company-profile.md            # Fake SaaS company details
│   ├── product-docs.md               # Product documentation for AI answers
│   ├── sample-tickets.json           # 50+ sample customer inquiries
│   ├── escalation-rules.md           # When to involve humans
│   └── brand-voice.md                # Company communication style
│
├── specs/                            # Requirements & specifications
│   ├── discovery-log.md              # Requirements discovered during incubation
│   ├── customer-success-fte-spec.md  # Crystallized specification
│   └── transition-checklist.md       # General → Custom Agent transition checklist
│
├── incubation/                       # Phase 1: Prototype code
│   ├── prototype.py                  # Core interaction loop prototype
│   ├── mcp_server.py                 # MCP server with 5+ tools
│   ├── agent_skills.py               # Agent skills manifest
│   └── memory_manager.py             # Conversation memory & state
│
├── production/                       # Phase 2: Production-grade system
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── customer_success_agent.py # OpenAI Agents SDK agent definition
│   │   ├── tools.py                  # @function_tool decorated functions
│   │   ├── prompts.py                # System prompts (extracted from prototype)
│   │   └── formatters.py             # Channel-specific response formatting
│   │
│   ├── channels/
│   │   ├── __init__.py
│   │   ├── gmail_handler.py          # Gmail API integration
│   │   ├── whatsapp_handler.py       # Twilio/WhatsApp integration
│   │   └── web_form_handler.py       # Web form API endpoint
│   │
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── message_processor.py      # Kafka consumer + agent runner
│   │   └── metrics_collector.py      # Background metrics collection
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py                   # FastAPI application (all endpoints)
│   │
│   ├── database/
│   │   ├── schema.sql                # PostgreSQL schema (our CRM)
│   │   ├── migrations/               # Database migrations
│   │   └── queries.py                # Database access functions
│   │
│   ├── kafka_client.py               # Kafka producer/consumer utilities
│   ├── config.py                     # Configuration management
│   └── requirements.txt              # Python dependencies
│
├── web-form/                         # Phase 2: Web Support Form (REQUIRED)
│   ├── components/
│   │   └── SupportForm.jsx           # React component (complete UI)
│   ├── pages/
│   │   └── index.js                  # Next.js page with form
│   ├── package.json
│   └── tailwind.config.js
│
├── k8s/                              # Phase 2: Kubernetes manifests
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secrets.yaml
│   ├── deployment-api.yaml
│   ├── deployment-worker.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   └── hpa.yaml                      # Horizontal Pod Autoscaler
│
├── tests/                            # Phase 3: Testing
│   ├── test_agent.py                 # Agent unit tests
│   ├── test_channels.py              # Channel handler tests
│   ├── test_multichannel_e2e.py      # End-to-end multi-channel tests
│   └── load_test.py                  # Locust load tests
│
├── Dockerfile                        # Container definition
├── docker-compose.yml                # Local development stack
├── Makefile                          # Common commands
└── README.md                         # Project documentation
```

---

## 🔨 Phase 1: The Incubation Phase (Hours 1-16)

### Objective
Use Claude Code as the **Agent Factory** to explore the problem space, discover hidden requirements, and build a working prototype that handles customer queries from any channel.

### Step 1.1: Context Setup & Initial Exploration (Hours 1-3)

**Goal:** Create the "Development Dossier" — all context files Claude Code needs to understand the business.

**Tasks:**
1. Create `context/company-profile.md` — Fake SaaS company (TechCorp) details
2. Create `context/product-docs.md` — Product documentation for AI to answer from
3. Create `context/sample-tickets.json` — 50+ realistic sample customer inquiries across all 3 channels
4. Create `context/escalation-rules.md` — Rules for when to escalate to humans
5. Create `context/brand-voice.md` — How the company communicates
6. Run initial exploration with Claude Code to analyze sample tickets and identify patterns

**Deliverables:**
- ✅ All 5 context files created with rich, realistic content
- ✅ Pattern analysis results documented

---

### Step 1.2: Prototype Core Loop (Hours 4-8)

**Goal:** Build a simple Python prototype that handles the core customer interaction loop.

**Tasks:**
1. Build `incubation/prototype.py` — Core interaction loop:
   - Takes customer message as input (with channel metadata)
   - Normalizes message regardless of source channel
   - Searches product docs for relevant information
   - Generates helpful response
   - Formats response appropriately for the channel
   - Decides if escalation is needed
2. Add channel-specific response formatting (email = formal, WhatsApp = concise, web = semi-formal)
3. Add handling for edge cases: empty messages, pricing queries, angry customers
4. Test with sample tickets from context files

**Deliverables:**
- ✅ Working prototype handling basic queries
- ✅ Channel-aware response formatting
- ✅ Edge case handling documented

---

### Step 1.3: Memory & State Management (Hours 9-11)

**Goal:** Add conversation memory and state tracking to the prototype.

**Tasks:**
1. Build `incubation/memory_manager.py` — In-memory conversation tracking:
   - Customer identification (email as primary key)
   - Conversation history per customer
   - Sentiment tracking (positive/negative/neutral)
   - Topics discussed tracking
   - Resolution status (solved/pending/escalated)
   - Original channel and channel switch tracking
2. Test cross-channel conversation continuity

**Deliverables:**
- ✅ Working memory system
- ✅ Sentiment analysis integration
- ✅ Cross-channel context preservation

---

### Step 1.4: MCP Server (Hours 12-14)

**Goal:** Expose prototype capabilities as an MCP server with 5+ tools.

**Tasks:**
1. Build `incubation/mcp_server.py` with tools:
   - `search_knowledge_base(query)` → relevant docs
   - `create_ticket(customer_id, issue, priority, channel)` → ticket_id
   - `get_customer_history(customer_id)` → past interactions across ALL channels
   - `escalate_to_human(ticket_id, reason)` → escalation_id
   - `send_response(ticket_id, message, channel)` → delivery_status
   - `analyze_sentiment(message)` → sentiment score + confidence
2. Follow MCP specification for tool definitions
3. Test all tools with sample inputs

**Deliverables:**
- ✅ MCP server with 6 tools
- ✅ All tools tested and working
- ✅ Tool definitions follow MCP spec

---

### Step 1.5: Agent Skills & Documentation (Hours 15-16)

**Goal:** Formalize agent capabilities and document all discoveries.

**Tasks:**
1. Build `incubation/agent_skills.py` — Skills manifest:
   - Knowledge Retrieval Skill
   - Sentiment Analysis Skill
   - Escalation Decision Skill
   - Channel Adaptation Skill
   - Customer Identification Skill
2. Create `specs/discovery-log.md` — Document all discovered requirements
3. Create `specs/customer-success-fte-spec.md` — Crystallized specification
4. Create `specs/transition-checklist.md` — Pre-transition checklist

**Deliverables:**
- ✅ Agent skills defined and tested
- ✅ Discovery log with iterative exploration notes
- ✅ Crystallized spec document
- ✅ Transition checklist completed

### Phase 1 Deliverables Summary

| # | Deliverable | Status |
|---|------------|--------|
| 1 | Working prototype handling queries from any channel | ☐ |
| 2 | `specs/discovery-log.md` | ☐ |
| 3 | `specs/customer-success-fte-spec.md` | ☐ |
| 4 | MCP server with 5+ tools | ☐ |
| 5 | Agent skills manifest | ☐ |
| 6 | Channel-specific response templates | ☐ |
| 7 | Edge cases documented (20+ per channel) | ☐ |
| 8 | Performance baseline measured | ☐ |

---

## 🏗️ Phase 2: The Specialization Phase (Hours 17-40)

### Objective
Transform the incubated prototype into a **production-grade Custom Agent** using OpenAI Agents SDK, FastAPI, PostgreSQL, Kafka, and Kubernetes — ready for 24/7 autonomous operation.

### Step 2.1: Database Schema — Our CRM System (Hours 17-19)

**Goal:** Design and implement the PostgreSQL schema that serves as our complete CRM/ticket management system.

**Tasks:**
1. Create `production/database/schema.sql` with tables:
   - `customers` — Unified customer database across all channels
   - `customer_identifiers` — Cross-channel identity matching (email, phone, WhatsApp)
   - `conversations` — Conversation threads with sentiment and status
   - `messages` — Individual messages with channel tracking, tool calls, latency
   - `tickets` — Support ticket lifecycle tracking
   - `knowledge_base` — Product documentation with vector embeddings (pgvector)
   - `channel_configs` — Per-channel configuration
   - `agent_metrics` — Performance metrics tracking
2. Create all necessary indexes for performance
3. Create `production/database/queries.py` — Database access functions
4. Create migration files

**Deliverables:**
- ✅ Complete PostgreSQL schema (8 tables)
- ✅ Vector search support (pgvector)
- ✅ Indexes for all query patterns
- ✅ Database access functions

---

### Step 2.2: Channel Integrations (Hours 20-24)

**Goal:** Build the intake handlers for all three channels.

#### 2.2.1: Gmail Integration

**Tasks:**
1. Create `production/channels/gmail_handler.py`:
   - Gmail API authentication and setup
   - Push notifications via Pub/Sub
   - Email parsing (headers, body extraction, multipart handling)
   - Reply sending with threading support
   - Channel-specific response formatting
2. Test with Gmail API sandbox

**Deliverables:**
- ✅ Complete Gmail handler class
- ✅ Webhook processing working
- ✅ Reply sending working

#### 2.2.2: WhatsApp/Twilio Integration

**Tasks:**
1. Create `production/channels/whatsapp_handler.py`:
   - Twilio client initialization
   - Webhook signature validation (security)
   - Message processing from Twilio webhook
   - Message sending via Twilio API
   - Response splitting for WhatsApp 1600-char limit
   - Delivery status tracking
2. Test with Twilio WhatsApp Sandbox

**Deliverables:**
- ✅ Complete WhatsApp handler class
- ✅ Webhook validation working
- ✅ Message splitting for long responses

#### 2.2.3: Web Support Form — REQUIRED DELIVERABLE (10 points!)

**Tasks:**
1. Create `production/channels/web_form_handler.py` — FastAPI endpoint:
   - Pydantic model with validation (name, email, subject, category, message)
   - POST `/support/submit` endpoint
   - GET `/support/ticket/{ticket_id}` status endpoint
   - Kafka publishing for agent processing
2. Create `web-form/components/SupportForm.jsx` — Complete React component:
   - Beautiful Tailwind CSS styled form
   - Real-time field validation
   - Category and priority selectors
   - Loading states and error handling
   - Success screen with ticket ID
   - Ticket status checking capability
3. Create `web-form/pages/index.js` — Next.js page hosting the form

**Deliverables:**
- ✅ FastAPI web form endpoints
- ✅ Complete React form component (Tailwind CSS)
- ✅ Form validation (client + server side)
- ✅ Ticket submission and status checking
- ✅ Beautiful, professional UI

---

### Step 2.3: OpenAI Agents SDK Implementation (Hours 25-29)

**Goal:** Transform the prototype into a production agent using OpenAI Agents SDK.

**Tasks:**
1. Create `production/agent/prompts.py` — System prompts:
   - Extract and formalize working prompts from incubation
   - Add explicit constraints for each channel
   - Define escalation triggers
   - Define cross-channel continuity instructions
2. Create `production/agent/tools.py` — Production tool definitions:
   - Convert MCP tools to `@function_tool` decorated functions
   - Add Pydantic input validation schemas
   - Add comprehensive error handling with fallbacks
   - Add structured logging
   - All 5+ tools: search_knowledge_base, create_ticket, get_customer_history, escalate_to_human, send_response
3. Create `production/agent/formatters.py` — Channel-specific formatting:
   - Email: Formal with greeting, signature, ticket reference
   - WhatsApp: Concise, conversational, under 300 chars
   - Web: Semi-formal, balanced
4. Create `production/agent/customer_success_agent.py` — Agent definition:
   - OpenAI Agents SDK Agent with all tools
   - Channel-aware instructions
   - Cross-channel continuity context

**Deliverables:**
- ✅ Production system prompts with explicit constraints
- ✅ All tools converted from MCP to @function_tool
- ✅ Pydantic input validation on all tools
- ✅ Error handling with fallbacks
- ✅ Channel-aware response formatting
- ✅ Agent definition with all tools registered

---

### Step 2.4: Kafka Event Streaming (Hours 30-31)

**Goal:** Set up Kafka topics for event-driven message processing.

**Tasks:**
1. Create `production/kafka_client.py`:
   - FTEKafkaProducer class with JSON serialization
   - FTEKafkaConsumer class with JSON deserialization
   - Topic definitions:
     - `fte.tickets.incoming` — Unified incoming messages
     - `fte.channels.email.inbound` — Email-specific
     - `fte.channels.whatsapp.inbound` — WhatsApp-specific
     - `fte.channels.webform.inbound` — Web form-specific
     - `fte.channels.email.outbound` — Email responses
     - `fte.channels.whatsapp.outbound` — WhatsApp responses
     - `fte.escalations` — Human escalations
     - `fte.metrics` — Performance metrics
     - `fte.dlq` — Dead letter queue for failures
2. Add error handling and retry logic

**Deliverables:**
- ✅ Kafka producer and consumer classes
- ✅ All topics defined and documented
- ✅ Error handling and retry logic

---

### Step 2.5: FastAPI Service (Hours 32-34)

**Goal:** Build the API layer with endpoints for all channels and management.

**Tasks:**
1. Create `production/api/main.py` — FastAPI application:
   - Health check: `GET /health`
   - Gmail webhook: `POST /webhooks/gmail`
   - WhatsApp webhook: `POST /webhooks/whatsapp` (with signature validation)
   - WhatsApp status: `POST /webhooks/whatsapp/status`
   - Web form: Include web_form_handler router
   - Conversation history: `GET /conversations/{conversation_id}`
   - Customer lookup: `GET /customers/lookup?email=&phone=`
   - Channel metrics: `GET /metrics/channels`
   - CORS middleware for web form
   - Startup/shutdown event handlers for Kafka
2. Add request/response models
3. Add error handling middleware

**Deliverables:**
- ✅ All API endpoints implemented
- ✅ CORS configured for web form
- ✅ Health check endpoint
- ✅ Channel-specific webhook handlers
- ✅ Customer lookup across channels
- ✅ Metrics endpoint

---

### Step 2.6: Unified Message Processor (Hours 35-37)

**Goal:** Build the worker that consumes Kafka messages and runs the agent.

**Tasks:**
1. Create `production/workers/message_processor.py`:
   - UnifiedMessageProcessor class
   - Customer resolution/creation logic
   - Conversation management (new vs. existing)
   - Message storage to PostgreSQL
   - Agent execution with conversation history
   - Response storage and channel-specific delivery
   - Metrics publishing
   - Error handling with graceful fallback
2. Create `production/workers/metrics_collector.py`:
   - Background metrics collection
   - Performance tracking
   - Alert generation

**Deliverables:**
- ✅ Message processor consuming from Kafka
- ✅ Customer resolution across channels
- ✅ Agent execution pipeline
- ✅ Error handling with apologetic responses
- ✅ Metrics collection

---

### Step 2.7: Kubernetes Deployment (Hours 38-40)

**Goal:** Create all Kubernetes manifests for production deployment.

**Tasks:**
1. Create `k8s/namespace.yaml` — Namespace definition
2. Create `k8s/configmap.yaml` — Configuration (env vars, channel configs)
3. Create `k8s/secrets.yaml` — Sensitive data (API keys, credentials)
4. Create `k8s/deployment-api.yaml` — API deployment (3 replicas)
5. Create `k8s/deployment-worker.yaml` — Worker deployment (3 replicas)
6. Create `k8s/service.yaml` — ClusterIP service
7. Create `k8s/ingress.yaml` — Ingress with TLS
8. Create `k8s/hpa.yaml` — Horizontal Pod Autoscaler (API: 3-20, Worker: 3-30)
9. Create `Dockerfile` — Multi-stage build
10. Create `docker-compose.yml` — Local development stack

**Deliverables:**
- ✅ All 8 K8s manifests
- ✅ Dockerfile for containerization
- ✅ docker-compose.yml for local testing
- ✅ Auto-scaling configured (HPA)
- ✅ Health checks configured
- ✅ Resource limits set

### Phase 2 Deliverables Summary

| # | Deliverable | Status |
|---|------------|--------|
| 1 | PostgreSQL schema with multi-channel support | ☐ |
| 2 | OpenAI Agents SDK implementation | ☐ |
| 3 | FastAPI service with all channel endpoints | ☐ |
| 4 | Gmail integration (webhook + send) | ☐ |
| 5 | WhatsApp/Twilio integration (webhook + send) | ☐ |
| 6 | **Web Support Form (REQUIRED — 10 pts)** | ☐ |
| 7 | Kafka event streaming with channel topics | ☐ |
| 8 | Kubernetes manifests for deployment | ☐ |
| 9 | Monitoring configuration | ☐ |
| 10 | Docker + docker-compose | ☐ |

---

## 🧪 Phase 3: Integration & Testing (Hours 41-48)

### Objective
Validate the entire system with comprehensive testing, documentation, and a 24-hour survival test.

### Step 3.1: Multi-Channel E2E Testing (Hours 41-44)

**Goal:** Build and pass comprehensive end-to-end tests across all channels.

**Tasks:**
1. Create `tests/test_agent.py` — Agent unit tests:
   - Tool execution order verification
   - Escalation trigger tests
   - Channel response format tests
   - Edge case tests (empty messages, angry customers, pricing queries)
2. Create `tests/test_channels.py` — Channel handler tests:
   - Gmail webhook processing
   - WhatsApp webhook with signature validation
   - Web form submission and validation
   - Response formatting per channel
3. Create `tests/test_multichannel_e2e.py` — End-to-end tests:
   - Web form submission → ticket creation → agent response
   - Gmail webhook → ticket creation → agent response
   - WhatsApp webhook → ticket creation → agent response
   - Cross-channel customer history
   - Customer lookup across channels
   - Channel metrics validation
4. Create `tests/test_transition.py` — Transition tests:
   - Edge cases from incubation still handled
   - Tool migration verification
   - Behavior parity with prototype

**Deliverables:**
- ✅ All unit tests passing
- ✅ All channel tests passing
- ✅ All E2E tests passing
- ✅ Transition tests passing

---

### Step 3.2: Load Testing (Hours 45-46)

**Goal:** Validate system performance under load.

**Tasks:**
1. Create `tests/load_test.py` — Locust load test:
   - WebFormUser: Simulates form submissions (weight=3)
   - HealthCheckUser: Monitors system health (weight=1)
   - Realistic wait times and random data
2. Run load test and document results
3. Validate performance requirements:
   - P95 latency < 3 seconds
   - No message loss
   - System remains stable under load

**Deliverables:**
- ✅ Load test suite
- ✅ Performance results documented
- ✅ System stable under load

---

### Step 3.3: Documentation & Runbook (Hours 47-48)

**Goal:** Create comprehensive documentation for deployment, operations, and judging.

**Tasks:**
1. Create `README.md` — Main project documentation:
   - Project overview and architecture
   - Quick start guide
   - Feature summary
   - Technology stack
2. Create `docs/deployment-guide.md` — Step-by-step deployment:
   - Prerequisites
   - Local development setup (docker-compose)
   - Kubernetes deployment
   - Channel configuration (Gmail, WhatsApp, Web Form)
   - Verification steps
3. Create `docs/runbook.md` — Operations guide:
   - Common issues and solutions
   - Scaling procedures
   - Incident response
   - Monitoring and alerting
   - Pod failure recovery
4. Create `docs/api-documentation.md` — API reference:
   - All endpoints documented
   - Request/response examples
   - Authentication requirements
5. Create `docs/24-hour-test-plan.md` — Survival test plan:
   - Traffic generation plan
   - Chaos testing procedures
   - Metrics validation criteria

**Deliverables:**
- ✅ README.md with project overview
- ✅ Deployment guide
- ✅ Operations runbook
- ✅ API documentation
- ✅ 24-hour test plan

### Phase 3 Deliverables Summary

| # | Deliverable | Status |
|---|------------|--------|
| 1 | Multi-channel E2E test suite passing | ☐ |
| 2 | Load test results showing 24/7 readiness | ☐ |
| 3 | Deployment documentation | ☐ |
| 4 | Operations runbook | ☐ |
| 5 | API documentation | ☐ |
| 6 | 24-hour test plan | ☐ |

---

## 🚀 24-Hour Continuous Operation Test Criteria

After deployment, the system must survive:

| Metric | Target | How We Validate |
|--------|--------|----------------|
| **Uptime** | > 99.9% | Health check monitoring |
| **Web Form Traffic** | 100+ submissions | Automated form submissions |
| **Email Simulation** | 50+ messages | Gmail API test messages |
| **WhatsApp Simulation** | 50+ messages | Twilio sandbox messages |
| **Cross-Channel** | 10+ multi-channel customers | Customers contacting via 2+ channels |
| **P95 Latency** | < 3 seconds | Metrics collection |
| **Escalation Rate** | < 25% | Ticket status tracking |
| **Cross-Channel ID** | > 95% accuracy | Customer identifier matching |
| **Message Loss** | 0 messages | Kafka offset tracking |
| **Chaos Tolerance** | Survives random pod kills | Kill pods every 2 hours |

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **AI Agent** | OpenAI Agents SDK + GPT-4o | Core intelligence |
| **API** | FastAPI (Python) | REST endpoints, webhooks |
| **Database/CRM** | PostgreSQL 16 + pgvector | Customer data, vector search |
| **Event Streaming** | Apache Kafka (aiokafka) | Message queue, event bus |
| **Web Form** | React + Next.js + Tailwind CSS | Customer-facing support form |
| **Email Channel** | Gmail API + Pub/Sub | Email intake and replies |
| **WhatsApp Channel** | Twilio WhatsApp API | WhatsApp intake and replies |
| **Containerization** | Docker | Packaging |
| **Orchestration** | Kubernetes + HPA | Deployment, auto-scaling |
| **Testing** | pytest + Locust | Unit, E2E, load testing |
| **Incubation** | Claude Code (MCP) | Prototype development |

---

## ⚠️ Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| OpenAI API rate limits | High | Implement retry logic, fallback responses |
| Kafka unavailable | High | Graceful degradation, local queue |
| Pod crashes | Medium | HPA auto-recovery, stateless design |
| Database connection pool exhausted | Medium | Connection pooling, query optimization |
| External API credentials missing | Medium | Sandbox/mocking for development |
| Web form validation bypass | Low | Server-side validation on FastAPI |
| Response exceeds channel limits | Low | Built-in truncation and splitting |

---

## 📅 Implementation Order

```
Phase 1 (Incubation)          Phase 2 (Specialization)        Phase 3 (Integration)
─────────────────────         ──────────────────────────      ─────────────────────
1. Context files              1. PostgreSQL schema            1. Agent unit tests
2. Sample tickets             2. Gmail handler                2. Channel tests
3. Prototype core loop        3. WhatsApp handler             3. E2E tests
4. Memory manager             4. Web Support Form ⭐          4. Load tests
5. MCP server (6 tools)       5. OpenAI Agent + tools         5. Documentation
6. Agent skills               6. Kafka streaming              6. Runbook
7. Discovery log              7. FastAPI service              7. Final validation
8. Spec document              8. Message processor
9. Transition checklist       9. K8s manifests + Docker
```

---

## 🏆 Success Criteria

### Minimum Viable (Passing):
- [ ] Working prototype with MCP server
- [ ] PostgreSQL schema deployed
- [ ] Web Support Form built and functional
- [ ] At least 2 channel integrations working
- [ ] FastAPI service with health check
- [ ] Agent can process and respond to test messages
- [ ] Basic tests passing

### Full Marks (Excelling):
- [ ] All Phase 1 deliverables complete
- [ ] All 3 channels fully functional
- [ ] Complete OpenAI Agents SDK implementation
- [ ] Kafka event streaming operational
- [ ] Kubernetes deployment with auto-scaling
- [ ] All E2E and load tests passing
- [ ] Cross-channel customer identification working
- [ ] Comprehensive documentation
- [ ] 24-hour survival test passed
- [ ] Creative innovations demonstrated

---

## 💡 Innovation Opportunities (Extra Points)

1. **Sentiment Dashboard** — Real-time customer sentiment tracking with visualization
2. **Smart Escalation** — ML-based escalation prediction beyond rule-based triggers
3. **Knowledge Base Auto-Learning** — Agent learns from resolved tickets and updates KB
4. **Multi-Language Support** — Auto-detect and respond in customer's language
5. **Response Quality Scoring** — Self-evaluation of response quality
6. **Proactive Outreach** — Agent follows up on unresolved tickets
7. **Advanced Analytics** — Daily reports on customer sentiment, top issues, resolution rates

---

> **"Welcome to the future of customer support. Now build it."**
