"""
Customer Success FTE — Unified Message Processor Worker
=========================================================
Phase 2: Specialization

The worker that consumes messages from Kafka and processes them
through the AI agent. This is the core of the 24/7 autonomous operation.

Flow:
1. Consume message from Kafka (any channel)
2. Resolve/create customer
3. Get/create conversation
4. Store incoming message
5. Run agent with conversation history
6. Store agent response
7. Send response via appropriate channel
8. Publish metrics
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from production.config import kafka
from production.kafka_client import FTEKafkaConsumer, FTEKafkaProducer, TOPICS

logger = logging.getLogger(__name__)


class UnifiedMessageProcessor:
    """Process incoming messages from all channels through the FTE agent."""

    def __init__(self):
        from production.channels.gmail_handler import GmailHandler
        from production.channels.whatsapp_handler import WhatsAppHandler

        self.gmail = GmailHandler()
        self.whatsapp = WhatsAppHandler()
        self.producer = FTEKafkaProducer()
        self._running = False

    async def start(self):
        """Start the message processor."""
        await self.producer.start()

        consumer = FTEKafkaConsumer(
            topics=[TOPICS['tickets_incoming']],
            group_id=kafka.group_id,
        )
        await consumer.start()

        self._running = True
        logger.info("Message processor started, listening for tickets...")

        # Start consuming (this runs forever)
        await consumer.consume(self.process_message)

    async def stop(self):
        """Stop the message processor."""
        self._running = False
        await self.producer.stop()
        logger.info("Message processor stopped")

    async def process_message(self, topic: str, message: dict):
        """Process a single incoming message from any channel.
        
        This is the main processing pipeline:
        1. Extract channel and customer info
        2. Resolve/create customer
        3. Get/create conversation
        4. Store incoming message
        5. Load conversation history
        6. Run agent
        7. Store agent response
        8. Send response via channel
        9. Publish metrics
        """
        start_time = datetime.utcnow()

        try:
            # Extract channel
            channel = message.get('channel', 'web_form')

            # Step 1: Resolve/create customer
            customer_id = await self.resolve_customer(message)

            # Step 2: Get/create conversation
            conversation_id = await self.get_or_create_conversation(
                customer_id=customer_id,
                channel=channel,
                message=message
            )

            # Step 3: Store incoming message
            await self.store_message(
                conversation_id=conversation_id,
                channel=channel,
                direction='inbound',
                role='customer',
                content=message.get('content', ''),
                channel_message_id=message.get('channel_message_id')
            )

            # Step 4: Load conversation history
            history = await self.load_conversation_history(conversation_id)

            # Step 5: Run agent
            result = await self.run_agent(
                messages=history,
                context={
                    'customer_id': customer_id,
                    'conversation_id': conversation_id,
                    'channel': channel,
                    'ticket_subject': message.get('subject', 'Support Request'),
                    'customer_email': message.get('customer_email'),
                    'customer_phone': message.get('customer_phone'),
                    'customer_name': message.get('customer_name', ''),
                    'metadata': message.get('metadata', {}),
                }
            )

            # Calculate latency
            latency_ms = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )

            # Step 6: Store agent response
            await self.store_message(
                conversation_id=conversation_id,
                channel=channel,
                direction='outbound',
                role='agent',
                content=result.output,
                latency_ms=latency_ms,
                tool_calls=result.tool_calls if hasattr(result, 'tool_calls') else []
            )

            # Step 7: Update ticket status
            if hasattr(result, 'ticket_id') and result.ticket_id:
                await self.update_ticket(
                    ticket_id=result.ticket_id,
                    escalated=result.escalated if hasattr(result, 'escalated') else False,
                    escalation_reason=result.escalation_reason if hasattr(result, 'escalation_reason') else None,
                    escalation_priority=result.escalation_priority if hasattr(result, 'escalation_priority') else None,
                )

            # Step 8: Publish metrics
            await self.producer.publish(TOPICS['metrics'], {
                'event_type': 'message_processed',
                'channel': channel,
                'latency_ms': latency_ms,
                'escalated': result.escalated if hasattr(result, 'escalated') else False,
                'sentiment_score': result.sentiment_score if hasattr(result, 'sentiment_score') else 0.5,
                'tool_calls_count': len(result.tool_calls) if hasattr(result, 'tool_calls') else 0,
            })

            logger.info(
                f"Processed {channel} message in {latency_ms}ms | "
                f"escalated={result.escalated if hasattr(result, 'escalated') else False} | "
                f"sentiment={result.sentiment_score if hasattr(result, 'sentiment_score') else 0.5}"
            )

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            await self.handle_error(message, e)

    async def resolve_customer(self, message: dict) -> str:
        """Resolve or create customer from message identifiers."""
        from production.database.queries import get_or_create_customer

        email = message.get('customer_email')
        phone = message.get('customer_phone')
        name = message.get('customer_name', '')

        customer = await get_or_create_customer(
            email=email,
            phone=phone,
            name=name
        )

        return customer['id']

    async def get_or_create_conversation(
        self,
        customer_id: str,
        channel: str,
        message: dict
    ) -> str:
        """Get active conversation or create new one."""
        from production.database.queries import (
            get_active_conversation,
            create_conversation
        )

        # Check for active conversation (within last 24 hours)
        active = await get_active_conversation(customer_id, within_hours=24)

        if active:
            # Check if we should merge (different channel)
            if active['initial_channel'] != channel:
                # Add new channel to history
                from production.database.queries import get_pool
                pool = await get_pool()
                async with pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE conversations
                        SET channel_history = array_append(channel_history, $1)
                        WHERE id = $2 AND NOT ($1 = ANY(channel_history))
                    """, channel, active['id'])
            return active['id']

        # Create new conversation
        conversation = await create_conversation(
            customer_id=customer_id,
            channel=channel,
            metadata={
                'subject': message.get('subject', 'Support Request'),
                'category': message.get('category', 'general'),
            }
        )

        return conversation['id']

    async def store_message(
        self,
        conversation_id: str,
        channel: str,
        direction: str,
        role: str,
        content: str,
        channel_message_id: str = None,
        latency_ms: int = None,
        tool_calls: list = None,
    ):
        """Store a message in the database."""
        from production.database.queries import store_message as db_store

        await db_store(
            conversation_id=conversation_id,
            channel=channel,
            direction=direction,
            role=role,
            content=content,
            channel_message_id=channel_message_id,
            latency_ms=latency_ms,
            tool_calls=tool_calls or [],
        )

    async def load_conversation_history(self, conversation_id: str) -> list:
        """Load conversation history for agent context."""
        from production.database.queries import get_conversation_messages

        messages = await get_conversation_messages(conversation_id, limit=20)

        # Convert to OpenAI message format
        history = []
        for msg in messages:
            history.append({
                'role': 'user' if msg['role'] == 'customer' else 'assistant',
                'content': msg['content']
            })

        return history

    async def run_agent(self, messages: list, context: dict):
        """Run the AI agent with conversation history."""
        from production.agent.customer_success_agent import process_customer_message

        # Get the last user message
        last_message = ""
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                last_message = msg.get('content', '')
                break

        result = await process_customer_message(
            message=last_message,
            channel=context.get('channel', 'web_form'),
            customer_id=context.get('customer_id'),
            customer_email=context.get('customer_email'),
            customer_name=context.get('customer_name', ''),
            ticket_subject=context.get('ticket_subject', ''),
            conversation_history=messages[:-1] if len(messages) > 1 else None,
        )

        return result

    async def update_ticket(
        self,
        ticket_id: str,
        escalated: bool = False,
        escalation_reason: str = None,
        escalation_priority: str = None,
    ):
        """Update ticket status based on agent result."""
        from production.database.queries import update_ticket_status, escalate_ticket

        if escalated and escalation_reason:
            route_map = {
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
            route_to = route_map.get(escalation_reason, 'support_team')

            await escalate_ticket(
                ticket_id=ticket_id,
                reason=escalation_reason,
                priority=escalation_priority or 'P2',
                route_to=route_to,
            )
        else:
            await update_ticket_status(
                ticket_id=ticket_id,
                status='processing',
                resolution_notes='AI response sent'
            )

    async def handle_error(self, message: dict, error: Exception):
        """Handle processing errors gracefully."""
        channel = message.get('channel', 'web_form')
        apology = (
            "I'm sorry, I'm having trouble processing your request right now. "
            "A human agent will follow up shortly."
        )

        try:
            # Send apologetic response via appropriate channel
            if channel == 'email' and message.get('customer_email'):
                await self.gmail.send_reply(
                    to_email=message['customer_email'],
                    subject=message.get('subject', 'Support Request'),
                    body=apology
                )
            elif channel == 'whatsapp' and message.get('customer_phone'):
                await self.whatsapp.send_message(
                    to_phone=message['customer_phone'],
                    body=apology
                )

        except Exception as e:
            logger.error(f"Failed to send error response: {e}")

        # Publish to DLQ for human review
        await self.producer.publish(TOPICS['dlq'], {
            'event_type': 'processing_error',
            'original_message': message,
            'error': str(error),
            'requires_human': True,
        })

        # Also publish to escalations
        await self.producer.publish(TOPICS['escalations'], {
            'event_type': 'processing_error',
            'error': str(error),
            'channel': channel,
            'requires_human': True,
        })


# ─── Metrics Collector Worker ──────────────────────────────────────────────

class MetricsCollector:
    """Background worker that collects and records metrics."""

    def __init__(self):
        self._running = False

    async def start(self):
        """Start the metrics collector."""
        self._running = True
        logger.info("Metrics collector started")

        while self._running:
            try:
                await self.collect_metrics()
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")

            await asyncio.sleep(60)  # Collect every minute

    async def stop(self):
        """Stop the metrics collector."""
        self._running = False
        logger.info("Metrics collector stopped")

    async def collect_metrics(self):
        """Collect and record system metrics."""
        from production.database.queries import record_metric

        # Record queue depth
        # Record processing latency
        # Record error rates
        # Record sentiment distribution
        pass  # Implementation depends on monitoring infrastructure


# ─── Main Entry Point ──────────────────────────────────────────────────────

async def main():
    """Start all workers."""
    processor = UnifiedMessageProcessor()
    metrics = MetricsCollector()

    # Run both concurrently
    await asyncio.gather(
        processor.start(),
        metrics.start(),
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
