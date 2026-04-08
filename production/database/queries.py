"""
Customer Success FTE — Database Queries
========================================
Phase 2: Specialization

Database access functions for the production CRM system.
All functions use asyncpg for async PostgreSQL access.
"""

import asyncpg
import os
from typing import Optional
from datetime import datetime
import json


# ─── Connection Pool ────────────────────────────────────────────────────────

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """Get or create the database connection pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "fte_db"),
            user=os.getenv("POSTGRES_USER", "fte_user"),
            password=os.getenv("POSTGRES_PASSWORD", "fte_password"),
            min_size=2,
            max_size=20,
            command_timeout=30,
        )
    return _pool


async def close_pool():
    """Close the database connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


# ─── Customer Queries ───────────────────────────────────────────────────────

async def find_customer_by_email(email: str) -> Optional[dict]:
    """Find a customer by email address."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM customers WHERE email = $1", email
        )
        return dict(row) if row else None


async def find_customer_by_phone(phone: str) -> Optional[dict]:
    """Find a customer by phone number."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM customers WHERE phone = $1", phone
        )
        return dict(row) if row else None


async def find_customer_by_identifier(identifier_type: str,
                                       identifier_value: str) -> Optional[dict]:
    """Find a customer by any identifier type (email, phone, whatsapp)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT c.* FROM customers c
            JOIN customer_identifiers ci ON ci.customer_id = c.id
            WHERE ci.identifier_type = $1 AND ci.identifier_value = $2
        """, identifier_type, identifier_value)
        return dict(row) if row else None


async def create_customer(email: str = None, phone: str = None,
                          name: str = "", metadata: dict = None) -> dict:
    """Create a new customer record."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO customers (email, phone, name, metadata)
            VALUES ($1, $2, $3, $4)
            RETURNING id, email, phone, name, created_at, avg_sentiment,
                      total_interactions, preferred_channel
        """, email, phone, name, json.dumps(metadata or {}))
        return dict(row)


async def get_or_create_customer(email: str = None, phone: str = None,
                                  name: str = "") -> dict:
    """Find existing customer or create a new one."""
    # Try email first
    if email:
        customer = await find_customer_by_email(email)
        if customer:
            if name and not customer.get('name'):
                await update_customer_name(customer['id'], name)
            return customer

    # Try phone
    if phone:
        customer = await find_customer_by_phone(phone)
        if customer:
            return customer

    # Create new
    return await create_customer(email=email, phone=phone, name=name)


async def update_customer_name(customer_id: str, name: str):
    """Update customer name."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE customers SET name = $1, updated_at = NOW() WHERE id = $2",
            name, customer_id
        )


async def get_customer_history(customer_id: str,
                                limit: int = 20) -> dict:
    """Get customer's complete interaction history."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Get customer info
        customer = await conn.fetchrow(
            "SELECT * FROM customers WHERE id = $1", customer_id
        )
        if not customer:
            return {"error": "Customer not found"}

        # Get conversations
        conversations = await conn.fetch("""
            SELECT c.id, c.initial_channel, c.status, c.started_at,
                   c.sentiment_score, c.topics, c.channel_history,
                   COUNT(m.id) as message_count
            FROM conversations c
            LEFT JOIN messages m ON m.conversation_id = c.id
            WHERE c.customer_id = $1
            GROUP BY c.id
            ORDER BY c.started_at DESC
            LIMIT $2
        """, customer_id, limit)

        return {
            'customer': dict(customer),
            'total_conversations': len(conversations),
            'conversations': [dict(c) for c in conversations]
        }


# ─── Conversation Queries ───────────────────────────────────────────────────

async def create_conversation(customer_id: str, channel: str,
                               metadata: dict = None) -> dict:
    """Create a new conversation."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO conversations (customer_id, initial_channel, metadata)
            VALUES ($1, $2, $3)
            RETURNING id, customer_id, initial_channel, started_at, status
        """, customer_id, channel, json.dumps(metadata or {}))
        return dict(row)


async def get_active_conversation(customer_id: str,
                                   within_hours: int = 24) -> Optional[dict]:
    """Find an active conversation for a customer within the time window."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT * FROM conversations
            WHERE customer_id = $1
              AND status = 'active'
              AND started_at > NOW() - INTERVAL '%s hours'
            ORDER BY started_at DESC
            LIMIT 1
        """ % within_hours, customer_id)
        return dict(row) if row else None


async def update_conversation_sentiment(conversation_id: str,
                                         sentiment: float):
    """Update conversation sentiment score."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE conversations 
            SET sentiment_score = $1, updated_at = NOW()
            WHERE id = $2
        """, sentiment, conversation_id)


async def resolve_conversation(conversation_id: str,
                                resolution_type: str,
                                notes: str = ""):
    """Mark a conversation as resolved."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE conversations
            SET status = 'resolved',
                resolution_type = $1,
                ended_at = NOW(),
                metadata = jsonb_set(metadata, '{resolution_notes}', to_jsonb($2::text))
            WHERE id = $3
        """, resolution_type, notes, conversation_id)


async def escalate_conversation(conversation_id: str,
                                 escalated_to: str,
                                 reason: str = ""):
    """Escalate a conversation to a human agent."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE conversations
            SET status = 'escalated',
                escalated_to = $1,
                metadata = jsonb_set(
                    jsonb_set(metadata, '{escalation_reason}', to_jsonb($2::text)),
                    '{escalated_at}', to_jsonb(NOW()::text)
                )
            WHERE id = $3
        """, escalated_to, reason, conversation_id)


# ─── Message Queries ────────────────────────────────────────────────────────

async def store_message(conversation_id: str, channel: str,
                        direction: str, role: str, content: str,
                        sentiment_score: float = 0.5,
                        channel_message_id: str = None,
                        latency_ms: int = None,
                        tool_calls: list = None,
                        metadata: dict = None) -> dict:
    """Store a message in the database."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO messages (
                conversation_id, channel, direction, role, content,
                sentiment_score, channel_message_id, latency_ms,
                tool_calls, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id, conversation_id, channel, direction, role,
                      content, created_at, sentiment_score
        """, conversation_id, channel, direction, role, content,
            sentiment_score, channel_message_id, latency_ms,
            json.dumps(tool_calls or []), json.dumps(metadata or {}))
        return dict(row)


async def get_conversation_messages(conversation_id: str,
                                     limit: int = 20) -> list:
    """Get messages for a conversation."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM messages
            WHERE conversation_id = $1
            ORDER BY created_at ASC
            LIMIT $2
        """, conversation_id, limit)
        return [dict(r) for r in rows]


# ─── Ticket Queries ─────────────────────────────────────────────────────────

async def create_ticket(conversation_id: str, customer_id: str,
                        source_channel: str, category: str = "general",
                        priority: str = "medium") -> dict:
    """Create a support ticket."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO tickets (
                conversation_id, customer_id, source_channel,
                category, priority, status
            ) VALUES ($1, $2, $3, $4, $5, 'open')
            RETURNING id, conversation_id, customer_id, source_channel,
                      category, priority, status, created_at
        """, conversation_id, customer_id, source_channel,
            category, priority)
        return dict(row)


async def get_ticket(ticket_id: str) -> Optional[dict]:
    """Get a ticket by ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM tickets WHERE id = $1", ticket_id
        )
        return dict(row) if row else None


async def update_ticket_status(ticket_id: str, status: str,
                                resolution_notes: str = ""):
    """Update ticket status."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE tickets
            SET status = $1,
                resolution_notes = $2,
                resolved_at = CASE WHEN $1 = 'resolved' THEN NOW() ELSE resolved_at END
            WHERE id = $3
        """, status, resolution_notes, ticket_id)


async def escalate_ticket(ticket_id: str, reason: str,
                          priority: str = "P2",
                          route_to: str = "support_team"):
    """Escalate a ticket to human agents."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE tickets
            SET status = 'escalated',
                escalation_reason = $1,
                escalation_priority = $2,
                escalated_to = $3,
                escalated_at = NOW()
            WHERE id = $4
        """, reason, priority, route_to, ticket_id)

        # Also create escalation record
        ticket = await get_ticket(ticket_id)
        if ticket:
            await conn.execute("""
                INSERT INTO escalations (
                    ticket_id, conversation_id, reason, priority, route_to,
                    context_summary
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """, ticket_id, ticket['conversation_id'], reason, priority,
                route_to, f"Escalated: {reason}")


# ─── Knowledge Base Queries ─────────────────────────────────────────────────

async def search_knowledge_base(query: str, max_results: int = 5,
                                 category: str = None) -> list:
    """Search the knowledge base using keyword matching.
    
    Production version will use pgvector for semantic search.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Keyword-based search (prototype)
        keywords = query.lower().split()

        if category:
            rows = await conn.fetch("""
                SELECT id, title, content, category,
                       keywords,
                       (SELECT COUNT(*) 
                        FROM unnest(keywords) k 
                        WHERE k = ANY($1::text[])) as match_count
                FROM knowledge_base
                WHERE category = $2
                  AND keywords && $1::text[]
                ORDER BY match_count DESC
                LIMIT $3
            """, keywords, category, max_results)
        else:
            rows = await conn.fetch("""
                SELECT id, title, content, category,
                       keywords,
                       (SELECT COUNT(*) 
                        FROM unnest(keywords) k 
                        WHERE k = ANY($1::text[])) as match_count
                FROM knowledge_base
                WHERE keywords && $1::text[]
                ORDER BY match_count DESC
                LIMIT $2
            """, keywords, max_results)

        results = []
        for row in rows:
            results.append({
                'id': str(row['id']),
                'title': row['title'],
                'content': row['content'],
                'category': row['category'],
                'score': row['match_count'] / max(len(keywords), 1)
            })

        return results


# ─── Metrics Queries ────────────────────────────────────────────────────────

async def record_metric(metric_name: str, metric_value: float,
                        channel: str = None, dimensions: dict = None):
    """Record a performance metric."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO agent_metrics (metric_name, metric_value, channel, dimensions)
            VALUES ($1, $2, $3, $4)
        """, metric_name, metric_value, channel, json.dumps(dimensions or {}))


async def get_channel_metrics(hours: int = 24) -> dict:
    """Get performance metrics by channel."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT 
                initial_channel as channel,
                COUNT(*) as total_conversations,
                ROUND(AVG(sentiment_score)::numeric, 2) as avg_sentiment,
                COUNT(*) FILTER (WHERE status = 'escalated') as escalations,
                COUNT(*) FILTER (WHERE status = 'resolved') as resolved
            FROM conversations
            WHERE started_at > NOW() - INTERVAL '%s hours'
            GROUP BY initial_channel
        """ % hours)

        return {row['channel']: dict(row) for row in rows}


# ─── Database Initialization ────────────────────────────────────────────────

async def init_database():
    """Initialize the database by running the schema."""
    pool = await get_pool()
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')

    with open(schema_path, 'r') as f:
        schema = f.read()

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(schema)

    print("Database initialized successfully.")
