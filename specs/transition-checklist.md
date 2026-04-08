# Transition Checklist: General Agent → Custom Agent

> **Date:** April 7, 2026
> **Purpose:** Ensure all incubation discoveries are captured before building production system

---

## 1. Discovered Requirements

All requirements documented during incubation:

- [x] **FR-01:** Accept messages from Gmail, WhatsApp, and Web Form
- [x] **FR-02:** Normalize messages from all channels into unified format
- [x] **FR-03:** Search knowledge base for relevant information
- [x] **FR-04:** Create a ticket for every interaction
- [x] **FR-05:** Track customer history across ALL channels
- [x] **FR-06:** Analyze sentiment of every message
- [x] **FR-07:** Decide when to escalate to human
- [x] **FR-08:** Format responses appropriately per channel
- [x] **FR-09:** Identify customers by email or phone
- [x] **FR-10:** Handle empty or meaningless messages gracefully
- [x] **FR-11:** Never discuss competitor products
- [x] **FR-12:** Never promise features not in documentation
- [x] **FR-13:** Never process refunds — always escalate
- [x] **FR-14:** Track topics discussed for reporting
- [x] **FR-15:** Provide ticket status checking

---

## 2. Working Prompts

### System Prompt That Worked (Prototype)

```
You are a helpful customer support agent for TechCorp SaaS.
Answer questions about the product using the provided documentation.
Be warm, clear, and empathetic.
Escalate immediately for: pricing, refunds, legal threats, compliance questions.
Adapt your tone to the channel:
- Email: formal, detailed, with greeting and signature
- WhatsApp: concise, conversational, under 300 characters
- Web form: semi-formal, helpful, balanced detail
```

### Tool Descriptions That Worked

| Tool | Description | Key Parameters |
|------|-------------|---------------|
| `search_knowledge_base` | "Search product documentation for relevant information" | query, max_results, category |
| `create_ticket` | "Create a support ticket for tracking. ALWAYS create at start of conversation" | customer_id, issue, priority, channel |
| `get_customer_history` | "Get customer's complete interaction history across ALL channels" | customer_id |
| `escalate_to_human` | "Escalate conversation to human support with reason" | ticket_id, reason, urgency |
| `send_response` | "Send response to customer via their preferred channel" | ticket_id, message, channel |
| `analyze_sentiment` | "Analyze sentiment of customer message (0=negative, 1=positive)" | message |
| `identify_customer` | "Identify or create customer from email/phone/name" | email, phone, name |

---

## 3. Edge Cases Found

| # | Edge Case | How It Was Handled | Test Case Needed |
|---|-----------|-------------------|------------------|
| 1 | Empty message (no content) | Return polite request for clarification | Yes |
| 2 | Meaningless message ("????") | Ask for clarification in casual tone | Yes |
| 3 | Test message ("just testing") | Acknowledge briefly, offer help | Yes |
| 4 | Competitor comparison request | Don't discuss competitors, pivot to TechCorp strengths | Yes |
| 5 | Extreme anger + legal threat | Immediate escalation, empathetic acknowledgment | Yes |
| 6 | Customer requests human on WhatsApp | Immediate escalation, confirm handoff | Yes |
| 7 | Pricing/discount inquiry | Escalate to sales, don't negotiate | Yes |
| 8 | Refund request | Escalate to billing, acknowledge concern | Yes |
| 9 | Compliance/legal question | Escalate to legal team | Yes |
| 10 | Bug requiring engineering | Troubleshoot first, escalate with details | Yes |
| 11 | Positive feedback / thanks | Acknowledge warmly, log for morale | Yes |
| 12 | New user onboarding | Provide quick start guide | Yes |
| 13 | Same customer, different channels | Detect via email/phone, merge conversations | Yes |
| 14 | Very long customer message | Process fully, keep response concise | Yes |
| 15 | Multiple questions in one message | Address each or prioritize main one | Yes |
| 16 | Customer provides wrong info | Politely correct based on available data | Yes |
| 17 | Duplicate submission | Detect similar recent tickets, reference them | Yes |
| 18 | Out-of-hours submission | Still respond (24/7 requirement) | Yes |
| 19 | Missing customer identifier | Use available metadata, create minimal record | Yes |
| 20 | Message with special characters | Handle Unicode properly, don't strip | Yes |

---

## 4. Response Patterns

### What Worked Best Per Channel

**Email:**
- Formal greeting: "Dear [Name],"
- Acknowledge the issue first
- Numbered step-by-step instructions
- Offer additional help
- Professional sign-off with ticket reference
- Length: 200-500 words ideal

**WhatsApp:**
- Casual greeting: "Hi [Name]! "
- Direct answer in 1-2 sentences
- One emoji maximum (😊 or 👍)
- Brief offer of more help
- Length: Under 300 characters preferred

**Web Form:**
- Friendly acknowledgment
- Clear answer with steps
- Brief sign-off
- Length: 100-300 words

### What Failed

| Pattern | Problem | Fix Applied |
|---------|---------|-------------|
| Long responses on WhatsApp | Customer loses interest | Truncate to 300 chars |
| No empathy acknowledgment | Felt robotic | Add empathy sentence first |
| Discussing competitors | Against policy | Pivot to TechCorp strengths |
| "I don't know" | Sounds incompetent | "Let me find out for you" |
| Generic responses | Didn't address specific issue | Use KB search results directly |

---

## 5. Escalation Rules (Finalized)

### Triggers That Worked Correctly

| # | Trigger | Condition | Result |
|---|---------|-----------|--------|
| 1 | Legal keywords | "lawyer", "attorney", "sue", "lawsuit" | ✅ Immediate escalation, P0 |
| 2 | Refund keywords | "refund", "chargeback", "cancel subscription" | ✅ Immediate escalation, P1 |
| 3 | Low sentiment | Sentiment score < 0.3 | ✅ Immediate escalation, P1 |
| 4 | Human requested | "human", "agent", "representative" on WhatsApp | ✅ Immediate escalation, P2 |
| 5 | Compliance keywords | "GDPR", "HIPAA", "SOC 2" | ✅ Immediate escalation, P1 |
| 6 | Pricing negotiation | "discount", "custom pricing", "bulk pricing" | ✅ Escalate to sales, P2 |
| 7 | Competitor mention | "Asana", "Monday.com", "Notion" comparison | ✅ Escalate to product specialist, P3 |

### Triggers That Needed Refinement

| # | Original | Refined | Reason |
|---|----------|---------|--------|
| 1 | Any billing question → escalate | Only refund/cancel → escalate | General billing questions (how to invoice) can be answered |
| 2 | Any bug report → escalate | Only engineering bugs → escalate | Workarounds can be provided for many bugs |
| 3 | Any enterprise question → escalate | Only custom features → escalate | Standard enterprise features can be explained from docs |

---

## 6. Performance Baseline

From prototype testing on 55 sample tickets:

| Metric | Value | Notes |
|--------|-------|-------|
| Average processing time | 50ms | Keyword search only (no LLM) |
| Knowledge base hit rate | 72% | Correct KB match for 40/55 tickets |
| Correct escalation rate | 89% | Correctly escalated 16/18 escalation-needed tickets |
| False escalation rate | 8% | Incorrectly escalated 3/37 non-escalation tickets |
| Empty message handling | 100% | All 2 empty messages handled gracefully |
| Channel formatting accuracy | 95% | Correct format for 52/55 tickets |
| Customer identification rate | 93% | Correctly identified 51/55 customers |

**Expected Production Metrics (with LLM):**
- Processing time: 1-3 seconds (LLM call adds latency)
- KB hit rate: > 85% (semantic search with pgvector)
- Correct escalation rate: > 95% (LLM better at context understanding)
- False escalation rate: < 5% (LLM better at nuance)

---

## 7. Pre-Transition Checklist

### From Incubation (Must Have Before Proceeding)

- [x] Working prototype that handles basic queries
- [x] Documented edge cases (20 identified)
- [x] Working system prompt
- [x] MCP tools defined and tested (7 tools)
- [x] Channel-specific response patterns identified
- [x] Escalation rules finalized
- [x] Performance baseline measured

### Transition Steps

- [x] Created production folder structure
- [x] Extracted prompts to prompts.py (in prototype)
- [x] Converted MCP tools to @function_tool format (in mcp_server.py)
- [x] Added Pydantic input validation to all tools (in MCP schema)
- [x] Added error handling to all tools (try/catch in all handlers)
- [x] Created transition test suite (documented in discovery log)
- [ ] All transition tests passing (will run in Phase 3)

### Ready for Production Build

- [x] Database schema designed (see Phase 2 plan)
- [x] Kafka topics defined (7 topics)
- [x] Channel handlers outlined (3 handlers)
- [x] Kubernetes resource requirements estimated
- [x] API endpoints listed (8+ endpoints)

---

## 8. Code Mapping: Incubation → Production

| Incubation Component | Production Component | Changes Needed |
|---------------------|---------------------|----------------|
| `prototype.py` | `production/agent/customer_success_agent.py` | Replace keyword search with pgvector, use OpenAI SDK |
| `mcp_server.py` | `production/agent/tools.py` | Convert to @function_tool, add Pydantic schemas |
| `memory_manager.py` | `production/database/queries.py` | Replace in-memory with PostgreSQL queries |
| `agent_skills.py` | `production/agent/tools.py` | Convert skills to @function_tool functions |
| Print statements | Structured logging | Use Python logging module |
| Local JSON state | PostgreSQL | Full relational schema |
| Simple sentiment | OpenAI sentiment or dedicated model | More accurate analysis |
| Keyword KB search | pgvector semantic search | Vector embeddings |

---

## 9. Common Mistakes to Avoid

| Mistake | Why It Happens | How We're Avoiding |
|---------|---------------|-------------------|
| Skipping documentation | "I remember what worked" | All discoveries documented in this file |
| Copying code directly | "It worked in prototype" | Refactoring for production patterns |
| Ignoring edge cases | "We'll fix those later" | 20 edge cases documented with test cases |
| Hardcoding values | "Just for now" | Using config/env vars from day 1 |
| No error handling | "It didn't crash before" | Try/catch with fallbacks in all tools |
| Forgetting channel differences | "One response fits all" | Testing each channel separately |

---

*Transition checklist complete. Ready to proceed to Phase 2: Specialization.*
