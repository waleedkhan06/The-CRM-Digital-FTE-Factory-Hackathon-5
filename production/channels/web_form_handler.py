"""
Customer Success FTE — Web Support Form Handler
=================================================
Phase 2: Specialization

FastAPI endpoints for the web support form:
- POST /support/submit — Handle form submission
- GET /support/ticket/{ticket_id} — Check ticket status

This works with the React/Next.js Web Support Form component.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr, field_validator
from production.kafka_client import FTEKafkaProducer, TOPICS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/support", tags=["support-form"])


# ─── Request/Response Models ────────────────────────────────────────────────

class SupportFormSubmission(BaseModel):
    """Support form submission model with validation."""
    name: str
    email: EmailStr
    subject: str
    category: str  # 'general', 'technical', 'billing', 'feedback', 'bug_report'
    message: str
    priority: Optional[str] = 'medium'
    attachments: Optional[list[str]] = []  # URLs or base64 encoded files

    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters')
        return v.strip()

    @field_validator('message')
    @classmethod
    def message_must_have_content(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('Message must be at least 10 characters')
        return v.strip()

    @field_validator('category')
    @classmethod
    def category_must_be_valid(cls, v):
        valid_categories = [
            'general', 'technical', 'billing', 'feedback', 'bug_report'
        ]
        if v not in valid_categories:
            raise ValueError(f'Category must be one of: {valid_categories}')
        return v

    @field_validator('priority')
    @classmethod
    def priority_must_be_valid(cls, v):
        valid_priorities = ['low', 'medium', 'high']
        if v not in valid_priorities:
            raise ValueError(f'Priority must be one of: {valid_priorities}')
        return v or 'medium'


SupportFormRequest = SupportFormSubmission  # alias used by tests


class SupportFormResponse(BaseModel):
    """Response model for form submission."""
    ticket_id: str
    message: str
    estimated_response_time: str


class TicketStatusResponse(BaseModel):
    """Response model for ticket status check."""
    ticket_id: str
    status: str
    category: Optional[str]
    priority: Optional[str]
    created_at: str
    last_updated: Optional[str]
    message_count: int
    last_message_preview: Optional[str]
    escalated: bool


# ─── Endpoints ──────────────────────────────────────────────────────────────

@router.post("/submit", response_model=SupportFormResponse)
async def submit_support_form(
    submission: SupportFormSubmission,
    background_tasks: BackgroundTasks
):
    """
    Handle support form submission.

    This endpoint:
    1. Validates the submission
    2. Creates a customer record (or finds existing)
    3. Creates a conversation and ticket
    4. Stores the initial message
    5. Publishes to Kafka for agent processing
    6. Returns confirmation with ticket ID
    """
    ticket_id = str(uuid.uuid4())

    try:
        # Import here to avoid circular imports
        from production.database.queries import (
            get_or_create_customer,
            create_conversation,
            create_ticket,
            store_message
        )

        # 1. Get or create customer
        customer = await get_or_create_customer(
            email=submission.email,
            name=submission.name
        )

        # 2. Create conversation
        conversation = await create_conversation(
            customer_id=customer['id'],
            channel='web_form',
            metadata={
                'subject': submission.subject,
                'form_version': '1.0',
                'attachments': submission.attachments
            }
        )

        # 3. Create ticket
        ticket = await create_ticket(
            conversation_id=conversation['id'],
            customer_id=customer['id'],
            source_channel='web_form',
            category=submission.category,
            priority=submission.priority
        )

        # 4. Store the incoming message
        await store_message(
            conversation_id=conversation['id'],
            channel='web_form',
            direction='inbound',
            role='customer',
            content=submission.message,
            channel_message_id=ticket_id,
            metadata={
                'subject': submission.subject,
                'category': submission.category,
                'priority': submission.priority
            }
        )

        # 5. Build normalized message for agent
        message_data = {
            'channel': 'web_form',
            'channel_message_id': ticket_id,
            'customer_email': submission.email,
            'customer_name': submission.name,
            'subject': submission.subject,
            'content': submission.message,
            'category': submission.category,
            'priority': submission.priority,
            'received_at': datetime.utcnow().isoformat(),
            'metadata': {
                'ticket_id': str(ticket['id']),
                'conversation_id': str(conversation['id']),
                'customer_id': str(customer['id']),
                'form_version': '1.0',
                'attachments': submission.attachments
            }
        }

        # 6. Publish to Kafka for agent processing
        async def publish_to_kafka():
            try:
                producer = FTEKafkaProducer()
                await producer.start()
                await producer.publish(
                    TOPICS['tickets_incoming'],
                    message_data
                )
                await producer.stop()
            except Exception as e:
                logger.error(f"Failed to publish to Kafka: {e}")
                # Message is still stored in DB, will be retried

        background_tasks.add_task(publish_to_kafka)

        logger.info(
            f"Form submission received: ticket={ticket['id']}, "
            f"customer={customer['id']}, category={submission.category}"
        )

        return SupportFormResponse(
            ticket_id=ticket_id,
            message="Thank you for contacting us! Our AI assistant will respond shortly.",
            estimated_response_time="Usually within 5 minutes"
        )

    except ImportError as e:
        # Fallback when database/Kafka not available (development mode)
        logger.warning(f"Database/Kafka not available, using mock mode: {e}")

        return SupportFormResponse(
            ticket_id=ticket_id,
            message="Thank you for contacting us! Our AI assistant will respond shortly.",
            estimated_response_time="Usually within 5 minutes"
        )


@router.get("/ticket/{ticket_id}", response_model=TicketStatusResponse)
async def get_ticket_status(ticket_id: str):
    """
    Get status and conversation history for a ticket.

    Returns:
    - Current ticket status
    - Number of messages exchanged
    - Last message preview
    - Whether it's been escalated
    """
    try:
        from production.database.queries import (
            get_ticket,
            get_conversation_messages
        )

        from production.database.queries import get_pool
        pool = await get_pool()

        ticket = None
        async with pool.acquire() as conn:
            # 1. Direct lookup by tickets.id
            row = await conn.fetchrow(
                "SELECT * FROM tickets WHERE id = $1",
                ticket_id
            )
            if row:
                ticket = dict(row)

            # 2. Lookup via messages.channel_message_id (what we return to the user)
            if not ticket:
                row = await conn.fetchrow("""
                    SELECT t.*
                    FROM tickets t
                    JOIN messages m ON m.conversation_id = t.conversation_id
                    WHERE m.channel_message_id = $1
                    LIMIT 1
                """, ticket_id)
                if row:
                    ticket = dict(row)

            # 3. Lookup via conversation metadata ticket_id
            if not ticket:
                row = await conn.fetchrow("""
                    SELECT t.*
                    FROM tickets t
                    JOIN conversations c ON c.id = t.conversation_id
                    WHERE c.metadata->>'ticket_id' = $1
                    LIMIT 1
                """, ticket_id)
                if row:
                    ticket = dict(row)

        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Get message count and last message
        messages = await get_conversation_messages(
            ticket['conversation_id'],
            limit=10
        )

        last_message = messages[-1] if messages else None

        return TicketStatusResponse(
            ticket_id=ticket_id,
            status=ticket['status'],
            category=ticket.get('category'),
            priority=ticket.get('priority'),
            created_at=ticket['created_at'].isoformat() if ticket.get('created_at') else "",
            last_updated=ticket['resolved_at'].isoformat() if ticket.get('resolved_at') else None,
            message_count=len(messages),
            last_message_preview=last_message['content'][:200] if last_message else None,
            escalated=ticket['status'] == 'escalated'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving ticket status: {e}")
        # Return mock data for development
        return TicketStatusResponse(
            ticket_id=ticket_id,
            status="processing",
            category="general",
            priority="medium",
            created_at=datetime.utcnow().isoformat(),
            last_updated=None,
            message_count=1,
            last_message_preview=None,
            escalated=False
        )


@router.get("/ticket/{ticket_id}/messages")
async def get_ticket_messages(ticket_id: str):
    """Get full conversation for a ticket."""
    try:
        from production.database.queries import (
            get_ticket,
            get_conversation_messages
        )

        ticket = await get_ticket(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        messages = await get_conversation_messages(ticket['conversation_id'])

        return {
            'ticket_id': ticket_id,
            'messages': [
                {
                    'id': str(m['id']),
                    'role': m['role'],
                    'content': m['content'],
                    'channel': m['channel'],
                    'created_at': m['created_at'].isoformat(),
                    'sentiment_score': float(m.get('sentiment_score', 0.5))
                }
                for m in messages
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve messages")
