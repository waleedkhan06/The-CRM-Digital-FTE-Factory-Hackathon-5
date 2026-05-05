# Customer Success FTE — API Documentation

**Base URL (local dev):** `http://localhost:8000`  
**Base URL (k8s):** `https://fte.techcorp.ai`  
**API Version:** `2.0.0`  
**Interactive Docs:** `GET /docs` (Swagger UI) · `GET /redoc` (ReDoc)

All request/response bodies are JSON unless noted otherwise.  
Timestamps are ISO-8601 UTC strings. UUIDs are standard v4 format.

---

## Authentication

| Channel | Auth Method |
|---------|------------|
| Web Form endpoints | No auth required (public) |
| Gmail webhook | Google Cloud Pub/Sub push (verified by payload signature) |
| WhatsApp webhook | Twilio signature header `X-Twilio-Signature` |
| Internal endpoints (`/agent/*`, `/metrics/*`) | Set `Authorization: Bearer <API_KEY>` (env `INTERNAL_API_KEY`) |

---

## Health & Readiness

### `GET /health`
Basic liveness probe. Used by Kubernetes liveness checks.

**Response `200 OK`**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "version": "2.0.0",
  "channels": {
    "email": "active",
    "whatsapp": "active",
    "web_form": "active"
  }
}
```

---

### `GET /health/ready`
Deep readiness probe — verifies database, Kafka, and channel handler connectivity.

**Response `200 OK` — all healthy**
```json
{
  "status": "ready",
  "checks": {
    "database": true,
    "kafka": true,
    "gmail": true,
    "whatsapp": true
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

**Response `200 OK` — degraded (some checks failed)**
```json
{
  "status": "degraded",
  "checks": {
    "database": true,
    "kafka": false,
    "gmail": false,
    "whatsapp": true
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

> **Note:** Returns HTTP `200` even when degraded so k8s does not restart healthy pods. Monitor the `status` field.

---

## Web Support Form

### `POST /support/submit`
Submit a new customer support ticket via the web form.

**Request Body**
```json
{
  "name": "Alice Smith",
  "email": "alice@example.com",
  "subject": "Cannot log in after password change",
  "category": "account",
  "message": "I changed my password yesterday and now I cannot log in. The reset email never arrived.",
  "priority": "medium"
}
```

| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| `name` | string | ✅ | 2–100 chars |
| `email` | string (email) | ✅ | Valid email format |
| `subject` | string | ✅ | 5–200 chars |
| `category` | string | ✅ | `account`, `billing`, `technical`, `general`, `feature_request` |
| `message` | string | ✅ | 10–5000 chars |
| `priority` | string | ❌ | `low`, `medium` (default), `high`, `urgent` |

**Response `202 Accepted`**
```json
{
  "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Your support request has been received. Our AI agent will respond within 3 seconds.",
  "estimated_response_time": "< 30 seconds",
  "channel": "web_form"
}
```

**Response `422 Unprocessable Entity`** — validation error
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

### `GET /support/ticket/{ticket_id}`
Check the status of a previously submitted support ticket.

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `ticket_id` | UUID string | Ticket ID returned from `POST /support/submit` |

**Response `200 OK`**
```json
{
  "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "resolved",
  "created_at": "2024-01-15T10:30:00.000Z",
  "resolved_at": "2024-01-15T10:30:28.000Z",
  "category": "account",
  "priority": "medium",
  "agent_response": "Hello Alice, to reset your password please go to Settings > Security > Reset Password. You should receive a new email within 2 minutes. — TechCorp Support",
  "escalated": false,
  "sentiment_score": 0.65
}
```

**Ticket Status Values**

| Status | Meaning |
|--------|---------|
| `queued` | Received, waiting for agent |
| `processing` | Agent is generating a response |
| `resolved` | Agent responded successfully |
| `escalated` | Handed off to human support |
| `open` | Active, pending further action |

**Response `404 Not Found`**
```json
{
  "detail": "Ticket not found"
}
```

---

## Gmail Webhook

### `POST /webhooks/gmail`
Receives Gmail push notifications from Google Cloud Pub/Sub.  
**Do not call this manually** — Google Cloud routes emails here automatically.

**Request Body** (Google Pub/Sub push format)
```json
{
  "message": {
    "data": "<base64-encoded-json>",
    "messageId": "1234567890",
    "publishTime": "2024-01-15T10:30:00.000Z"
  },
  "subscription": "projects/your-project/subscriptions/gmail-push"
}
```

The `data` field decodes to:
```json
{
  "emailAddress": "support@techcorp.ai",
  "historyId": "12345"
}
```

**Response `200 OK`**
```json
{
  "status": "processed",
  "count": 3
}
```

**Response `500 Internal Server Error`**
```json
{
  "detail": "Gmail API error: <message>"
}
```

> **Setup:** Configure Gmail Pub/Sub push subscription to point to `POST /webhooks/gmail`.  
> See `docs/deployment-guide.md` → Gmail Setup for full instructions.

---

## WhatsApp / Twilio Webhook

### `POST /webhooks/whatsapp`
Receives incoming WhatsApp messages from Twilio.  
**Security:** Every request is validated against the `X-Twilio-Signature` header using `TWILIO_AUTH_TOKEN`.

**Request** (Twilio sends `application/x-www-form-urlencoded`)
```
Body=Hello+I+need+help
From=whatsapp%3A%2B12345678900
To=whatsapp%3A%2B14155238886
MessageSid=SM1234567890abcdef
AccountSid=AC1234567890abcdef
NumMedia=0
```

**Response `200 OK`** (empty TwiML — agent responds asynchronously)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response></Response>
```

**Response `403 Forbidden`** — invalid Twilio signature
```json
{
  "detail": "Invalid signature"
}
```

> **Setup:** In Twilio Console, set webhook URL to `POST /webhooks/whatsapp` with HTTP POST method.

---

### `POST /webhooks/whatsapp/status`
Receives delivery status updates (sent, delivered, read, failed) from Twilio.

**Request** (form-urlencoded)
```
MessageSid=SM1234567890abcdef
MessageStatus=delivered
To=whatsapp%3A%2B12345678900
```

**Response `200 OK`**
```json
{
  "status": "received"
}
```

---

## Conversations

### `GET /conversations/{conversation_id}`
Retrieve full conversation history including all messages across channels.

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `conversation_id` | UUID string | Conversation ID |

**Response `200 OK`**
```json
{
  "conversation": {
    "id": "conv-uuid-here",
    "customer_id": "cust-uuid-here",
    "initial_channel": "email",
    "status": "resolved",
    "sentiment_score": 0.72,
    "started_at": "2024-01-15T10:28:00.000Z",
    "ended_at": "2024-01-15T10:30:28.000Z"
  },
  "messages": [
    {
      "id": "msg-uuid-1",
      "role": "customer",
      "content": "I cannot log in to my account.",
      "channel": "email",
      "direction": "inbound",
      "created_at": "2024-01-15T10:28:00.000Z",
      "sentiment_score": 0.5,
      "delivery_status": "received"
    },
    {
      "id": "msg-uuid-2",
      "role": "agent",
      "content": "Hello Alice, to reset your password...",
      "channel": "email",
      "direction": "outbound",
      "created_at": "2024-01-15T10:28:03.000Z",
      "sentiment_score": 0.72,
      "delivery_status": "sent"
    }
  ],
  "message_count": 2
}
```

**Response `404 Not Found`**
```json
{
  "detail": "Conversation not found"
}
```

---

## Customers

### `GET /customers/lookup`
Look up a customer by email or phone number, returning their profile and interaction history across **all channels**.

**Query Parameters** (at least one required)

| Parameter | Type | Description |
|-----------|------|-------------|
| `email` | string | Customer email address |
| `phone` | string | Customer phone number (E.164 format, e.g. `+12345678900`) |

**Examples**
```
GET /customers/lookup?email=alice@example.com
GET /customers/lookup?phone=+12345678900
GET /customers/lookup?email=alice@example.com&phone=+12345678900
```

**Response `200 OK`**
```json
{
  "customer": {
    "id": "cust-uuid-here",
    "email": "alice@example.com",
    "phone": "+12345678900",
    "name": "Alice Smith",
    "preferred_channel": "email",
    "total_interactions": 5,
    "avg_sentiment": 0.72,
    "created_at": "2024-01-10T09:00:00.000Z"
  },
  "history": {
    "customer": { "...": "..." },
    "total_conversations": 5,
    "conversations": [
      {
        "id": "conv-uuid-1",
        "initial_channel": "email",
        "status": "resolved",
        "sentiment_score": 0.8,
        "message_count": 2,
        "topics": ["password_reset", "account_access"]
      }
    ]
  }
}
```

**Response `400 Bad Request`**
```json
{
  "detail": "Provide at least email or phone parameter"
}
```

---

## Metrics

### `GET /metrics/channels`
Get channel-specific performance metrics for the last 24 hours.

**Response `200 OK`**
```json
{
  "email": {
    "conversation_count": 45,
    "avg_sentiment": 0.68,
    "escalation_rate": 0.12,
    "avg_response_time_ms": 1850,
    "channel": "email",
    "total_tickets": 45,
    "escalated": 5,
    "resolved": 38,
    "open_tickets": 2
  },
  "whatsapp": {
    "conversation_count": 78,
    "avg_sentiment": 0.71,
    "escalation_rate": 0.09,
    "avg_response_time_ms": 1200,
    "channel": "whatsapp",
    "total_tickets": 78,
    "escalated": 7,
    "resolved": 68,
    "open_tickets": 3
  },
  "web_form": {
    "conversation_count": 32,
    "avg_sentiment": 0.74,
    "escalation_rate": 0.06,
    "avg_response_time_ms": 2100,
    "channel": "web_form",
    "total_tickets": 32,
    "escalated": 2,
    "resolved": 29,
    "open_tickets": 1
  }
}
```

---

## Agent (Internal / Debug)

### `POST /agent/process`
Manually trigger agent processing for a message. **Used for testing and debugging only.**

**Request Body**
```json
{
  "content": "How do I reset my password?",
  "channel": "web_form",
  "customer_email": "test@example.com",
  "customer_name": "Test User",
  "subject": "Password Reset Help"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `content` | string | Customer message text |
| `channel` | string | `email`, `whatsapp`, or `web_form` |
| `customer_email` | string | Customer email (used as customer ID) |
| `customer_phone` | string | Customer phone (alternative ID) |
| `customer_name` | string | Customer display name |
| `subject` | string | Ticket subject/topic |

**Response `200 OK`**
```json
{
  "status": "processed",
  "response": "Hello! To reset your password, please go to Settings > Security > Reset Password...",
  "escalated": false,
  "escalation_reason": null,
  "sentiment": 0.65,
  "topics": ["password_reset"],
  "ticket_id": "ticket-uuid-here"
}
```

**Response `500 Internal Server Error`**
```json
{
  "detail": "Agent processing error: <message>"
}
```

---

## Kafka Topics Reference

| Topic | Description | Published By | Consumed By |
|-------|-------------|--------------|-------------|
| `fte.tickets.incoming` | Unified incoming messages from all channels | API (all webhooks) | Worker (message_processor) |
| `fte.channels.email.inbound` | Email-specific inbound messages | Gmail webhook | Analytics |
| `fte.channels.whatsapp.inbound` | WhatsApp-specific inbound messages | WhatsApp webhook | Analytics |
| `fte.channels.webform.inbound` | Web form submissions | Web form handler | Analytics |
| `fte.channels.email.outbound` | Email responses sent | Message processor | Audit |
| `fte.channels.whatsapp.outbound` | WhatsApp responses sent | Message processor | Audit |
| `fte.escalations` | Human escalation events + alerts | Message processor, MetricsCollector | Human support queue |
| `fte.metrics` | Performance metrics snapshots + heartbeats | MetricsCollector | Monitoring dashboard |
| `fte.dlq` | Failed message dead-letter queue | Any component on error | Human review |

---

## Error Codes Reference

| HTTP Code | Meaning | Common Cause |
|-----------|---------|--------------|
| `200` | OK | Request processed successfully |
| `202` | Accepted | Queued for async processing (web form submit) |
| `400` | Bad Request | Missing required query parameters |
| `403` | Forbidden | Invalid Twilio webhook signature |
| `404` | Not Found | Ticket/conversation/customer ID does not exist |
| `422` | Unprocessable Entity | Request body fails Pydantic validation |
| `500` | Internal Server Error | Unexpected server error (check logs) |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| `POST /support/submit` | 10 req/min per IP |
| `GET /support/ticket/*` | 60 req/min per IP |
| `POST /webhooks/gmail` | Unlimited (Google Pub/Sub) |
| `POST /webhooks/whatsapp` | Unlimited (Twilio) |
| `GET /metrics/*` | 30 req/min |
| `POST /agent/process` | 5 req/min (debug only) |

---

## CORS Policy

CORS is configured for the web form. Allowed origins are set via the `WEB_FORM_ALLOWED_ORIGINS` environment variable (defaults to `*` in development).

```
Access-Control-Allow-Origin: https://your-frontend-domain.com
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

---

## Response Format Conventions

All JSON responses follow these conventions:

- **Timestamps:** ISO-8601 UTC (`2024-01-15T10:30:00.000Z`)
- **IDs:** UUID v4 strings (`550e8400-e29b-41d4-a716-446655440000`)
- **Sentiment scores:** Decimal `0.0`–`1.0` (0 = very negative, 1 = very positive)
- **Channel values:** `"email"`, `"whatsapp"`, `"web_form"` (snake_case)
- **Status values:** snake_case strings (e.g., `"open"`, `"in_progress"`, `"escalated"`)
