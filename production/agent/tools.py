"""
Customer Success FTE — Production Tool Definitions
====================================================
Phase 2: Specialization

All @function_tool definitions for the OpenAI Agents SDK.
These replace the MCP server tools from incubation with:
- Strict Pydantic input schemas
- Comprehensive error handling with fallbacks
- Structured logging
- PostgreSQL database integration
"""

import logging
import json
from typing import Optional
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ─── Input Schemas ─────────────────────────────────────────────────────────

class Channel(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEB_FORM = "web_form"


class KnowledgeSearchInput(BaseModel):
    """Input schema for knowledge base search."""
    query: str = Field(..., description="The search query from the customer message")
    max_results: int = Field(default=5, description="Maximum number of results to return")
    category: Optional[str] = Field(
        default=None,
        description="Optional category filter (account, billing, technical, etc.)"
    )


class TicketInput(BaseModel):
    """Input schema for ticket creation."""
    customer_id: str = Field(..., description="Unique customer identifier")
    issue: str = Field(..., description="Description of the customer issue")
    priority: str = Field(default="medium", description="Ticket priority (low, medium, high, urgent)")
    channel: Channel = Field(..., description="Source channel of the inquiry")
    category: Optional[str] = Field(default="general", description="Issue category")


class EscalationInput(BaseModel):
    """Input schema for escalation."""
    ticket_id: str = Field(..., description="The ticket/conversation ID to escalate")
    reason: str = Field(
        ...,
        description="Reason for escalation (pricing_inquiry, refund_request, legal_threat, etc.)"
    )
    urgency: str = Field(default="P2", description="Escalation urgency level (P0-P3)")


class ResponseInput(BaseModel):
    """Input schema for sending response."""
    ticket_id: str = Field(..., description="The ticket/conversation ID")
    message: str = Field(..., description="The response message to send")
    channel: Channel = Field(..., description="Channel to send via")


# ─── Tool Functions ────────────────────────────────────────────────────────
# These will be decorated with @function_tool when OpenAI Agents SDK is used.
# For now, they're regular async functions that can be tested independently.

async def search_knowledge_base(input: KnowledgeSearchInput) -> str:
    """Search product documentation for relevant information.

    Use this when the customer asks questions about product features,
    how to use something, or needs technical information.

    Args:
        input: Search parameters including query and optional filters

    Returns:
        Formatted search results with relevance scores
    """
    try:
        from production.database.queries import search_knowledge_base as db_search

        results = await db_search(
            query=input.query,
            max_results=input.max_results,
            category=input.category
        )

        if not results:
            return (
                f"No relevant documentation found for: \"{input.query}\". "
                "Consider escalating to human support or asking the customer for more details."
            )

        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(
                f"**{r['title']}** (relevance: {r['score']:.2f}, category: {r['category']})\n"
                f"{r['content']}"
            )

        return "\n\n---\n\n".join(formatted)

    except Exception as e:
        logger.error(f"Knowledge base search failed: {e}")
        return (
            "Knowledge base temporarily unavailable. Please try again or escalate. "
            f"Error: {str(e)[:100]}"
        )


async def create_ticket(input: TicketInput) -> str:
    """Create a support ticket for tracking.

    ALWAYS create a ticket at the start of every conversation.
    Include the source channel for proper tracking.

    Args:
        input: Ticket parameters with customer info and channel

    Returns:
        Ticket ID and confirmation
    """
    try:
        from production.database.queries import (
            get_or_create_customer,
            create_conversation,
            create_ticket as db_create_ticket
        )

        # Get or create customer
        customer = await get_or_create_customer(
            email=input.customer_id if '@' in input.customer_id else None,
            phone=input.customer_id if '+' in input.customer_id else None,
            name=input.customer_id
        )

        # Create conversation
        conversation = await create_conversation(
            customer_id=customer['id'],
            channel=input.channel.value,
            metadata={'subject': input.issue[:100]}
        )

        # Create ticket
        ticket = await db_create_ticket(
            conversation_id=conversation['id'],
            customer_id=customer['id'],
            source_channel=input.channel.value,
            category=input.category,
            priority=input.priority
        )

        return (
            f"Ticket created successfully.\n"
            f"Ticket ID: {ticket['id']}\n"
            f"Customer ID: {customer['id']}\n"
            f"Channel: {input.channel.value}\n"
            f"Conversation ID: {conversation['id']}\n"
            f"Priority: {input.priority}\n"
            f"Status: open"
        )

    except Exception as e:
        logger.error(f"Ticket creation failed: {e}")
        return f"Error creating ticket: {str(e)[:200]}"


async def get_customer_history(customer_id: str) -> str:
    """Get customer's complete interaction history across ALL channels.

    Use this to understand context from previous conversations,
    even if they happened on a different channel.

    Args:
        customer_id: Unique customer identifier (email or UUID)

    Returns:
        Formatted customer history with conversation summaries
    """
    try:
        from production.database.queries import (
            get_or_create_customer,
            get_customer_history as db_history
        )

        # Resolve customer
        customer = await get_or_create_customer(
            email=customer_id if '@' in customer_id else None,
            phone=customer_id if '+' in customer_id else None,
            name=customer_id
        )

        history = await db_history(customer['id'], limit=20)

        if 'error' in history:
            return f"Error: {history['error']}"

        if history['total_conversations'] == 0:
            return "No previous interactions found for this customer."

        lines = [
            f"Customer: {history['customer'].get('name', 'Unknown')}",
            f"Email: {history['customer'].get('email', 'N/A')}",
            f"Phone: {history['customer'].get('phone', 'N/A')}",
            f"Total conversations: {history['total_conversations']}",
            f"Average sentiment: {history['customer'].get('avg_sentiment', 0.5):.2f}",
            ""
        ]

        for conv in history['conversations']:
            lines.append(
                f"Conversation {str(conv['id'])[:8]}... | "
                f"Channel: {conv['initial_channel']} | "
                f"Status: {conv['status']} | "
                f"Sentiment: {conv['sentiment_score']:.2f} | "
                f"Messages: {conv['message_count']} | "
                f"Topics: {', '.join(conv.get('topics', []) or [])}"
            )

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Customer history retrieval failed: {e}")
        return f"Error retrieving customer history: {str(e)[:200]}"


async def escalate_to_human(input: EscalationInput) -> str:
    """Escalate conversation to human support.

    Use this when:
    - Customer asks about pricing or refunds
    - Customer sentiment is negative
    - You cannot find relevant information
    - Customer explicitly requests human help

    Args:
        input: Escalation parameters with ticket ID and reason

    Returns:
        Escalation confirmation with reference ID
    """
    try:
        from production.database.queries import escalate_ticket

        # Determine routing
        routing_map = {
            'pricing_inquiry': 'sales_team',
            'refund_request': 'billing_team',
            'legal_threat': 'legal_team',
            'compliance_question': 'compliance_team',
            'angry_customer': 'senior_support',
            'human_requested': 'next_available_agent',
            'engineering_bug': 'engineering_team',
            'enterprise_inquiry': 'sales_team',
            'competitor_question': 'product_specialist',
            'cannot_answer': 'support_team',
        }
        route_to = routing_map.get(input.reason, 'support_team')

        await escalate_ticket(
            ticket_id=input.ticket_id,
            reason=input.reason,
            priority=input.urgency,
            route_to=route_to
        )

        escalation_id = f"ESC-{datetime.utcnow().strftime('%Y%m%d')}-{hash(input.ticket_id) % 10000:04d}"

        return (
            f"Escalation created successfully.\n"
            f"Escalation ID: {escalation_id}\n"
            f"Ticket ID: {input.ticket_id}\n"
            f"Reason: {input.reason}\n"
            f"Urgency: {input.urgency}\n"
            f"Routed to: {route_to}\n"
            f"Status: awaiting_human_agent"
        )

    except Exception as e:
        logger.error(f"Escalation failed: {e}")
        return f"Error creating escalation: {str(e)[:200]}"


async def send_response(input: ResponseInput) -> str:
    """Send response to customer via their preferred channel.

    The response will be automatically formatted for the channel.
    - Email: Formal with greeting/signature
    - WhatsApp: Concise and conversational
    - Web: Semi-formal

    Args:
        input: Response parameters with ticket ID, message, and channel

    Returns:
        Delivery status confirmation
    """
    try:
        from production.database.queries import (
            get_ticket,
            store_message,
            get_conversation_messages
        )
        from production.agent.formatters import format_for_channel

        # Get ticket and conversation info
        ticket = await get_ticket(input.ticket_id)
        if not ticket:
            return f"Error: Ticket {input.ticket_id} not found"

        # Format response for channel
        customer_name = ""
        if ticket.get('customer_id'):
            from production.database.queries import get_pool
            pool = await get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT name FROM customers WHERE id = $1",
                    ticket['customer_id']
                )
                if row:
                    customer_name = row['name'] or ""

        formatted = format_for_channel(
            input.message,
            input.channel.value,
            ticket_id=input.ticket_id,
            customer_name=customer_name
        )

        # Store response message
        await store_message(
            conversation_id=ticket['conversation_id'],
            channel=input.channel.value,
            direction='outbound',
            role='agent',
            content=input.message,
            metadata={'formatted_response': formatted}
        )

        # Update ticket status
        from production.database.queries import update_ticket_status
        await update_ticket_status(
            ticket_id=input.ticket_id,
            status='processing',
            resolution_notes='AI response sent'
        )

        return (
            f"Response sent successfully.\n"
            f"Ticket ID: {input.ticket_id}\n"
            f"Channel: {input.channel.value}\n"
            f"Delivery status: sent\n"
            f"Message length: {len(formatted)} characters"
        )

    except Exception as e:
        logger.error(f"Failed to send response: {e}")
        return f"Error sending response: {str(e)[:200]}"


# ─── Sentiment Analysis (Simple heuristic, replaceable with LLM) ───────────

async def analyze_sentiment(message: str) -> str:
    """Analyze the sentiment of a customer message.

    Returns a score from 0.0 (very negative) to 1.0 (very positive).
    Use this to gauge customer satisfaction and determine if escalation is needed.

    Args:
        message: The customer message text

    Returns:
        Sentiment score, label, and recommendation
    """
    try:
        score = _calculate_sentiment(message)

        if score >= 0.7:
            label = "positive"
            recommendation = "continue_normal_service"
        elif score >= 0.4:
            label = "neutral"
            recommendation = "continue_normal_service"
        elif score >= 0.3:
            label = "slightly_negative"
            recommendation = "show_extra_empathy"
        else:
            label = "negative"
            recommendation = "consider_escalation"

        return (
            f"Sentiment Analysis Result:\n"
            f"Score: {score:.2f} (0.0 = very negative, 1.0 = very positive)\n"
            f"Label: {label}\n"
            f"Recommendation: {recommendation}\n"
            f"Requires attention: {'Yes' if score < 0.4 else 'No'}"
        )

    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        return f"Error analyzing sentiment: {str(e)}"


def _calculate_sentiment(text: str) -> float:
    """Calculate sentiment score (0.0 to 1.0)."""
    text = text.lower()

    positive_words = {
        'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
        'love', 'thanks', 'thank', 'appreciate', 'helpful', 'awesome',
        'perfect', 'happy', 'pleased', 'best', 'cool', 'nice', 'superb'
    }
    negative_words = {
        'bad', 'terrible', 'awful', 'horrible', 'worst', 'hate',
        'angry', 'frustrated', 'frustrating', 'annoyed', 'disappointed',
        'useless', 'garbage', 'broken', 'not working', 'sucks',
        'ridiculous', 'unacceptable', 'scam', 'waste', 'pathetic'
    }

    words = set(text.split())
    positive_count = len(words & positive_words)
    negative_count = len(words & negative_words)

    total = positive_count + negative_count
    if total == 0:
        return 0.5

    raw_score = (positive_count - negative_count) / total
    return round((raw_score + 1) / 2, 2)


# ─── Escalation Evaluation ────────────────────────────────────────────────

async def evaluate_escalation(message: str, sentiment_score: float) -> str:
    """Evaluate whether a conversation should be escalated.

    Checks multiple escalation triggers and returns a recommendation.

    Args:
        message: Customer message text
        sentiment_score: Pre-calculated sentiment score (0-1)

    Returns:
        Escalation decision with reason and priority
    """
    text = message.lower()

    triggers = {
        'legal_threat': {
            'keywords': ['lawyer', 'attorney', 'sue', 'lawsuit', 'breach of contract'],
            'priority': 'P0'
        },
        'refund_request': {
            'keywords': ['refund', 'chargeback', 'dispute charge', 'cancel subscription'],
            'priority': 'P1'
        },
        'human_requested': {
            'keywords': ['human', 'agent', 'representative', 'real person', 'speak to someone'],
            'priority': 'P2'
        },
        'angry_customer': {
            'keywords': [],  # Based on sentiment only
            'priority': 'P1',
            'condition': sentiment_score < 0.3
        },
        'compliance_question': {
            'keywords': ['gdpr', 'hipaa', 'soc 2', 'compliance', 'data retention', 'baa'],
            'priority': 'P1'
        },
        'pricing_inquiry': {
            'keywords': ['discount', 'negotiate', 'custom pricing', 'bulk pricing',
                        'nonprofit discount', 'education pricing'],
            'priority': 'P2'
        },
        'competitor_question': {
            'keywords': ['asana', 'monday.com', 'notion', 'jira', 'trello', 'clickup'],
            'priority': 'P3'
        },
    }

    for reason, config in triggers.items():
        # Check keyword-based triggers
        if config.get('keywords'):
            if any(kw in text for kw in config['keywords']):
                return (
                    f"ESCALATION RECOMMENDED\n"
                    f"Reason: {reason}\n"
                    f"Priority: {config['priority']}\n"
                    f"Confidence: high"
                )

        # Check condition-based triggers
        if config.get('condition'):
            if config['condition']:
                return (
                    f"ESCALATION RECOMMENDED\n"
                    f"Reason: {reason}\n"
                    f"Priority: {config['priority']}\n"
                    f"Confidence: high"
                )

    return (
        f"NO ESCALATION NEEDED\n"
        f"Sentiment: {sentiment_score:.2f}\n"
        f"Confidence: high"
    )
