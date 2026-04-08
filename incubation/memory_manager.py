"""
Customer Success FTE — Memory & State Manager
==============================================
Phase 1: Incubation

Manages conversation state, customer identification, sentiment tracking,
and cross-channel conversation continuity.

Production version will use PostgreSQL for persistent storage.
"""

import json
import os
from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid


# ─── Enums ───────────────────────────────────────────────────────────────────

class ConversationStatus(str, Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    PENDING = "pending"
    ESCALATED = "escalated"


class ResolutionType(str, Enum):
    AI_RESOLVED = "ai_resolved"
    ESCALATED_TO_HUMAN = "escalated_to_human"
    CUSTOMER_ABANDONED = "customer_abandoned"
    MERGED = "merged"


# ─── Data Classes ────────────────────────────────────────────────────────────

@dataclass
class Customer:
    """Unified customer record across all channels."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    email: Optional[str] = None
    phone: Optional[str] = None
    name: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    total_interactions: int = 0
    avg_sentiment: float = 0.5
    preferred_channel: str = "email"
    metadata: dict = field(default_factory=dict)

    def update_sentiment(self, new_score: float):
        """Update running average sentiment."""
        self.total_interactions += 1
        # Running average
        self.avg_sentiment = (
            (self.avg_sentiment * (self.total_interactions - 1) + new_score)
            / self.total_interactions
        )


@dataclass
class Message:
    """Individual message in a conversation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str = ""
    channel: str = ""
    direction: str = "inbound"  # inbound or outbound
    role: str = "customer"  # customer, agent, system
    content: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    sentiment_score: float = 0.5
    topics: list = field(default_factory=list)
    tool_calls: list = field(default_factory=list)
    channel_message_id: Optional[str] = None  # External ID (Gmail ID, Twilio SID)
    metadata: dict = field(default_factory=dict)


@dataclass
class Conversation:
    """A conversation thread, potentially spanning multiple channels."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    initial_channel: str = ""
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    ended_at: Optional[str] = None
    status: str = ConversationStatus.ACTIVE
    sentiment_score: float = 0.5
    resolution_type: Optional[str] = None
    escalated_to: Optional[str] = None
    channel_history: list = field(default_factory=list)  # Track all channels used
    messages: list = field(default_factory=list)
    topics: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def add_message(self, message: Message):
        """Add a message to the conversation."""
        self.messages.append(message)
        if message.channel not in self.channel_history:
            self.channel_history.append(message.channel)
        # Update conversation sentiment (running average of recent messages)
        recent_sentiments = [
            m.sentiment_score for m in self.messages[-5:]
            if m.sentiment_score > 0
        ]
        if recent_sentiments:
            self.sentiment_score = sum(recent_sentiments) / len(recent_sentiments)

    def get_context_summary(self, max_messages: int = 10) -> str:
        """Get a summary of recent conversation context."""
        recent = self.messages[-max_messages:]
        lines = []
        for msg in recent:
            sender = "Customer" if msg.role == "customer" else "Agent"
            lines.append(f"[{msg.channel}] {sender}: {msg.content[:200]}")
        return "\n".join(lines)


# ─── Memory Manager ─────────────────────────────────────────────────────────

class MemoryManager:
    """Manages all state for the customer success agent.
    
    In-memory storage for the prototype. Production version uses PostgreSQL.
    """

    def __init__(self):
        self.customers: dict[str, Customer] = {}
        self.conversations: dict[str, Conversation] = {}
        self.messages: dict[str, Message] = {}
        # Indexes
        self.email_to_customer: dict[str, str] = {}
        self.phone_to_customer: dict[str, str] = {}
        self.customer_conversations: dict[str, list[str]] = {}  # customer_id -> [conversation_ids]

    # ─── Customer Management ─────────────────────────────────────────────

    def get_or_create_customer(self, email: str = None, phone: str = None,
                                name: str = "") -> Customer:
        """Find existing customer or create a new one."""
        customer = None

        # Try to find by email
        if email and email in self.email_to_customer:
            customer = self.customers[self.email_to_customer[email]]

        # Try to find by phone
        if not customer and phone and phone in self.phone_to_customer:
            customer = self.customers[self.phone_to_customer[phone]]

        # Create new customer
        if not customer:
            customer = Customer(email=email, phone=phone, name=name)
            self.customers[customer.id] = customer
            self.customer_conversations[customer.id] = []

            # Index identifiers
            if email:
                self.email_to_customer[email] = customer.id
            if phone:
                self.phone_to_customer[phone] = customer.id

        # Update identifiers if new ones provided
        if email and email not in self.email_to_customer:
            self.email_to_customer[email] = customer.id
            customer.email = email

        if phone and phone not in self.phone_to_customer:
            self.phone_to_customer[phone] = customer.id
            customer.phone = phone

        if name and not customer.name:
            customer.name = name

        return customer

    def get_customer_by_email(self, email: str) -> Optional[Customer]:
        """Look up customer by email."""
        if email in self.email_to_customer:
            return self.customers[self.email_to_customer[email]]
        return None

    def get_customer_by_phone(self, phone: str) -> Optional[Customer]:
        """Look up customer by phone."""
        if phone in self.phone_to_customer:
            return self.customers[self.phone_to_customer[phone]]
        return None

    def get_customer_history(self, customer_id: str) -> dict:
        """Get complete customer interaction history."""
        customer = self.customers.get(customer_id)
        if not customer:
            return {"error": "Customer not found"}

        conversation_ids = self.customer_conversations.get(customer_id, [])
        conversations = []
        for cid in conversation_ids:
            conv = self.conversations.get(cid)
            if conv:
                conversations.append({
                    'id': conv.id,
                    'initial_channel': conv.initial_channel,
                    'status': conv.status,
                    'started_at': conv.started_at,
                    'sentiment_score': conv.sentiment_score,
                    'message_count': len(conv.messages),
                    'topics': conv.topics,
                    'channels_used': conv.channel_history
                })

        return {
            'customer': asdict(customer),
            'total_conversations': len(conversations),
            'conversations': conversations
        }

    # ─── Conversation Management ─────────────────────────────────────────

    def create_conversation(self, customer_id: str, channel: str,
                            subject: str = "") -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(
            customer_id=customer_id,
            initial_channel=channel,
            metadata={'subject': subject}
        )
        self.conversations[conversation.id] = conversation
        self.customer_conversations.setdefault(customer_id, []).append(conversation.id)
        return conversation

    def get_active_conversation(self, customer_id: str,
                                 within_hours: int = 24) -> Optional[Conversation]:
        """Find an active conversation for a customer within the time window."""
        conversation_ids = self.customer_conversations.get(customer_id, [])

        for cid in conversation_ids:
            conv = self.conversations.get(cid)
            if conv and conv.status == ConversationStatus.ACTIVE:
                # Check if within time window
                started = datetime.fromisoformat(conv.started_at)
                if datetime.utcnow() - started < timedelta(hours=within_hours):
                    return conv

        return None

    def add_message_to_conversation(self, conversation_id: str,
                                     message: Message) -> None:
        """Add a message to an existing conversation."""
        conversation = self.conversations.get(conversation_id)
        if conversation:
            conversation.add_message(message)
            self.messages[message.id] = message

    def resolve_conversation(self, conversation_id: str,
                              resolution_type: str,
                              notes: str = "") -> None:
        """Mark a conversation as resolved or escalated."""
        conversation = self.conversations.get(conversation_id)
        if conversation:
            conversation.status = ConversationStatus.RESOLVED
            conversation.resolution_type = resolution_type
            conversation.ended_at = datetime.utcnow().isoformat()
            conversation.metadata['resolution_notes'] = notes

    def escalate_conversation(self, conversation_id: str,
                               escalated_to: str,
                               reason: str = "") -> None:
        """Escalate a conversation to a human agent."""
        conversation = self.conversations.get(conversation_id)
        if conversation:
            conversation.status = ConversationStatus.ESCALATED
            conversation.escalated_to = escalated_to
            conversation.metadata['escalation_reason'] = reason
            conversation.metadata['escalated_at'] = datetime.utcnow().isoformat()

    # ─── Sentiment Tracking ──────────────────────────────────────────────

    def get_sentiment_trend(self, customer_id: str) -> list:
        """Get sentiment trend across all customer conversations."""
        conversation_ids = self.customer_conversations.get(customer_id, [])
        trend = []

        for cid in conversation_ids:
            conv = self.conversations.get(cid)
            if conv:
                trend.append({
                    'conversation_id': cid,
                    'sentiment': conv.sentiment_score,
                    'status': conv.status,
                    'date': conv.started_at
                })

        return sorted(trend, key=lambda x: x['date'])

    def get_sentiment_alerts(self, threshold: float = 0.3) -> list:
        """Get all active conversations with negative sentiment."""
        alerts = []
        for conv in self.conversations.values():
            if (conv.status == ConversationStatus.ACTIVE and
                    conv.sentiment_score < threshold):
                alerts.append({
                    'conversation_id': conv.id,
                    'customer_id': conv.customer_id,
                    'sentiment': conv.sentiment_score,
                    'channel': conv.initial_channel,
                    'message_count': len(conv.messages)
                })
        return alerts

    # ─── Cross-Channel Continuity ────────────────────────────────────────

    def detect_channel_switch(self, customer_id: str,
                               new_channel: str) -> bool:
        """Detect if a customer has switched channels in an active conversation."""
        conversation = self.get_active_conversation(customer_id)
        if conversation and new_channel not in conversation.channel_history:
            return True
        return False

    def merge_conversations(self, primary_id: str,
                             secondary_id: str) -> Optional[Conversation]:
        """Merge two conversations (e.g., same customer, different channels)."""
        primary = self.conversations.get(primary_id)
        secondary = self.conversations.get(secondary_id)

        if not primary or not secondary:
            return None

        # Move messages from secondary to primary
        for msg in secondary.messages:
            msg.conversation_id = primary_id
            primary.add_message(msg)

        # Merge channel history
        for ch in secondary.channel_history:
            if ch not in primary.channel_history:
                primary.channel_history.append(ch)

        # Merge topics
        for topic in secondary.topics:
            if topic not in primary.topics:
                primary.topics.append(topic)

        # Mark secondary as merged
        secondary.status = ConversationStatus.RESOLVED
        secondary.resolution_type = ResolutionType.MERGED
        secondary.metadata['merged_into'] = primary_id

        return primary

    # ─── Topic Tracking ──────────────────────────────────────────────────

    def track_topics(self, conversation_id: str, topics: list) -> None:
        """Track topics discussed in a conversation."""
        conversation = self.conversations.get(conversation_id)
        if conversation:
            for topic in topics:
                if topic not in conversation.topics:
                    conversation.topics.append(topic)

    def get_popular_topics(self, hours: int = 24) -> list:
        """Get most discussed topics in the time window."""
        topic_counts = {}
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        for conv in self.conversations.values():
            started = datetime.fromisoformat(conv.started_at)
            if started >= cutoff:
                for topic in conv.topics:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1

        return sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)

    # ─── Reporting ───────────────────────────────────────────────────────

    def get_summary_stats(self) -> dict:
        """Get summary statistics for reporting."""
        total_customers = len(self.customers)
        total_conversations = len(self.conversations)
        active_conversations = sum(
            1 for c in self.conversations.values()
            if c.status == ConversationStatus.ACTIVE
        )
        escalated = sum(
            1 for c in self.conversations.values()
            if c.status == ConversationStatus.ESCALATED
        )
        resolved = sum(
            1 for c in self.conversations.values()
            if c.status == ConversationStatus.RESOLVED
        )

        avg_sentiment = 0
        if self.conversations:
            sentiments = [c.sentiment_score for c in self.conversations.values()]
            avg_sentiment = sum(sentiments) / len(sentiments)

        # Channel breakdown
        channel_counts = {}
        for conv in self.conversations.values():
            ch = conv.initial_channel
            channel_counts[ch] = channel_counts.get(ch, 0) + 1

        return {
            'total_customers': total_customers,
            'total_conversations': total_conversations,
            'active_conversations': active_conversations,
            'escalated': escalated,
            'resolved': resolved,
            'avg_sentiment': round(avg_sentiment, 2),
            'channel_breakdown': channel_counts,
            'popular_topics': self.get_popular_topics()[:5]
        }

    # ─── Persistence (Prototype: JSON file) ──────────────────────────────

    def save_state(self, filepath: str = None) -> None:
        """Save current state to JSON file."""
        if not filepath:
            filepath = os.path.join(os.path.dirname(__file__), 'state.json')

        state = {
            'customers': {k: asdict(v) for k, v in self.customers.items()},
            'conversations': {k: asdict(v) for k, v in self.conversations.items()},
            'email_index': self.email_to_customer,
            'phone_index': self.phone_to_customer,
            'customer_conversations': self.customer_conversations,
            'saved_at': datetime.utcnow().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)

    def load_state(self, filepath: str = None) -> None:
        """Load state from JSON file."""
        if not filepath:
            filepath = os.path.join(os.path.dirname(__file__), 'state.json')

        if not os.path.exists(filepath):
            return

        with open(filepath, 'r') as f:
            state = json.load(f)

        # Reconstruct objects
        for cid, cdata in state.get('customers', {}).items():
            customer = Customer(**cdata)
            self.customers[cid] = customer

        for conv_id, conv_data in state.get('conversations', {}).items():
            conv = Conversation(**conv_data)
            self.conversations[conv_id] = conv

        self.email_to_customer = state.get('email_index', {})
        self.phone_to_customer = state.get('phone_index', {})
        self.customer_conversations = state.get('customer_conversations', {})
