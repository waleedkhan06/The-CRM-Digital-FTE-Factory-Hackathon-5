"""
Customer Success FTE — Prototype Core Loop
============================================
Phase 1: Incubation

This is the initial prototype that handles the core customer interaction loop:
1. Takes a customer message as input (with channel metadata)
2. Normalizes the message regardless of source channel
3. Searches the product docs for relevant information
4. Decides if escalation is needed
5. Generates a helpful response
6. Formats response appropriately for the channel

This prototype uses simple keyword-based search (no embeddings yet).
The production version will use PostgreSQL with pgvector for semantic search.
"""

import json
import re
import os
from enum import Enum
from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict


# ─── Enums ───────────────────────────────────────────────────────────────────

class Channel(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEB_FORM = "web_form"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class EscalationReason(str, Enum):
    NONE = "none"
    PRICING_INQUIRY = "pricing_inquiry"
    REFUND_REQUEST = "refund_request"
    LEGAL_THREAT = "legal_threat"
    COMPLIANCE_QUESTION = "compliance_question"
    ANGRY_CUSTOMER = "angry_customer"
    HUMAN_REQUESTED = "human_requested"
    ENGINEERING_BUG = "engineering_bug"
    ENTERPRISE_INQUIRY = "enterprise_inquiry"
    CANNOT_ANSWER = "cannot_answer"
    COMPETITOR_QUESTION = "competitor_question"


# ─── Data Classes ────────────────────────────────────────────────────────────

@dataclass
class CustomerMessage:
    """Normalized customer message regardless of source channel."""
    content: str
    channel: Channel
    customer_id: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_name: Optional[str] = None
    subject: Optional[str] = None
    category: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict = field(default_factory=dict)


@dataclass
class AgentResponse:
    """Response from the agent."""
    ticket_id: str
    response_text: str
    channel: Channel
    escalated: bool = False
    escalation_reason: EscalationReason = EscalationReason.NONE
    escalation_priority: str = "P3"
    sentiment_score: float = 0.5
    topics: list = field(default_factory=list)
    tool_calls: list = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ─── Knowledge Base (Simple text-based for prototype) ────────────────────────

class SimpleKnowledgeBase:
    """Simple keyword-based knowledge base for the prototype.
    
    Production version will use PostgreSQL with pgvector for semantic search.
    """

    def __init__(self, docs_path: str = None):
        self.entries = []
        self._load_documents(docs_path)

    def _load_documents(self, docs_path: str = None):
        """Load product documentation into searchable entries."""
        if docs_path and os.path.exists(docs_path):
            with open(docs_path, 'r') as f:
                content = f.read()
            # Split by sections (## headers)
            sections = re.split(r'\n## ', content)
            for section in sections:
                lines = section.strip().split('\n')
                if lines:
                    title = lines[0].strip('# ')
                    body = '\n'.join(lines[1:])
                    self.entries.append({
                        'title': title,
                        'content': body,
                        'category': 'product_docs',
                        'keywords': self._extract_keywords(title + ' ' + body)
                    })
        else:
            # Use built-in knowledge base
            self._load_builtin_kb()

    def _load_builtin_kb(self):
        """Built-in knowledge base entries."""
        kb_entries = [
            {
                'title': 'Reset Password',
                'content': (
                    'To reset your password:\n'
                    '1. Go to techcorp.io/login\n'
                    '2. Click "Forgot Password?"\n'
                    '3. Enter your email address\n'
                    '4. Check your inbox for the reset link (valid for 1 hour)\n'
                    '5. Click the link and set a new password\n'
                    'Password requirements: minimum 8 characters, 1 uppercase, 1 number.\n'
                    'If you don\'t receive the email within 5 minutes, check your spam folder.'
                ),
                'category': 'account',
                'keywords': ['password', 'reset', 'forgot', 'login', 'sign in', 'can\'t access', 'locked']
            },
            {
                'title': 'Invite Team Members',
                'content': (
                    'To invite team members:\n'
                    '1. Go to Settings → Team Members\n'
                    '2. Click "Invite Members"\n'
                    '3. Enter email addresses (comma-separated for multiple)\n'
                    '4. Select role: Member (full access) or Viewer (read-only)\n'
                    '5. Click "Send Invites"\n'
                    'You can also share a join link from Settings → Team Members → Share Link.'
                ),
                'category': 'collaboration',
                'keywords': ['invite', 'add member', 'team', 'join', 'add people', 'add user']
            },
            {
                'title': 'API Rate Limits',
                'content': (
                    'API rate limits by plan:\n'
                    '- Starter: 100 requests/hour, burst limit 20\n'
                    '- Professional: 1,000 requests/hour, burst limit 200\n'
                    '- Enterprise: 10,000 requests/hour, burst limit 2,000\n'
                    '\n'
                    'If you receive a 429 error, you\'ve exceeded your rate limit.\n'
                    'Wait for the rate limit window to reset (1 hour) or implement exponential backoff.\n'
                    'Consider upgrading your plan for higher limits.\n'
                    '\n'
                    'All API requests require a Bearer token in the Authorization header.'
                ),
                'category': 'api',
                'keywords': ['api', 'rate limit', '429', 'requests', 'throttle', 'quota']
            },
            {
                'title': 'Workflow Automation',
                'content': (
                    'To create an automation rule:\n'
                    '1. Go to Project Settings → Automation\n'
                    '2. Click "+ New Rule"\n'
                    '3. Choose a trigger: task created, task assigned, due date approaching,\n'
                    '   task completed, status changed, or comment added\n'
                    '4. Choose an action: assign to team member, set due date, add label,\n'
                    '   move to column, send notification, or create subtask\n'
                    '5. Click "Save Rule"\n'
                    '\n'
                    'Automation limits:\n'
                    '- Starter: 100 runs/month\n'
                    '- Professional: 10,000 runs/month\n'
                    '- Enterprise: Unlimited'
                ),
                'category': 'automation',
                'keywords': ['automation', 'rule', 'trigger', 'workflow', 'auto', 'automate']
            },
            {
                'title': 'Pricing Plans',
                'content': (
                    'TechCorp Plans:\n'
                    '- Starter (Free): Up to 5 users, 1GB storage, basic features, email support\n'
                    '- Professional ($29/user/month): Unlimited users, 50GB storage, automation,\n'
                    '  API access, priority support, 200+ integrations\n'
                    '- Enterprise ($79/user/month): Everything in Professional plus unlimited storage,\n'
                    '  unlimited automation, SSO/SAML, custom integrations, 99.9% SLA,\n'
                    '  dedicated account manager, phone support\n'
                    '\n'
                    'For custom pricing, volume discounts, or nonprofit/education pricing,\n'
                    'please contact our sales team at sales@techcorp.io.'
                ),
                'category': 'billing',
                'keywords': ['pricing', 'plan', 'cost', 'price', 'upgrade', 'plan comparison']
            },
            {
                'title': 'Mobile Apps',
                'content': (
                    'TechCorp mobile apps are available for:\n'
                    '- iOS: Search "TechCorp Platform" in the App Store\n'
                    '- Android: Search "TechCorp Platform" in Google Play\n'
                    '\n'
                    'Mobile features:\n'
                    '- View and edit tasks\n'
                    '- Comment on tasks\n'
                    '- Push notifications\n'
                    '- View project boards and lists\n'
                    '- Upload photos from your device\n'
                    '- Quick task creation via widget\n'
                    '- Offline mode (changes sync when connected)\n'
                    '- Biometric login (Face ID / fingerprint)'
                ),
                'category': 'mobile',
                'keywords': ['mobile', 'app', 'ios', 'android', 'phone', 'iphone', 'tablet']
            },
            {
                'title': 'Two-Factor Authentication (2FA)',
                'content': (
                    'To enable two-factor authentication:\n'
                    '1. Go to Settings → Security\n'
                    '2. Click "Enable Two-Factor Authentication"\n'
                    '3. Scan the QR code with your authenticator app (Google Authenticator, Authy)\n'
                    '4. Enter the 6-digit code to verify\n'
                    '5. Save your backup codes in a secure location\n'
                    '\n'
                    'Enterprise plan admins can enforce 2FA for all team members.'
                ),
                'category': 'security',
                'keywords': ['2fa', 'two-factor', 'authentication', 'security', 'mfa', 'authenticator']
            },
            {
                'title': 'File Attachments',
                'content': (
                    'File attachment limits:\n'
                    '- Maximum file size: 100MB per file\n'
                    '- Supported formats: images, PDFs, documents, spreadsheets\n'
                    '- Storage limits: Starter 1GB, Professional 50GB, Enterprise Unlimited\n'
                    '\n'
                    'To attach files:\n'
                    '- Drag and drop into tasks or comments\n'
                    '- Or click the attachment icon in the task detail view\n'
                    '- On mobile, you can take photos and attach directly'
                ),
                'category': 'general',
                'keywords': ['file', 'attach', 'upload', 'document', 'image', 'photo', 'size limit']
            },
            {
                'title': 'Delete Account',
                'content': (
                    'To delete your account:\n'
                    '1. Go to Settings → Account\n'
                    '2. Scroll to "Danger Zone"\n'
                    '3. Click "Delete Account"\n'
                    '4. Confirm by typing your email address\n'
                    '5. WARNING: This action is irreversible. All your data will be permanently deleted.\n'
                    '\n'
                    'To cancel subscription without deleting account:\n'
                    '1. Go to Settings → Billing\n'
                    '2. Click "Cancel Subscription"\n'
                    '3. Select a reason\n'
                    '4. Confirm cancellation\n'
                    'You retain access until the end of your billing period.'
                ),
                'category': 'account',
                'keywords': ['delete', 'cancel', 'close account', 'remove account', 'subscription']
            },
            {
                'title': 'Task Management Basics',
                'content': (
                    'Creating and managing tasks:\n'
                    '1. Open any project\n'
                    '2. Click "+ Add Task" or the "+" button in any column\n'
                    '3. Enter a task title and press Enter\n'
                    '4. Click the task to add details:\n'
                    '   - Description (supports Markdown)\n'
                    '   - Assignee\n'
                    '   - Due date\n'
                    '   - Priority (Low, Medium, High, Urgent)\n'
                    '   - Labels (color-coded tags)\n'
                    '   - Attachments (up to 100MB each)\n'
                    '   - Subtasks\n'
                    '   - Dependencies\n'
                    '\n'
                    'Task status workflow: To Do → In Progress → In Review → Done\n'
                    'Customize this in Project Settings → Workflow.'
                ),
                'category': 'tasks',
                'keywords': ['task', 'create task', 'manage', 'assign', 'priority', 'due date', 'subtask']
            },
            {
                'title': 'Project Views',
                'content': (
                    'TechCorp offers multiple project views:\n'
                    '- Board View: Kanban-style columns for visual task management\n'
                    '- List View: Spreadsheet-like list for detailed task tracking\n'
                    '- Timeline View: Gantt chart for project planning and dependencies\n'
                    '- Calendar View: Tasks displayed on a calendar by due date\n'
                    '\n'
                    'Switch views using the view selector at the top of any project.\n'
                    'Starter plan includes Board and List views.\n'
                    'Professional and Enterprise plans include all views.'
                ),
                'category': 'projects',
                'keywords': ['view', 'board', 'kanban', 'timeline', 'gantt', 'calendar', 'list']
            },
            {
                'title': 'System Status',
                'content': (
                    'Check real-time system status at status.techcorp.io\n'
                    '\n'
                    'Subscribe to status updates:\n'
                    '- Email notifications\n'
                    '- SMS alerts\n'
                    '- Slack webhook\n'
                    '- RSS feed\n'
                    '\n'
                    'If you\'re experiencing issues, check status.techcorp.io first\n'
                    'to see if there\'s a known outage.'
                ),
                'category': 'status',
                'keywords': ['status', 'down', 'outage', 'not working', 'error', 'unavailable']
            },
        ]

        for entry in kb_entries:
            entry['keywords'] = self._extract_keywords(
                entry['title'] + ' ' + entry['content']
            )
            self.entries.append(entry)

    def _extract_keywords(self, text: str) -> set:
        """Extract keywords from text."""
        # Simple keyword extraction
        text = text.lower()
        # Remove punctuation
        text = re.sub(r'[^\w\s]', '', text)
        words = set(text.split())
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'shall',
            'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in',
            'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
            'through', 'during', 'before', 'after', 'above', 'below',
            'between', 'out', 'off', 'over', 'under', 'again', 'further',
            'then', 'once', 'and', 'but', 'or', 'nor', 'not', 'so',
            'yet', 'both', 'either', 'neither', 'each', 'every', 'all',
            'any', 'few', 'more', 'most', 'other', 'some', 'such',
            'no', 'only', 'own', 'same', 'than', 'too', 'very',
            'just', 'because', 'if', 'when', 'where', 'how', 'what',
            'which', 'who', 'whom', 'this', 'that', 'these', 'those',
            'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'you',
            'your', 'yours', 'he', 'him', 'his', 'she', 'her', 'it',
            'its', 'they', 'them', 'their', 'about'
        }
        return words - stop_words

    def search(self, query: str, max_results: int = 5) -> list:
        """Search knowledge base for relevant entries."""
        query_keywords = self._extract_keywords(query)

        scored_results = []
        for entry in self.entries:
            # Count keyword matches
            matches = len(query_keywords & entry['keywords'])
            if matches > 0:
                scored_results.append({
                    'title': entry['title'],
                    'content': entry['content'],
                    'category': entry['category'],
                    'score': matches / max(len(query_keywords), 1)
                })

        # Sort by score descending
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        return scored_results[:max_results]


# ─── Escalation Engine ──────────────────────────────────────────────────────

class EscalationEngine:
    """Determines if a conversation should be escalated to a human agent."""

    # Immediate escalation keywords
    LEGAL_KEYWORDS = ['lawyer', 'attorney', 'sue', 'lawsuit', 'legal action', 'court', 'breach of contract']
    REFUND_KEYWORDS = ['refund', 'chargeback', 'dispute charge', 'cancel subscription', 'cancel my subscription']
    HUMAN_REQUEST_KEYWORDS = ['human', 'agent', 'representative', 'real person', 'speak to someone', 'talk to someone', 'live agent']
    COMPETITOR_KEYWORDS = ['asana', 'monday.com', 'notion', 'jira', 'trello', 'basecamp', 'clickup']
    COMPLIANCE_KEYWORDS = ['gdpr', 'hipaa', 'soc 2', 'compliance', 'data retention', 'baa', 'data residency']

    def evaluate(self, message: str, sentiment_score: float) -> tuple[bool, EscalationReason, str]:
        """Evaluate if escalation is needed.
        
        Returns: (should_escalate, reason, priority)
        """
        text = message.lower()

        # Check for legal threats
        if any(kw in text for kw in self.LEGAL_KEYWORDS):
            return True, EscalationReason.LEGAL_THREAT, "P0"

        # Check for refund requests
        if any(kw in text for kw in self.REFUND_KEYWORDS):
            return True, EscalationReason.REFUND_REQUEST, "P1"

        # Check for explicit human request
        if any(kw in text for kw in self.HUMAN_REQUEST_KEYWORDS):
            return True, EscalationReason.HUMAN_REQUESTED, "P2"

        # Check for angry customer (negative sentiment)
        if sentiment_score < 0.3:
            return True, EscalationReason.ANGRY_CUSTOMER, "P1"

        # Check for compliance questions
        if any(kw in text for kw in self.COMPLIANCE_KEYWORDS):
            return True, EscalationReason.COMPLIANCE_QUESTION, "P1"

        # Check for pricing inquiries (not just "what are your plans")
        pricing_indicators = ['discount', 'negotiate', 'custom pricing', 'bulk pricing',
                            'nonprofit discount', 'education pricing', 'student pricing',
                            'special pricing', 'volume discount']
        if any(kw in text for kw in pricing_indicators):
            return True, EscalationReason.PRICING_INQUIRY, "P2"

        # Check for competitor questions
        if any(kw in text for kw in self.COMPETITOR_KEYWORDS):
            return True, EscalationReason.COMPETITOR_QUESTION, "P3"

        return False, EscalationReason.NONE, "P3"


# ─── Sentiment Analyzer (Simple heuristic-based) ────────────────────────────

class SimpleSentimentAnalyzer:
    """Simple heuristic-based sentiment analyzer for the prototype.
    
    Production version will use OpenAI API or a dedicated ML model.
    """

    POSITIVE_WORDS = {
        'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
        'love', 'loved', 'loving', 'like', 'liked', 'thanks', 'thank',
        'appreciate', 'helpful', 'awesome', 'perfect', 'happy', 'pleased',
        'beautiful', 'best', 'brilliant', 'cool', 'nice', 'superb', '🎉', '😊', '👍'
    }

    NEGATIVE_WORDS = {
        'bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'hated',
        'angry', 'frustrated', 'frustrating', 'annoyed', 'disappointed',
        'disappointing', 'useless', 'garbage', 'broken', 'not working',
        'doesn\'t work', 'does not work', 'sucks', 'ridiculous', 'unacceptable',
        'unacceptable', 'outrageous', 'scam', 'fraud', 'sue', 'lawsuit',
        'refund', 'cancel', 'worst ever', 'waste', 'pathetic', 'stupid'
    }

    INTENSIFIERS = {
        'very', 'really', 'extremely', 'incredibly', 'absolutely',
        'totally', 'completely', 'utterly', 'so', 'completely'
    }

    NEGATORS = {'not', 'no', 'never', 'neither', 'n\'t', 'don\'t', 'doesn\'t', 'didn\'t', 'won\'t', 'wouldn\'t', 'can\'t', 'cannot'}

    def analyze(self, text: str) -> float:
        """Analyze sentiment of text. Returns score from -1.0 (very negative) to 1.0 (very positive)."""
        text = text.lower()
        words = text.split()

        positive_score = 0
        negative_score = 0
        intensifier_multiplier = 1.0
        negation_active = False

        for i, word in enumerate(words):
            # Check for negation
            if word in self.NEGATORS:
                negation_active = True
                continue

            # Check for intensifiers
            if word in self.INTENSIFIERS:
                intensifier_multiplier = 1.5
                continue

            # Score words
            if word in self.POSITIVE_WORDS:
                if negation_active:
                    negative_score += 1 * intensifier_multiplier
                else:
                    positive_score += 1 * intensifier_multiplier
            elif word in self.NEGATIVE_WORDS:
                if negation_active:
                    positive_score += 0.5 * intensifier_multiplier
                else:
                    negative_score += 1 * intensifier_multiplier

            # Reset flags
            negation_active = False
            intensifier_multiplier = 1.0

        total = positive_score + negative_score
        if total == 0:
            return 0.5  # Neutral

        # Normalize to 0-1 range
        raw_score = (positive_score - negative_score) / total
        # Convert from [-1, 1] to [0, 1]
        normalized = (raw_score + 1) / 2

        return round(normalized, 2)


# ─── Response Formatter ─────────────────────────────────────────────────────

class ResponseFormatter:
    """Formats responses appropriately for each channel."""

    @staticmethod
    def format_for_channel(response_text: str, channel: Channel, ticket_id: str = "",
                          customer_name: str = "") -> str:
        """Format response for the specific channel."""

        if channel == Channel.EMAIL:
            greeting = f"Dear {customer_name}," if customer_name else "Dear Customer,"
            signature = (
                f"\n\nIf you have any further questions, please don't hesitate to reply to this email.\n\n"
                f"Best regards,\n"
                f"TechCorp AI Support Team\n"
                f"---\n"
                f"Ticket Reference: {ticket_id}\n"
                f"This response was generated by our AI assistant. For complex issues, you can request human support."
            )
            return f"{greeting}\n\nThank you for reaching out to TechCorp Support.\n\n{response_text}{signature}"

        elif channel == Channel.WHATSAPP:
            # Keep it short for WhatsApp
            if len(response_text) > 300:
                response_text = response_text[:297] + "..."
            greeting = f"Hi {customer_name}! " if customer_name else "Hi! "
            return f"{greeting}{response_text}\n\nReply for more help or type 'human' for live support. 😊"

        else:  # WEB_FORM
            return (
                f"{response_text}\n\n"
                f"---\n"
                f"Need more help? Reply to this message or visit our support portal."
            )


# ─── Main Agent Loop ────────────────────────────────────────────────────────

class CustomerSuccessAgent:
    """Main customer success agent — the core interaction loop."""

    def __init__(self, kb_path: str = None):
        self.kb = SimpleKnowledgeBase(kb_path)
        self.escalation_engine = EscalationEngine()
        self.sentiment_analyzer = SimpleSentimentAnalyzer()
        self.formatter = ResponseFormatter()
        self.ticket_counter = 0

    def _generate_ticket_id(self) -> str:
        """Generate a unique ticket ID."""
        self.ticket_counter += 1
        return f"TK-2026-{self.ticket_counter:04d}"

    def _normalize_message(self, raw_message: dict, channel: str) -> CustomerMessage:
        """Normalize incoming message from any channel."""
        channel_enum = Channel(channel)

        return CustomerMessage(
            content=raw_message.get('content', '').strip(),
            channel=channel_enum,
            customer_email=raw_message.get('customer_email'),
            customer_phone=raw_message.get('customer_phone'),
            customer_name=raw_message.get('customer_name', ''),
            subject=raw_message.get('subject', ''),
            category=raw_message.get('category', 'general'),
            priority=Priority(raw_message.get('priority', 'medium')),
            metadata=raw_message.get('metadata', {})
        )

    def _generate_response(self, message: CustomerMessage,
                           kb_results: list, sentiment: float) -> str:
        """Generate a helpful response based on knowledge base results."""

        if not kb_results:
            if sentiment < 0.4:
                return (
                    "I'm sorry you're experiencing this issue. I want to make sure you get "
                    "the best help possible. I'm connecting you with our specialist team who "
                    "will have all the context from our conversation. They'll be in touch shortly."
                )
            return (
                "Thank you for your question. I want to make sure I give you the most accurate "
                "information. Let me connect you with our team who can provide a detailed answer. "
                "They'll have all the context from our conversation, so you won't need to repeat yourself."
            )

        # Build response from top knowledge base results
        best_result = kb_results[0]
        response = best_result['content']

        # Add context from additional results if relevant
        if len(kb_results) > 1 and kb_results[1]['score'] > 0.3:
            response += f"\n\nAdditionally, you might find this helpful:\n{kb_results[1]['content'][:300]}"

        return response

    def process_message(self, raw_message: dict, channel: str) -> AgentResponse:
        """Main processing loop — handles a customer message from any channel."""

        # Step 1: Normalize the message
        message = self._normalize_message(raw_message, channel)

        # Step 2: Handle edge cases
        if not message.content or len(message.content.strip()) < 2:
            return self._handle_empty_message(message)

        # Step 3: Analyze sentiment
        sentiment = self.sentiment_analyzer.analyze(message.content)

        # Step 4: Check for escalation
        should_escalate, reason, priority = self.escalation_engine.evaluate(
            message.content, sentiment
        )

        # Step 5: Search knowledge base
        kb_results = self.kb.search(message.content, max_results=3)

        # Step 6: Generate response
        if should_escalate:
            response_text = self._generate_escalation_response(reason, message, kb_results)
        else:
            response_text = self._generate_response(message, kb_results, sentiment)

        # Step 7: Format for channel
        ticket_id = self._generate_ticket_id()
        formatted_response = self.formatter.format_for_channel(
            response_text, message.channel, ticket_id, message.customer_name
        )

        # Step 8: Build response object
        return AgentResponse(
            ticket_id=ticket_id,
            response_text=formatted_response,
            channel=message.channel,
            escalated=should_escalate,
            escalation_reason=reason,
            escalation_priority=priority,
            sentiment_score=sentiment,
            topics=[r['category'] for r in kb_results[:2]] if kb_results else ['general'],
            tool_calls=['sentiment_analysis', 'escalation_check', 'knowledge_search', 'response_generation']
        )

    def _handle_empty_message(self, message: CustomerMessage) -> AgentResponse:
        """Handle empty or meaningless messages."""
        ticket_id = self._generate_ticket_id()

        if message.channel == Channel.WHATSAPP:
            response = "Hi! 👋 How can I help you today? Feel free to describe your question or issue."
        else:
            response = (
                "Hello! Thank you for reaching out to TechCorp Support. "
                "It looks like your message may have come through empty. "
                "Could you please describe your question or issue in more detail? "
                "I'm here to help!"
            )

        formatted = self.formatter.format_for_channel(
            response, message.channel, ticket_id, message.customer_name
        )

        return AgentResponse(
            ticket_id=ticket_id,
            response_text=formatted,
            channel=message.channel,
            sentiment_score=0.5,
            topics=['general'],
            tool_calls=['empty_message_handler']
        )

    def _generate_escalation_response(self, reason: EscalationReason,
                                       message: CustomerMessage,
                                       kb_results: list) -> str:
        """Generate an appropriate response when escalation is needed."""

        response_map = {
            EscalationReason.PRICING_INQUIRY: (
                "Thank you for your interest in our pricing options! I'd love to connect you "
                "with our sales team who can provide personalized pricing based on your needs. "
                "They'll be in touch shortly with the best options for your team."
            ),
            EscalationReason.REFUND_REQUEST: (
                "I understand you'd like to discuss a refund. I'm connecting you with our "
                "billing team who can review your account and help resolve this. They'll have "
                "all the context from our conversation."
            ),
            EscalationReason.LEGAL_THREAT: (
                "I take your concerns very seriously. I'm immediately escalating this to our "
                "senior team who will personally review your situation and respond. They'll be "
                "in touch as soon as possible."
            ),
            EscalationReason.COMPLIANCE_QUESTION: (
                "That's an important question about compliance. I'm connecting you with our "
                "compliance team who can provide the detailed documentation you need. They'll "
                "respond with the appropriate information shortly."
            ),
            EscalationReason.ANGRY_CUSTOMER: (
                "I completely understand your frustration, and I'm sorry you've had this experience. "
                "I'm connecting you with our senior support team who will personally look into your "
                "situation. They'll be in touch within the hour."
            ),
            EscalationReason.HUMAN_REQUESTED: (
                "Of course! I'm connecting you with a human agent right now. They'll have all the "
                "context from our conversation, so you won't need to repeat yourself. "
                "Please hold on for just a moment."
            ),
            EscalationReason.ENGINEERING_BUG: (
                "Thank you for reporting this issue. I'm creating a detailed bug report for our "
                "engineering team to investigate. They'll work on a fix and we'll update you as "
                "soon as we have more information."
            ),
            EscalationReason.COMPETITOR_QUESTION: (
                "I'd be happy to tell you more about what makes TechCorp great! Let me connect "
                "you with our product specialist who can give you a comprehensive overview of our "
                "features and how we compare. They'll be in touch shortly."
            ),
            EscalationReason.ENTERPRISE_INQUIRY: (
                "Great question about our enterprise features! I'm connecting you with our "
                "enterprise team who can provide detailed information and a personalized demo. "
                "They'll reach out to you directly."
            ),
            EscalationReason.CANNOT_ANSWER: (
                "That's a great question, and I want to make sure I give you the most accurate "
                "information. Let me connect you with our specialist team who can provide a "
                "detailed answer."
            ),
        }

        return response_map.get(reason, (
            "Thank you for reaching out. I'm connecting you with our team who can best assist you. "
            "They'll have all the context from our conversation."
        ))


# ─── CLI Runner (for testing) ───────────────────────────────────────────────

def main():
    """Interactive CLI for testing the prototype."""
    import sys

    # Initialize agent
    docs_path = os.path.join(os.path.dirname(__file__), '..', 'context', 'product-docs.md')
    agent = CustomerSuccessAgent(kb_path=docs_path)

    print("=" * 60)
    print("  TechCorp Customer Success FTE — Prototype")
    print("  Type 'quit' to exit, 'test' to run sample tickets")
    print("=" * 60)

    while True:
        print("\n---")
        channel = input("Channel (email/whatsapp/web) [email]: ").strip().lower() or 'email'
        if channel == 'quit':
            break

        if channel == 'test':
            run_sample_tests(agent)
            continue

        content = input("Customer message: ").strip()
        if content == 'quit':
            break

        raw_message = {
            'content': content,
            'channel': channel,
            'customer_name': 'Test User',
            'customer_email': 'test@example.com',
        }

        response = agent.process_message(raw_message, channel)

        print(f"\n📋 Ticket: {response.ticket_id}")
        print(f"📊 Sentiment: {response.sentiment_score}")
        print(f"🔀 Escalated: {response.escalated} ({response.escalation_reason.value})")
        print(f"📝 Topics: {', '.join(response.topics)}")
        print(f"\n💬 Response:\n{response.response_text}")


def run_sample_tests(agent: CustomerSuccessAgent):
    """Run a few sample tickets from the sample data."""
    samples_path = os.path.join(os.path.dirname(__file__), '..', 'context', 'sample-tickets.json')

    with open(samples_path, 'r') as f:
        samples = json.load(f)

    # Test first 5 samples
    for sample in samples[:5]:
        channel = sample['channel']
        raw_message = {
            'content': sample.get('content', sample.get('message', '')),
            'channel': channel,
            'customer_email': sample.get('customer_email'),
            'customer_phone': sample.get('customer_phone'),
            'customer_name': sample.get('customer_name', ''),
            'subject': sample.get('subject', ''),
            'category': sample.get('category', 'general'),
            'priority': sample.get('priority', 'medium'),
        }

        response = agent.process_message(raw_message, channel)

        print(f"\n{'=' * 50}")
        print(f"📋 Ticket: {response.ticket_id}")
        print(f"📡 Channel: {channel}")
        print(f"📊 Sentiment: {response.sentiment_score}")
        print(f"🔀 Escalated: {response.escalated} ({response.escalation_reason.value})")
        print(f"📝 Topics: {', '.join(response.topics)}")
        print(f"💬 Response preview: {response.response_text[:150]}...")


if __name__ == "__main__":
    main()
