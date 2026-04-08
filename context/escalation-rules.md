# Escalation Rules — When to Involve Human Agents

## Overview

The Digital FTE should handle routine inquiries autonomously but escalate appropriately. This document defines the escalation rules discovered during analysis of sample tickets.

---

## 🔴 IMMEDIATE ESCALATION (No AI Response — Route to Human)

These triggers require immediate escalation. The AI should NOT attempt to respond.

| Trigger | Keywords/Conditions | Reason | Example |
|---------|-------------------|--------|---------|
| **Legal Threat** | "lawyer", "attorney", "sue", "lawsuit", "legal action", "court", "breach of contract" | Legal liability risk | "I'm suing for breach of contract" |
| **Refund Request** | "refund", "chargeback", "dispute charge", "cancel subscription" | Financial authority required | "Can I get a refund for unused months?" |
| **Pricing Negotiation** | "discount", "negotiate price", "custom pricing", "bulk pricing" | Sales team required | "Do you offer nonprofit discounts?" |
| **Compliance/Legal** | "GDPR", "HIPAA", "SOC 2", "compliance", "data retention policy", "BAA" | Legal/compliance team required | "Are you HIPAA compliant?" |
| **Aggressive Language** | Profanity, all-caps rage, threats | Customer needs human empathy | "your product is complete GARBAGE" |
| **Sentiment Score < 0.3** | AI-detected negative sentiment | Emotional intelligence required | Customer expressing extreme frustration |
| **Explicit Human Request** | "human", "agent", "representative", "real person", "speak to someone" | Customer preference | "I want to speak to a human agent" |

---

## 🟡 ESCALATION WITH AI CONTEXT (AI Responds First, Then Escalates)

The AI should provide an initial response and then flag for human follow-up.

| Trigger | Condition | AI Action | Human Follow-up |
|---------|-----------|-----------|-----------------|
| **Bug Requiring Engineering** | Bug report that needs code fix or investigation | Acknowledge, gather details, create ticket | Engineering investigation |
| **Enterprise Feature Inquiry** | Questions about SSO, white-labeling, custom SLAs | Provide available info | Sales/engineering deep-dive |
| **Data Residency Questions** | Questions about where data is stored | Provide public info | Compliance team confirmation |
| **Security Audit Requests** | SOC 2, penetration test reports | Acknowledge request | Security team provides documents |
| **Account Access Issues** | Can't log in, expired subscription, locked account | Attempt troubleshooting | Account team intervention |
| **Multi-Channel Confusion** | Customer contacted on 2+ channels with same issue | Acknowledge and consolidate | Support manager review |

---

## 🟢 AI HANDLES AUTONOMOUSLY (No Escalation)

The AI should handle these entirely without human involvement.

| Category | Examples | Expected Behavior |
|----------|----------|-------------------|
| **Password Reset** | "Forgot password", "Can't log in" | Guide through reset process |
| **How-To Questions** | "How do I create a project?", "How to add team members?" | Provide step-by-step guidance from docs |
| **Feature Questions** | "What does automation do?", "API rate limits?" | Answer from product documentation |
| **Bug Workarounds** | "Timeline view not loading" | Suggest troubleshooting steps |
| **Feedback/Suggestions** | "Love the product!", "Feature request: dark mode" | Acknowledge, thank, log feedback |
| **Account Setup** | "Just signed up, help me get started" | Provide onboarding guidance |
| **Documentation Requests** | "API examples", "How to use webhooks" | Provide documentation links and examples |
| **Status Checks** | "Is the system down?", "When will it be back up?" | Check status page, provide info |

---

## Escalation Priority Matrix

| Severity | Response Time | Examples |
|----------|--------------|----------|
| **P0 — Critical** | < 15 minutes | Legal threats, system outage, data breach |
| **P1 — High** | < 1 hour | Angry customer, billing disputes, compliance |
| **P2 — Medium** | < 4 hours | Bug reports, enterprise inquiries, account issues |
| **P3 — Low** | < 24 hours | Feature requests, general feedback, non-urgent questions |

---

## Escalation Data Format

When escalating, the AI must include:

```json
{
  "ticket_id": "uuid",
  "escalation_reason": "pricing_inquiry",
  "priority": "P2",
  "customer_id": "uuid",
  "channel": "email",
  "conversation_summary": "Customer asked about nonprofit discounts",
  "sentiment_score": 0.6,
  "ai_actions_taken": ["searched_knowledge_base", "checked_pricing_docs"],
  "full_conversation_history": [...],
  "suggested_human_team": "sales",
  "escalated_at": "2026-04-07T10:30:00Z"
}
```

---

## Escalation Routing

| Reason | Route To |
|--------|----------|
| pricing_inquiry, discount_request | Sales Team |
| refund_request, billing_dispute | Billing Team |
| legal_threat, gdpr_request, compliance | Legal/Compliance |
| bug_engineering, outage_report | Engineering |
| angry_customer, sentiment_low | Senior Support Agent |
| human_requested | Next Available Agent |
| enterprise_inquiry | Sales + Engineering |
| security_audit | Security Team |

---

## Rules Learned from Sample Ticket Analysis

1. **20% of tickets require escalation** — mostly pricing, legal, and angry customers
2. **80% can be handled autonomously** — how-to, feature questions, bug workarounds
3. **Email tends to be more formal** — customers include signatures, detailed context
4. **WhatsApp is casual and urgent** — short messages, immediate needs
5. **Web form is structured** — customers fill out categories, tend to be more detailed
6. **Empty messages happen** — ~2% of submissions are empty or meaningless
7. **Competitor questions are traps** — never discuss competitor products in detail
8. **Sentiment is the best escalation signal** — negative sentiment + complaint = escalate
9. **Cross-channel customers exist** — same person may email and WhatsApp about same issue
10. **Feedback is valuable** — even simple "thanks" messages should be logged for morale metrics
