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
import os
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

        tools = [
            function_tool(search_knowledge_base),
            function_tool(create_ticket),
            function_tool(get_customer_history),
            function_tool(escalate_to_human),
            function_tool(send_response),
            function_tool(analyze_sentiment),
            function_tool(evaluate_escalation),
        ]

        agent = Agent(
            name="Customer Success FTE",
            model="gpt-4o",
            instructions=CUSTOMER_SUCCESS_SYSTEM_PROMPT,
            tools=tools,
        )

        logger.info("Customer Success FTE agent created successfully (OpenAI Agents SDK)")
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
                 topics: list = None, ticket_id: str = None,
                 model_used: str = None, api_used: str = None):
        self.output = output
        self.tool_calls = tool_calls
        self.escalated = escalated
        self.escalation_reason = escalation_reason
        self.escalation_priority = escalation_priority
        self.sentiment_score = sentiment_score
        self.topics = topics or []
        self.ticket_id = ticket_id
        self.model_used = model_used or "unknown"
        self.api_used = api_used or "unknown"


# ─── Global Agent Instance ─────────────────────────────────────────────────

# Create a singleton agent instance
customer_success_agent = create_customer_success_agent()


# ─── Convenience Function ──────────────────────────────────────────────────

def _detect_escalation(message: str) -> tuple[bool, str | None]:
    """Detect if a message requires escalation based on keywords.
    
    Returns (escalated: bool, reason: str | None)
    """
    msg = message.lower()

    legal_keywords = ["sue", "lawyer", "attorney", "legal action", "lawsuit", "court"]
    if any(k in msg for k in legal_keywords):
        return True, "legal_threat"

    refund_keywords = ["refund", "money back", "chargeback", "dispute charge", "reimburse"]
    if any(k in msg for k in refund_keywords):
        return True, "refund_request"

    human_keywords = ["speak to human", "talk to human", "real person", "human agent",
                      "speak to agent", "talk to agent", "human support", "live agent"]
    if any(k in msg for k in human_keywords):
        return True, "human_requested"

    angry_keywords = ["worst", "garbage", "terrible", "hate", "furious", "disgusting",
                      "outrageous", "scam", "fraud", "useless", "pathetic", "unacceptable"]
    if any(k in msg for k in angry_keywords):
        return True, "angry_customer"

    competitor_keywords = ["asana", "monday.com", "jira", "salesforce", "hubspot",
                           "zendesk", "freshdesk", "competitor", "compare to", "better than"]
    if any(k in msg for k in competitor_keywords):
        return True, "competitor_inquiry"

    pricing_keywords = ["pricing", "negotiat", "discount", "enterprise plan", "custom plan"]
    if any(k in msg for k in pricing_keywords):
        return True, "pricing_negotiation"

    return False, None


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

    # Pre-detect escalation from message keywords (works regardless of AI model)
    escalated, escalation_reason = _detect_escalation(message)

    # Run agent — use SDK Runner if available, else fallback .run()
    try:
        from agents import Runner
        sdk_result = await Runner.run(customer_success_agent, input=message)
        return AgentResult(
            output=sdk_result.final_output or "",
            tool_calls=[],
            escalated=escalated,
            escalation_reason=escalation_reason,
            sentiment_score=0.5,
            topics=["general"],
            ticket_id="TK-2026-0001",
            model_used="gpt-4o",
            api_used="OpenAI",
        )
    except ImportError:
        pass
    except Exception as sdk_err:
        logger.warning(f"OpenAI Agents SDK call failed ({sdk_err}), trying Groq fallback")

    # Groq fallback — free LLM via OpenAI-compatible API
    groq_key = os.getenv("GROQ_API_KEY", "")
    if groq_key:
        try:
            from groq import AsyncGroq
            from production.agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
            groq_client = AsyncGroq(api_key=groq_key)
            channel = context.get("channel", "web_form") if context else "web_form"
            groq_resp = await groq_client.chat.completions.create(
                model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                messages=[
                    {"role": "system", "content": CUSTOMER_SUCCESS_SYSTEM_PROMPT},
                    {"role": "user", "content": f"[Channel: {channel}]\n\n{message}"},
                ],
                max_tokens=1024,
                temperature=0.3,
            )
            response_text = groq_resp.choices[0].message.content
            groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
            logger.info(f"Groq responded via {groq_model}")
            return AgentResult(
                output=response_text,
                tool_calls=[],
                escalated=escalated,
                escalation_reason=escalation_reason,
                sentiment_score=0.5,
                topics=["general"],
                ticket_id="TK-2026-0001",
                model_used=groq_model,
                api_used="Groq",
            )
        except Exception as groq_err:
            logger.warning(f"Groq fallback failed ({groq_err}), using prototype agent")

    # OpenRouter fallback — cycles through all configured free models
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
    if openrouter_key:
        import openai as openai_lib
        from production.agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
        or_client = openai_lib.AsyncOpenAI(
            api_key=openrouter_key,
            base_url="https://openrouter.ai/api/v1",
        )
        channel = context.get("channel", "web_form") if context else "web_form"
        primary = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
        extras = os.getenv("OPENROUTER_FALLBACK_MODELS", "")
        or_models = [primary] + [m.strip() for m in extras.split(",") if m.strip()]
        for or_model in or_models:
            try:
                or_resp = await or_client.chat.completions.create(
                    model=or_model,
                    messages=[
                        {"role": "system", "content": CUSTOMER_SUCCESS_SYSTEM_PROMPT},
                        {"role": "user", "content": f"[Channel: {channel}]\n\n{message}"},
                    ],
                    max_tokens=1024,
                    temperature=0.3,
                )
                response_text = or_resp.choices[0].message.content
                logger.info(f"OpenRouter responded via {or_model}")
                return AgentResult(
                    output=response_text,
                    tool_calls=[],
                    escalated=escalated,
                    escalation_reason=escalation_reason,
                    sentiment_score=0.5,
                    topics=["general"],
                    ticket_id="TK-2026-0001",
                    model_used=or_model,
                    api_used="OpenRouter",
                )
            except Exception as or_err:
                logger.warning(f"OpenRouter model {or_model} failed ({or_err}), trying next")
        logger.warning("All OpenRouter models failed, using prototype agent")

    # Final fallback: prototype agent (no external API calls)
    fallback = FallbackAgent()
    result = await fallback.run(messages=messages, context=context)
    result.model_used = "prototype"
    result.api_used = "Local Prototype"
    return result
