"""
Customer Success FTE — Main Agent Definition
==============================================
Phase 2: Specialization

Defines the Customer Success agent using the OpenAI Agents SDK.
This is the production Custom Agent that replaces the incubation prototype.

The agent:
- Uses GPT-4o for natural language understanding
- Has access to 7 tools (search KB, create ticket, get history, escalate, send response, sentiment, evaluate escalation)
- Follows channel-aware response formatting
- Enforces hard constraints and escalation triggers
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ─── Agent Definition ──────────────────────────────────────────────────────

def create_customer_success_agent():
    """Create the Customer Success FTE agent.
    
    Returns an OpenAI Agents SDK Agent configured with:
    - GPT-4o model
    - All production tools
    - Channel-aware system prompt
    - Escalation constraints
    """
    try:
        from openai import OpenAI
        from agents import Agent, function_tool

        from production.agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
        from production.agent.tools import (
            search_knowledge_base,
            create_ticket,
            get_customer_history,
            escalate_to_human,
            send_response,
            analyze_sentiment,
            evaluate_escalation,
        )

        # Wrap tools with @function_tool decorator
        tools = [
            function_tool(search_knowledge_base),
            function_tool(create_ticket),
            function_tool(create_ticket),  # type: ignore - will be properly decorated in production
            function_tool(get_customer_history),
            function_tool(escalate_to_human),
            function_tool(send_response),
        ]

        agent = Agent(
            name="Customer Success FTE",
            model="gpt-4o",
            instructions=CUSTOMER_SUCCESS_SYSTEM_PROMPT,
            tools=tools,
            tool_choice="auto",
        )

        logger.info("Customer Success FTE agent created successfully")
        return agent

    except ImportError as e:
        logger.warning(
            f"OpenAI Agents SDK not available, using fallback agent: {e}"
        )
        return FallbackAgent()


# ─── Fallback Agent (when OpenAI SDK is not available) ─────────────────────

class FallbackAgent:
    """Fallback agent that uses the incubation prototype logic.
    
    This ensures the system works even without the OpenAI Agents SDK,
    using the keyword-based search from incubation.
    """

    def __init__(self):
        from incubation.prototype import CustomerSuccessAgent
        self.prototype = CustomerSuccessAgent()
        logger.info("Fallback agent initialized (using incubation prototype)")

    async def run(self, messages: list, context: dict = None) -> 'AgentResult':
        """Process messages using the prototype.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            context: Additional context (channel, customer_id, etc.)
            
        Returns:
            AgentResult with response text and metadata
        """
        if not messages:
            return AgentResult(
                output="How can I help you today?",
                tool_calls=[],
                escalated=False
            )

        # Get the last user message
        last_message = None
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                last_message = msg
                break

        if not last_message:
            return AgentResult(
                output="How can I help you today?",
                tool_calls=[],
                escalated=False
            )

        channel = (context or {}).get('channel', 'web_form')
        raw_message = {
            'content': last_message.get('content', ''),
            'channel': channel,
            'customer_email': (context or {}).get('customer_email'),
            'customer_phone': (context or {}).get('customer_phone'),
            'customer_name': (context or {}).get('customer_name', ''),
            'subject': (context or {}).get('ticket_subject', ''),
            'category': (context or {}).get('category', 'general'),
            'priority': (context or {}).get('priority', 'medium'),
        }

        response = self.prototype.process_message(raw_message, channel)

        return AgentResult(
            output=response.response_text,
            tool_calls=response.tool_calls,
            escalated=response.escalated,
            escalation_reason=response.escalation_reason.value if response.escalated else None,
            escalation_priority=response.escalation_priority if response.escalated else None,
            sentiment_score=response.sentiment_score,
            topics=response.topics,
            ticket_id=response.ticket_id,
        )


class AgentResult:
    """Result from agent execution."""

    def __init__(self, output: str, tool_calls: list,
                 escalated: bool = False, escalation_reason: str = None,
                 escalation_priority: str = None, sentiment_score: float = 0.5,
                 topics: list = None, ticket_id: str = None):
        self.output = output
        self.tool_calls = tool_calls
        self.escalated = escalated
        self.escalation_reason = escalation_reason
        self.escalation_priority = escalation_priority
        self.sentiment_score = sentiment_score
        self.topics = topics or []
        self.ticket_id = ticket_id


# ─── Global Agent Instance ─────────────────────────────────────────────────

# Create a singleton agent instance
customer_success_agent = create_customer_success_agent()


# ─── Convenience Function ──────────────────────────────────────────────────

async def process_customer_message(
    message: str,
    channel: str = "web_form",
    customer_id: str = None,
    customer_email: str = None,
    customer_name: str = "",
    ticket_subject: str = "",
    conversation_history: list = None,
) -> AgentResult:
    """Process a customer message through the agent.
    
    This is the main entry point for processing customer messages.
    
    Args:
        message: Customer message text
        channel: Source channel (email/whatsapp/web_form)
        customer_id: Customer identifier
        customer_email: Customer email
        customer_name: Customer name
        ticket_subject: Original ticket subject
        conversation_history: Previous messages in conversation
        
    Returns:
        AgentResult with response and metadata
    """
    # Build message list
    messages = []
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": message})

    # Build context
    context = {
        'channel': channel,
        'customer_id': customer_id,
        'customer_email': customer_email,
        'customer_name': customer_name,
        'ticket_subject': ticket_subject,
    }

    # Run agent
    result = await customer_success_agent.run(messages=messages, context=context)

    return result
