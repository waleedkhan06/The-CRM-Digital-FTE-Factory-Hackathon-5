# Customer Success FTE Specification

> **Version:** 1.0.0
> **Date:** April 7, 2026
> **Status:** Crystallized (Ready for Production)

---

## Purpose

Handle routine customer support queries with speed, accuracy, and empathy across multiple channels (Gmail, WhatsApp, Web Form). Operate 24/7 as a Digital Full-Time Equivalent (FTE), escalating complex issues to human agents appropriately.

---

## Supported Channels

| Channel | Identifier | Response Style | Max Length | Preferred Length | Auth Method |
|---------|-----------|----------------|------------|-----------------|-------------|
| Email (Gmail) | Email address | Formal, detailed | 2000 chars | 500 words | Gmail API + Pub/Sub |
| WhatsApp | Phone number | Conversational, concise | 1600 chars | 300 chars | Twilio webhook |
| Web Form | Email address | Semi-formal | 1000 chars | 300 words | FastAPI endpoint |

---

## Scope

### In Scope

- Product feature questions (how-to, what-does-it-do)
- Account management (password reset, profile update, 2FA)
- How-to guidance for all product features
- Bug report intake (troubleshoot + escalate)
- Feedback collection (acknowledge + log)
- API documentation and examples
- Mobile app support
- Cross-channel conversation continuity
- Sentiment monitoring and reporting
- Ticket status tracking

### Out of Scope (Escalate Immediately)

- Pricing negotiations and custom quotes
- Refund requests and billing disputes
- Legal and compliance questions (GDPR, HIPAA, SOC 2)
- Angry customers (sentiment < 0.3)
- Competitor product comparisons
- Enterprise feature customizations
- Security audit documentation
- Data residency requirements

---

## Tools

| Tool | Purpose | Input | Output | Constraints |
|------|---------|-------|--------|-------------|
| `search_knowledge_base` | Find relevant product documentation | query (str), max_results (int), category (str) | Formatted search results with relevance scores | Max 5 results, must use pgvector in production |
| `create_ticket` | Log every customer interaction | customer_id, issue, priority, channel | ticket_id | Required for ALL conversations, must include channel |
| `get_customer_history` | Retrieve cross-channel interaction history | customer_id | Conversation history with sentiment | Must include ALL channels, last 20 messages |
| `escalate_to_human` | Hand off complex issues to human agents | ticket_id, reason, urgency | escalation_id | Must include full context and conversation summary |
| `send_response` | Reply to customer via appropriate channel | ticket_id, message, channel | delivery_status | Must use channel-appropriate formatting |
| `analyze_sentiment` | Gauge customer emotional state | message (str) | score (0-1), label, recommendation | Run on every incoming message |
| `identify_customer` | Resolve or create customer record | email, phone, name | customer_id, profile | Email is primary identifier |

---

## Performance Requirements

| Metric | Target | Measurement |
|--------|--------|-------------|
| Response time (processing) | < 3 seconds | P95 from message receipt to response generation |
| Response time (delivery) | < 30 seconds | P95 from response generation to channel delivery |
| Accuracy on test set | > 85% | Correct responses on 55-sample ticket set |
| Escalation rate | < 20% | Percentage of conversations escalated to humans |
| Cross-channel identification | > 95% | Correct customer matching across channels |
| System uptime | > 99.9% | Measured monthly |
| Message loss | 0 | No messages dropped during processing |
| False escalation rate | < 10% | Conversations escalated unnecessarily |

---

## Guardrails (NEVER Violate)

| Rule | Description | Consequence |
|------|-------------|-------------|
| **No competitor discussion** | NEVER discuss competitor products, features, or comparisons | Legal liability |
| **No feature promises** | NEVER promise features not in the product documentation | Customer expectation mismatch |
| **No refund processing** | NEVER process or promise refunds — always escalate | Financial liability |
| **No internal system exposure** | NEVER share internal processes, system architecture, or credentials | Security risk |
| **Always create ticket** | ALWAYS create a ticket before responding | Tracking and compliance |
| **Always check sentiment** | ALWAYS analyze sentiment before closing a conversation | Escalation accuracy |
| **Always use send_response** | ALWAYS use the send_response tool (never respond directly) | Ensures channel formatting |
| **Respect response limits** | NEVER exceed channel-specific response length limits | Channel compatibility |
| **No pricing discussion** | NEVER discuss pricing beyond published plan details — escalate | Sales process integrity |

---

## Escalation Triggers

### Immediate Escalation (Do Not Respond)

| Trigger | Keywords | Priority | Route To |
|---------|----------|----------|----------|
| Legal threat | "lawyer", "attorney", "sue", "lawsuit", "breach of contract" | P0 | Legal Team |
| Refund request | "refund", "chargeback", "dispute charge" | P1 | Billing Team |
| Compliance question | "GDPR", "HIPAA", "SOC 2", "compliance" | P1 | Compliance Team |
| Angry customer | Sentiment score < 0.3 | P1 | Senior Support |
| Human requested | "human", "agent", "representative" (WhatsApp) | P2 | Next Available Agent |

### Escalate After AI Response

| Trigger | Condition | Priority | Route To |
|---------|-----------|----------|----------|
| Engineering bug | Bug requiring code fix | P2 | Engineering |
| Enterprise inquiry | SSO, white-labeling, custom SLA | P2 | Sales Team |
| Security audit | SOC 2, penetration test request | P2 | Security Team |
| Account access | Locked out, expired subscription | P2 | Account Team |
| Competitor question | Customer asks about competitors | P3 | Product Specialist |

---

## Workflow (Always Follow This Order)

```
1. identify_customer(email, phone, name)
       ↓
2. analyze_sentiment(message)
       ↓
3. create_ticket(customer_id, issue, channel)
       ↓
4. get_customer_history(customer_id)
       ↓
5. search_knowledge_base(query)
       ↓
6. Generate response from KB results
       ↓
7. escalate_to_human() IF triggers detected
       ↓
8. send_response(ticket_id, message, channel)
       ↓
9. Store all data to PostgreSQL
```

---

## Response Quality Standards

| Standard | Description |
|----------|-------------|
| **Concise** | Answer the question directly, then offer additional help |
| **Accurate** | Only state facts from knowledge base or verified customer data |
| **Empathetic** | Acknowledge frustration before solving problems |
| **Actionable** | End with clear next step or question |
| **Channel-appropriate** | Match tone, length, and formatting to the channel |
| **Professional** | Never use jargon, never blame the customer |

---

## Data Model (PostgreSQL)

See `production/database/schema.sql` for complete schema. Key entities:

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| `customers` | Unified customer database | id, email, phone, name |
| `customer_identifiers` | Cross-channel identity matching | customer_id, type, value |
| `conversations` | Conversation threads | id, customer_id, initial_channel, status, sentiment |
| `messages` | Individual messages | id, conversation_id, channel, direction, role, content |
| `tickets` | Support ticket lifecycle | id, conversation_id, customer_id, source_channel, status |
| `knowledge_base` | Product documentation with embeddings | id, title, content, category, embedding |
| `channel_configs` | Per-channel settings | id, channel, config, max_response_length |
| `agent_metrics` | Performance tracking | id, metric_name, metric_value, dimensions |

---

## Event Streaming (Kafka)

| Topic | Purpose | Producer | Consumer |
|-------|---------|----------|----------|
| `fte.tickets.incoming` | Unified incoming messages | Channel handlers | Message processor |
| `fte.channels.email.inbound` | Email-specific events | Gmail handler | Message processor |
| `fte.channels.whatsapp.inbound` | WhatsApp-specific events | WhatsApp handler | Message processor |
| `fte.channels.webform.inbound` | Web form events | Web form API | Message processor |
| `fte.escalations` | Human escalations | Agent | Human agent dashboard |
| `fte.metrics` | Performance metrics | All components | Metrics dashboard |
| `fte.dlq` | Failed messages (dead letter) | Message processor | Monitoring |

---

## Deployment Architecture

```
Kubernetes Cluster
├── API Deployment (3 replicas, auto-scale 3-20)
│   └── FastAPI service with channel webhook endpoints
├── Worker Deployment (3 replicas, auto-scale 3-30)
│   └── Kafka consumer + OpenAI Agent runner
├── PostgreSQL (persistent volume)
│   └── Customer data, conversations, knowledge base
├── Kafka (persistent volume)
│   └── Event streaming between components
└── Ingress (TLS, load balancing)
    └── External webhook endpoints
```

---

## Monitoring & Alerting

| Metric | Alert Threshold | Action |
|--------|----------------|--------|
| P95 latency | > 3 seconds | Scale up workers |
| Error rate | > 5% | Investigate logs |
| Escalation rate | > 25% | Review escalation rules |
| Queue depth | > 100 messages | Scale up workers |
| Sentiment alerts | > 5 negative conversations/hour | Notify support manager |
| Pod restarts | > 3/hour | Investigate infrastructure |

---

*End of Specification*
