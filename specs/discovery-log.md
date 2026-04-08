# Discovery Log — Requirements Found During Incubation

> **Date:** April 7, 2026
> **Phase:** Incubation (Phase 1)
> **Method:** Analysis of 55 sample customer tickets across 3 channels + prototype iteration

---

## 1. Initial Exploration Summary

### 1.1 Sample Ticket Analysis

We analyzed **55 sample customer tickets** across three channels:

| Channel | Count | Characteristics |
|---------|-------|----------------|
| Email | 22 | Longer messages (avg 150 words), formal tone, includes signatures, detailed context |
| WhatsApp | 18 | Short messages (avg 12 words), casual tone, often urgent, sometimes typos |
| Web Form | 15 | Structured (category + priority selected), medium length (avg 80 words), clear subjects |

### 1.2 Pattern Discovery

**Top Issue Categories Found:**

| Category | Count | % | Can AI Handle? |
|----------|-------|---|---------------|
| How-to / Feature Questions | 18 | 33% | ✅ Yes |
| Technical / Bug Reports | 10 | 18% | ⚠️ Partially (troubleshoot + escalate) |
| Billing / Pricing | 8 | 15% | ❌ No (escalate) |
| Account Management | 6 | 11% | ✅ Yes |
| Feedback / Suggestions | 5 | 9% | ✅ Yes (acknowledge) |
| Compliance / Legal | 4 | 7% | ❌ No (escalate) |
| General / Other | 4 | 7% | ⚠️ Depends |

**Key Discovery: 60-70% of tickets can be handled autonomously by AI.**

### 1.3 Channel-Specific Patterns

**Email Patterns:**
- Customers include full context (account details, steps to reproduce)
- Formal greetings and sign-offs are expected
- Longer, detailed responses are acceptable
- Ticket references in signature are helpful
- Average response should be 200-500 words

**WhatsApp Patterns:**
- Very short messages (often one sentence)
- Customers expect quick, actionable answers
- Emojis are acceptable (but limited to 1-2)
- Responses over 300 characters feel too long
- Customers may type "human" or "agent" to request live help

**Web Form Patterns:**
- Structured input (category, priority pre-selected)
- Customers write more than WhatsApp but less than email
- Semi-formal tone is appropriate
- Success confirmation with ticket ID is expected
- Customers check status after submission

---

## 2. Requirements Discovered

### 2.1 Functional Requirements

| ID | Requirement | Priority | Source |
|----|------------|----------|--------|
| FR-01 | Must accept messages from Gmail, WhatsApp, and Web Form | Critical | Spec |
| FR-02 | Must normalize messages from all channels into unified format | Critical | Prototype testing |
| FR-03 | Must search knowledge base for relevant information | Critical | Sample ticket analysis |
| FR-04 | Must create a ticket for every interaction | Critical | Spec |
| FR-05 | Must track customer history across ALL channels | Critical | Cross-channel pattern discovery |
| FR-06 | Must analyze sentiment of every message | High | Escalation rules |
| FR-07 | Must decide when to escalate to human | Critical | Escalation rules analysis |
| FR-08 | Must format responses appropriately per channel | Critical | Channel pattern analysis |
| FR-09 | Must identify customers by email or phone | High | Customer data analysis |
| FR-10 | Must handle empty or meaningless messages gracefully | Medium | Edge case: sample-026, sample-027 |
| FR-11 | Must never discuss competitor products | High | Escalation rules |
| FR-12 | Must never promise features not in documentation | Critical | Guardrails |
| FR-13 | Must never process refunds — always escalate | Critical | Escalation rules |
| FR-14 | Must track topics discussed for reporting | Medium | Business value |
| FR-15 | Must provide ticket status checking | Medium | Web form pattern |

### 2.2 Non-Functional Requirements

| ID | Requirement | Target | Source |
|----|------------|--------|--------|
| NFR-01 | Response time (processing) | < 3 seconds | Spec |
| NFR-02 | Response time (delivery) | < 30 seconds | Spec |
| NFR-03 | Accuracy on test set | > 85% | Spec |
| NFR-04 | Escalation rate | < 20% | Spec |
| NFR-05 | Cross-channel identification accuracy | > 95% | Spec |
| NFR-06 | System uptime | > 99.9% | 24/7 requirement |
| NFR-07 | No message loss | 0 messages | 24-hour test criteria |
| NFR-08 | Survive pod restarts | Yes | Kubernetes deployment |

### 2.3 Channel-Specific Requirements

| ID | Requirement | Email | WhatsApp | Web Form |
|----|------------|-------|----------|----------|
| CSR-01 | Max response length | 2000 chars | 1600 chars | 1000 chars |
| CSR-02 | Preferred response length | 500 words | 300 chars | 300 words |
| CSR-03 | Greeting required | Yes (formal) | Yes (casual) | No |
| CSR-04 | Signature required | Yes | No | Yes (brief) |
| CSR-05 | Emojis allowed | No | Yes (1-2 max) | No |
| CSR-06 | Authentication | Email headers | Twilio signature | None |

---

## 3. Edge Cases Discovered

| # | Edge Case | Channel | Handling Strategy | Test Case |
|---|-----------|---------|-------------------|-----------|
| 1 | Empty message (no content) | All | Ask for clarification politely | sample-026 |
| 2 | Meaningless message ("????") | WhatsApp | Ask for clarification, casual tone | sample-027 |
| 3 | Test message ("just testing") | Web | Acknowledge briefly | sample-028 |
| 4 | Competitor comparison request | Email | Don't discuss competitors, pivot to strengths | sample-029 |
| 5 | Extreme anger + legal threat | Email | Immediate escalation, empathetic acknowledgment | sample-030 |
| 6 | Customer explicitly requests human | WhatsApp | Immediate escalation, confirm handoff | sample-015, sample-037 |
| 7 | Pricing/discount inquiry | Web | Escalate to sales, don't negotiate | sample-006, sample-023 |
| 8 | Refund request | WhatsApp | Escalate to billing, acknowledge concern | sample-008 |
| 9 | Compliance/legal question | Web | Escalate to legal team | sample-013, sample-034 |
| 10 | Bug requiring engineering | Email | Troubleshoot first, then escalate with details | sample-024 |
| 11 | Positive feedback / thanks | WhatsApp | Acknowledge warmly, log for morale metrics | sample-025 |
| 12 | Onboarding request (new user) | WhatsApp | Provide quick start guide | sample-050 |
| 13 | Missing email in message | Email | Use email from headers/metadata | — |
| 14 | Same customer, different channels | All | Detect and merge conversations | — |
| 15 | Very long customer message | Email | Process fully, but keep response concise | — |
| 16 | Message with attachments | Email | Acknowledge receipt, note attachment in ticket | — |
| 17 | Duplicate submission | Web | Detect similar recent tickets, reference them | — |
| 18 | Out-of-hours submission | All | Still respond (24/7 requirement) | — |
| 19 | Multiple questions in one message | Email | Address each question or prioritize the main one | — |
| 20 | Customer provides wrong info | All | Politely correct based on available data | — |

---

## 4. Escalation Rules (Finalized from Testing)

### 4.1 Immediate Escalation Triggers (AI should NOT respond)

1. Legal threats: "lawyer", "attorney", "sue", "lawsuit", "breach of contract"
2. Refund/cancellation: "refund", "chargeback", "cancel subscription"
3. Compliance: "GDPR", "HIPAA", "SOC 2", "compliance", "data retention"
4. Sentiment score < 0.3 (very negative)
5. Customer explicitly requests human on WhatsApp

### 4.2 Escalate After AI Response

1. Bug reports that need engineering investigation
2. Enterprise feature inquiries (SSO, white-labeling, custom SLAs)
3. Security audit requests
4. Account access issues (locked, expired)
5. Competitor comparison questions

### 4.3 AI Handles Fully

1. Password resets
2. How-to questions
3. Feature explanations
4. Bug workarounds
5. Feedback/suggestions
6. Onboarding help
7. Documentation requests
8. Status checks

---

## 5. Response Patterns Discovered

### 5.1 What Worked Well

| Pattern | Channel | Effectiveness |
|---------|---------|--------------|
| Step-by-step numbered instructions | Email | ✅ Excellent |
| Direct, concise answers | WhatsApp | ✅ Excellent |
| Acknowledgment before solution | All | ✅ Excellent |
| Offering additional help at end | All | ✅ Good |
| Ticket reference in email signature | Email | ✅ Good |
| Emoji in WhatsApp (1 max) | WhatsApp | ✅ Good |
| Linking to documentation | All | ✅ Good (when relevant) |

### 5.2 What Didn't Work

| Pattern | Problem | Fix |
|---------|---------|-----|
| Long responses on WhatsApp | Too verbose, customer loses interest | Truncate to 300 chars |
| No acknowledgment of frustration | Felt robotic | Add empathy first |
| Discussing competitor features | Against policy, creates liability | Pivot to TechCorp strengths |
| Saying "I don't know" | Sounds incompetent | Say "Let me find out" |
| Generic responses | Didn't address specific issue | Use KB search results |

---

## 6. Performance Baseline (From Prototype Testing)

| Metric | Value | Notes |
|--------|-------|-------|
| Average processing time | 50ms | Keyword search, no LLM |
| Knowledge base hit rate | 72% | On sample ticket set |
| Correct escalation rate | 89% | On escalation-required tickets |
| False escalation rate | 8% | Escalated when shouldn't have |
| Empty message handling | 100% | All handled gracefully |
| Channel formatting accuracy | 95% | Correct format per channel |

**Note:** These metrics are from the keyword-based prototype. Production metrics with LLM will differ.

---

## 7. Architecture Insights

### 7.1 Key Design Decisions

1. **Email as primary customer identifier** — Most customers have email, even WhatsApp customers can be linked via email later
2. **Conversation window of 24 hours** — Messages within 24h of each other are part of the same conversation
3. **Sentiment as primary escalation signal** — Negative sentiment is the strongest single indicator that escalation is needed
4. **Channel metadata must be preserved end-to-end** — From intake through response, channel info is critical
5. **Knowledge base search must be fast** — < 100ms for search to meet overall < 3s response time

### 7.2 Data Flow Discovered

```
Incoming Message → Normalize → Identify Customer → Check History
    → Analyze Sentiment → Search KB → Generate Response
    → Check Escalation → Format for Channel → Send → Store
```

### 7.3 State Requirements

- Customer records (persistent)
- Conversation threads (persistent)
- Message history (persistent)
- Sentiment scores (persistent, for trending)
- Ticket status (persistent)
- Knowledge base (persistent, versioned)
- Agent metrics (persistent, time-series)

---

## 8. Open Questions for Production

1. How to handle customers who contact via email AND WhatsApp about the same issue simultaneously?
2. What is the fallback if knowledge base search returns no results AND no human is available?
3. How to handle rate limiting on external APIs (Gmail, Twilio)?
4. What is the maximum conversation length before context becomes too large for LLM?
5. How to handle multi-language support?
6. What is the data retention policy for conversation history?
7. How to implement A/B testing for response quality?

---

## 9. Iteration Log

| Iteration | Change | Result |
|-----------|--------|--------|
| 1 | Basic keyword search | 72% hit rate on sample set |
| 2 | Added category filtering | Improved precision by 10% |
| 3 | Added sentiment analysis | Correctly identified 8/10 angry customers |
| 4 | Added escalation engine | 89% correct escalation decisions |
| 5 | Added channel formatting | All 3 channels formatted correctly |
| 6 | Added empty message handling | 100% graceful handling |
| 7 | Added customer identification | Cross-channel linking working |
| 8 | Added MCP server tools | All 7 tools functional |

---

*End of Discovery Log*
