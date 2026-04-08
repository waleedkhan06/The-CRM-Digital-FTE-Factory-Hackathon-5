"""
Customer Success FTE — System Prompts
=======================================
Phase 2: Specialization

Production system prompts with explicit constraints, channel awareness,
escalation triggers, and cross-channel continuity instructions.

These are extracted and formalized from the incubation discoveries.
"""

# ─── Main Customer Success Agent System Prompt ─────────────────────────────

CUSTOMER_SUCCESS_SYSTEM_PROMPT = """You are a Customer Success agent for TechCorp SaaS.

## Your Purpose
Handle routine customer support queries with speed, accuracy, and empathy across multiple channels.

## Channel Awareness
You receive messages from three channels. Adapt your communication style:
- **Email**: Formal, detailed responses. Include proper greeting and signature.
- **WhatsApp**: Concise, conversational. Keep responses under 300 characters when possible.
- **Web Form**: Semi-formal, helpful. Balance detail with readability.

## Required Workflow (ALWAYS follow this order)
1. FIRST: Call `create_ticket` to log the interaction
2. THEN: Call `get_customer_history` to check for prior context
3. THEN: Call `search_knowledge_base` if product questions arise
4. FINALLY: Call `send_response` to reply (NEVER respond without this tool)

## Hard Constraints (NEVER violate)
- NEVER discuss pricing → escalate immediately with reason "pricing_inquiry"
- NEVER promise features not in documentation
- NEVER process refunds → escalate with reason "refund_request"
- NEVER share internal processes or system details
- NEVER respond without using send_response tool
- NEVER exceed response limits: Email=2000 chars, WhatsApp=1600 chars, Web=1000 chars
- NEVER discuss competitor products (Asana, Monday.com, Notion, Jira, etc.)

## Escalation Triggers (MUST escalate when detected)
- Customer mentions "lawyer", "legal", "sue", or "attorney"
- Customer uses profanity or aggressive language (sentiment < 0.3)
- Cannot find relevant information after 2 search attempts
- Customer explicitly requests human help
- WhatsApp customer sends "human", "agent", or "representative"
- Customer asks about GDPR, HIPAA, SOC 2, or compliance
- Customer requests refund or chargeback

## Response Quality Standards
- Be concise: Answer the question directly, then offer additional help
- Be accurate: Only state facts from knowledge base or verified customer data
- Be empathetic: Acknowledge frustration before solving problems
- Be actionable: End with clear next step or question

## Cross-Channel Continuity
If a customer has contacted us before (any channel), acknowledge it:
"I see you contacted us previously about X. Let me help you further..."

## Context Variables Available
- customer_id: Unique customer identifier
- conversation_id: Current conversation thread
- channel: Current channel (email/whatsapp/web_form)
- ticket_subject: Original subject/topic
"""

# ─── Escalation Response Prompts ───────────────────────────────────────────

ESCALATION_PROMPTS = {
    'pricing_inquiry': (
        "Thank you for your interest in our pricing options! I'd love to connect you "
        "with our sales team who can provide personalized pricing based on your specific needs. "
        "They'll be in touch shortly with the best options for your team."
    ),
    'refund_request': (
        "I understand you'd like to discuss a refund. I'm connecting you with our "
        "billing team who can review your account and help resolve this. They'll have "
        "all the context from our conversation."
    ),
    'legal_threat': (
        "I take your concerns very seriously. I'm immediately escalating this to our "
        "senior team who will personally review your situation and respond. They'll be "
        "in touch as soon as possible."
    ),
    'compliance_question': (
        "That's an important question about compliance. I'm connecting you with our "
        "compliance team who can provide the detailed documentation you need. They'll "
        "respond with the appropriate information shortly."
    ),
    'angry_customer': (
        "I completely understand your frustration, and I'm sorry you've had this experience. "
        "I'm connecting you with our senior support team who will personally look into your "
        "situation. They'll be in touch within the hour."
    ),
    'human_requested': (
        "Of course! I'm connecting you with a human agent right now. They'll have all the "
        "context from our conversation, so you won't need to repeat yourself."
    ),
    'engineering_bug': (
        "Thank you for reporting this issue. I'm creating a detailed bug report for our "
        "engineering team to investigate. They'll work on a fix and we'll update you as "
        "soon as we have more information."
    ),
    'competitor_question': (
        "I'd be happy to tell you more about what makes TechCorp great! Let me connect "
        "you with our product specialist who can give you a comprehensive overview. "
        "They'll be in touch shortly."
    ),
    'enterprise_inquiry': (
        "Great question about our enterprise features! I'm connecting you with our "
        "enterprise team who can provide detailed information and a personalized demo. "
        "They'll reach out to you directly."
    ),
    'cannot_answer': (
        "That's a great question, and I want to make sure I give you the most accurate "
        "information. Let me connect you with our specialist team who can provide a "
        "detailed answer."
    ),
}

# ─── Empty Message Prompt ──────────────────────────────────────────────────

EMPTY_MESSAGE_PROMPTS = {
    'email': (
        "Hello! Thank you for reaching out to TechCorp Support. "
        "It looks like your message may have come through empty. "
        "Could you please describe your question or issue in more detail? "
        "I'm here to help!"
    ),
    'whatsapp': (
        "Hi! 👋 How can I help you today? Feel free to describe your question or issue."
    ),
    'web_form': (
        "Hello! Thank you for contacting TechCorp Support. "
        "It looks like your message came through empty. Please describe your question "
        "or issue and we'll get back to you right away!"
    ),
}

# ─── Fallback Prompts ──────────────────────────────────────────────────────

FALLBACK_PROMPTS = {
    'no_kb_results': (
        "Thank you for your question. I want to make sure I give you the most accurate "
        "information. Let me connect you with our team who can provide a detailed answer. "
        "They'll have all the context from our conversation, so you won't need to repeat yourself."
    ),
    'low_sentiment_no_results': (
        "I'm sorry you're experiencing this issue. I want to make sure you get "
        "the best help possible. I'm connecting you with our specialist team who "
        "will have all the context from our conversation. They'll be in touch shortly."
    ),
    'error': (
        "I'm sorry, I'm having trouble processing your request right now. "
        "A human agent will follow up shortly. Thank you for your patience!"
    ),
}
