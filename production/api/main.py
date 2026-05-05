"""
Customer Success FTE — FastAPI Service
========================================
Phase 2: Specialization

Main API layer with endpoints for all channels:
- Health check
- Gmail webhook
- WhatsApp/Twilio webhook
- Web support form (included from web_form_handler)
- Conversation history
- Customer lookup
- Channel metrics

This is the entry point for all external traffic.
"""

import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from production.channels.web_form_handler import router as web_form_router
from production.config import validate_config, gmail, whatsapp, webform

logger = logging.getLogger(__name__)

# ─── Application Factory ───────────────────────────────────────────────────

app = FastAPI(
    title="Customer Success FTE API",
    description="24/7 AI-powered customer support across Email, WhatsApp, and Web",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── Middleware ─────────────────────────────────────────────────────────────

# CORS for web form
# allow_credentials=True is incompatible with allow_origins=["*"].
# In development we expand the origins list to cover all common frontend ports.
_cors_origins = webform.allowed_origins
if "*" in _cors_origins or os.getenv("ENVIRONMENT", "development") == "development":
    _cors_origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:4000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Include Routers ───────────────────────────────────────────────────────

app.include_router(web_form_router)

# ─── Initialize Channel Handlers ───────────────────────────────────────────

from production.channels.gmail_handler import GmailHandler
from production.channels.whatsapp_handler import WhatsAppHandler
from production.kafka_client import FTEKafkaProducer, TOPICS

gmail_handler = GmailHandler()
whatsapp_handler = WhatsAppHandler()
kafka_producer = FTEKafkaProducer()

# ─── Lifecycle Events ──────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    # Validate configuration
    errors = validate_config()
    if errors:
        logger.warning(f"Configuration warnings: {', '.join(errors)}")

    # Start Kafka producer
    try:
        await kafka_producer.start()
        logger.info("Kafka producer started")
    except Exception as e:
        logger.warning(f"Kafka producer not available (mock mode): {e}")

    # Initialize channel handlers
    if gmail.enabled:
        logger.info("Gmail handler initialized")
    if whatsapp.enabled:
        logger.info("WhatsApp handler initialized")

    logger.info("Customer Success FTE API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up services on shutdown."""
    try:
        await kafka_producer.stop()
        logger.info("Kafka producer stopped")
    except Exception:
        pass

    from production.database.queries import close_pool
    await close_pool()
    logger.info("Customer Success FTE API shut down")


# ─── Health Check ──────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes probes."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "channels": {
            "email": "active" if gmail.enabled else "disabled",
            "whatsapp": "active" if whatsapp.enabled else "disabled",
            "web_form": "active" if webform.enabled else "disabled"
        }
    }


@app.get("/health/ready")
async def readiness_check():
    """Readiness check — verifies all dependencies are available."""
    checks = {
        "database": True,
        "kafka": kafka_producer._running,
        "gmail": gmail_handler._initialized if hasattr(gmail_handler, '_initialized') else False,
        "whatsapp": whatsapp_handler._initialized if hasattr(whatsapp_handler, '_initialized') else False,
    }

    # Check database connectivity
    try:
        from production.database.queries import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        checks["database"] = True
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        checks["database"] = False

    all_healthy = all(checks.values())

    return {
        "status": "ready" if all_healthy else "degraded",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }


# ─── Gmail Webhook Endpoint ────────────────────────────────────────────────

@app.post("/webhooks/gmail")
async def gmail_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handle Gmail push notifications via Pub/Sub.

    Receives notifications from Google Cloud Pub/Sub when new emails arrive.
    Fetches the actual email content and publishes to Kafka for processing.
    """
    try:
        body = await request.json()
        messages = await gmail_handler.process_notification(body)

        for message in messages:
            # Publish to unified ticket queue
            background_tasks.add_task(
                kafka_producer.publish,
                TOPICS['tickets_incoming'],
                message
            )
            # Also publish to email-specific topic
            background_tasks.add_task(
                kafka_producer.publish,
                TOPICS['email_inbound'],
                message
            )

        logger.info(f"Processed {len(messages)} emails from Gmail webhook")
        return {"status": "processed", "count": len(messages)}

    except Exception as e:
        logger.error(f"Gmail webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── WhatsApp/Twilio Webhook Endpoint ──────────────────────────────────────

@app.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handle incoming WhatsApp messages via Twilio webhook.

    Validates Twilio signature, processes the message,
    and publishes to Kafka for agent processing.
    """
    try:
        # Validate Twilio signature
        is_valid = await whatsapp_handler.validate_webhook(request)
        if not is_valid:
            logger.warning("Invalid Twilio webhook signature")
            raise HTTPException(status_code=403, detail="Invalid signature")

        # Parse form data
        form_data = await request.form()
        message = await whatsapp_handler.process_webhook(dict(form_data))

        # Publish to unified ticket queue
        background_tasks.add_task(
            kafka_producer.publish,
            TOPICS['tickets_incoming'],
            message
        )
        # Also publish to WhatsApp-specific topic
        background_tasks.add_task(
            kafka_producer.publish,
            TOPICS['whatsapp_inbound'],
            message
        )

        # Return empty TwiML response (agent will respond asynchronously)
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
            media_type="application/xml"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        # Don't return error to Twilio — it will retry
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
            media_type="application/xml"
        )


@app.post("/webhooks/whatsapp/status")
async def whatsapp_status_webhook(request: Request):
    """
    Handle WhatsApp message status updates (delivered, read, failed).

    Updates the delivery status in the database.
    """
    try:
        form_data = await request.form()
        message_sid = form_data.get('MessageSid')
        status = form_data.get('MessageStatus')

        if message_sid and status:
            await whatsapp_handler.update_delivery_status(message_sid, status)

        return {"status": "received"}

    except Exception as e:
        logger.error(f"WhatsApp status webhook error: {e}")
        return {"status": "error", "detail": str(e)}


# ─── Conversation History Endpoint ─────────────────────────────────────────

@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Get full conversation history with cross-channel context.

    Returns all messages in the conversation with metadata.
    """
    try:
        from production.database.queries import get_conversation_messages, get_pool

        pool = await get_pool()
        async with pool.acquire() as conn:
            conv = await conn.fetchrow(
                "SELECT * FROM conversations WHERE id = $1", conversation_id
            )
            if not conv:
                raise HTTPException(status_code=404, detail="Conversation not found")

            messages = await get_conversation_messages(conversation_id, limit=100)

        return {
            'conversation': dict(conv),
            'messages': [
                {
                    'id': str(m['id']),
                    'role': m['role'],
                    'content': m['content'],
                    'channel': m['channel'],
                    'direction': m['direction'],
                    'created_at': m['created_at'].isoformat(),
                    'sentiment_score': float(m.get('sentiment_score', 0.5)),
                    'delivery_status': m.get('delivery_status'),
                }
                for m in messages
            ],
            'message_count': len(messages)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation")


# ─── Customer Lookup Endpoint ──────────────────────────────────────────────

@app.get("/customers/lookup")
async def lookup_customer(email: Optional[str] = None,
                           phone: Optional[str] = None):
    """
    Look up customer by email or phone across all channels.

    Returns customer profile with interaction history.
    """
    if not email and not phone:
        raise HTTPException(
            status_code=400,
            detail="Provide at least email or phone parameter"
        )

    try:
        from production.database.queries import (
            get_or_create_customer,
            get_customer_history
        )

        customer = await get_or_create_customer(email=email, phone=phone)
        history = await get_customer_history(customer['id'], limit=10)

        return {
            'customer': customer,
            'history': history
        }

    except Exception as e:
        logger.error(f"Customer lookup error: {e}")
        raise HTTPException(status_code=500, detail="Failed to lookup customer")


# ─── Channel Metrics Endpoint ──────────────────────────────────────────────

@app.get("/metrics/channels")
async def get_channel_metrics():
    """
    Get performance metrics by channel.

    Returns conversation counts, sentiment, and escalation rates
    broken down by channel for the last 24 hours.
    """
    try:
        from production.database.queries import get_channel_metrics as db_metrics

        metrics = await db_metrics(hours=24)

        # Add ticket metrics
        from production.database.queries import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            ticket_metrics = await conn.fetch("""
                SELECT 
                    source_channel as channel,
                    COUNT(*) as total_tickets,
                    COUNT(*) FILTER (WHERE status = 'escalated') as escalated,
                    COUNT(*) FILTER (WHERE status = 'resolved') as resolved,
                    COUNT(*) FILTER (WHERE status = 'open') as open_tickets
                FROM tickets
                WHERE created_at > NOW() - INTERVAL '24 hours'
                GROUP BY source_channel
            """)

            for row in ticket_metrics:
                channel = row['channel']
                if channel in metrics:
                    metrics[channel].update(dict(row))
                else:
                    metrics[channel] = dict(row)

        return metrics

    except Exception as e:
        logger.error(f"Metrics retrieval error: {e}")
        # Return empty metrics rather than error
        return {}


# ─── Gmail Poll Endpoint (Local Testing) ──────────────────────────────────

@app.post("/gmail/poll")
async def poll_gmail(background_tasks: BackgroundTasks, max_results: int = 10):
    """
    Poll Gmail inbox for unread emails and process them through the agent.

    Useful for local testing without Pub/Sub setup.
    Fetches unread messages, marks them as read, and runs each through the agent.
    """
    try:
        messages = await gmail_handler.fetch_unread(max_results=max_results)

        if not messages:
            return {"status": "ok", "processed": 0, "message": "No unread emails found"}

        results = []
        for msg in messages:
            background_tasks.add_task(
                kafka_producer.publish,
                TOPICS['tickets_incoming'],
                msg
            )
            results.append({
                "from": msg.get("customer_email"),
                "subject": msg.get("subject"),
                "message_id": msg.get("channel_message_id"),
            })

        logger.info(f"Gmail poll: queued {len(results)} emails for processing")
        return {"status": "ok", "processed": len(results), "emails": results}

    except Exception as e:
        logger.error(f"Gmail poll error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── Agent Processing Endpoint (Manual Trigger) ───────────────────────────

@app.post("/agent/process")
async def trigger_agent_processing(message: dict):
    """
    Manually trigger agent processing for a message.

    Useful for testing and debugging.
    """
    try:
        from production.agent.customer_success_agent import process_customer_message

        result = await process_customer_message(
            message=message.get('content', ''),
            channel=message.get('channel', 'web_form'),
            customer_id=message.get('customer_email') or message.get('customer_phone'),
            customer_email=message.get('customer_email'),
            customer_name=message.get('customer_name', ''),
            ticket_subject=message.get('subject', ''),
        )

        return {
            'status': 'processed',
            'response': result.output,
            'escalated': result.escalated,
            'escalation_reason': result.escalation_reason,
            'sentiment': result.sentiment_score,
            'topics': result.topics,
            'ticket_id': result.ticket_id,
        }

    except Exception as e:
        logger.error(f"Agent processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
