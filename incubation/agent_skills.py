"""
Customer Success FTE — Agent Skills Manifest
=============================================
Phase 1: Incubation

Formal definition of the agent's reusable capabilities (skills).
Each skill defines when to use it, what inputs it needs, and what outputs it produces.

These skills are invoked by the agent during conversation processing and are
designed to be modular, testable, and composable.

Production version: These become @function_tool decorated functions in the
OpenAI Agents SDK implementation.
"""

from typing import Optional
from dataclasses import dataclass, asdict
from datetime import datetime


# ─── Skill Result Types ─────────────────────────────────────────────────────

@dataclass
class SkillResult:
    """Standard result type for all skills."""
    skill_name: str
    success: bool
    output: dict
    confidence: float = 1.0
    error: Optional[str] = None
    execution_time_ms: int = 0


# ─── Skill 1: Knowledge Retrieval ──────────────────────────────────────────

class KnowledgeRetrievalSkill:
    """
    Knowledge Retrieval Skill
    
    When to use: Customer asks product questions
    Inputs: query text, optional category filter, max results
    Outputs: relevant documentation snippets with relevance scores
    
    This skill searches the knowledge base and returns the most relevant
    documentation entries. It uses keyword matching in the prototype and
    will use vector similarity (pgvector) in production.
    """

    def __init__(self, knowledge_base):
        self.kb = knowledge_base

    def execute(self, query: str, max_results: int = 5,
                category: str = None) -> SkillResult:
        """Execute knowledge retrieval."""
        start = datetime.utcnow()

        try:
            results = self.kb.search(query, max_results=max_results)

            if category:
                results = [r for r in results if r.get('category') == category]

            elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)

            if not results:
                return SkillResult(
                    skill_name='knowledge_retrieval',
                    success=True,
                    output={
                        'results': [],
                        'count': 0,
                        'message': 'No relevant documentation found'
                    },
                    confidence=0.0,
                    execution_time_ms=elapsed
                )

            return SkillResult(
                skill_name='knowledge_retrieval',
                success=True,
                output={
                    'results': results,
                    'count': len(results),
                    'best_match': results[0]['title'],
                    'best_score': results[0]['score']
                },
                confidence=results[0]['score'],
                execution_time_ms=elapsed
            )

        except Exception as e:
            return SkillResult(
                skill_name='knowledge_retrieval',
                success=False,
                output={'results': [], 'count': 0},
                confidence=0.0,
                error=str(e)
            )


# ─── Skill 2: Sentiment Analysis ───────────────────────────────────────────

class SentimentAnalysisSkill:
    """
    Sentiment Analysis Skill
    
    When to use: Every customer message
    Inputs: message text
    Outputs: sentiment score (0.0-1.0), confidence, label, escalation recommendation
    
    Analyzes the emotional tone of customer messages to gauge satisfaction
    and determine if escalation is needed.
    """

    def __init__(self, analyzer):
        self.analyzer = analyzer

    def execute(self, message: str) -> SkillResult:
        """Execute sentiment analysis."""
        start = datetime.utcnow()

        try:
            score = self.analyzer.analyze(message)
            elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)

            # Determine label
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

            return SkillResult(
                skill_name='sentiment_analysis',
                success=True,
                output={
                    'score': score,
                    'label': label,
                    'recommendation': recommendation,
                    'requires_attention': score < 0.4
                },
                confidence=0.85 if score > 0.7 or score < 0.3 else 0.6,
                execution_time_ms=elapsed
            )

        except Exception as e:
            return SkillResult(
                skill_name='sentiment_analysis',
                success=False,
                output={'score': 0.5, 'label': 'unknown'},
                confidence=0.0,
                error=str(e)
            )


# ─── Skill 3: Escalation Decision ──────────────────────────────────────────

class EscalationDecisionSkill:
    """
    Escalation Decision Skill
    
    When to use: After generating response, before sending
    Inputs: conversation context, sentiment score/trend, message content
    Outputs: should_escalate (bool), reason, priority, routing suggestion
    
    Evaluates multiple signals to determine if human intervention is needed.
    """

    def __init__(self, escalation_engine):
        self.engine = escalation_engine

    def execute(self, message: str, sentiment_score: float,
                context: dict = None) -> SkillResult:
        """Execute escalation decision."""
        start = datetime.utcnow()

        try:
            should_escalate, reason, priority = self.engine.evaluate(
                message, sentiment_score
            )
            elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)

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
            }

            route_to = routing_map.get(reason.value if hasattr(reason, 'value') else str(reason), 'support_team')

            return SkillResult(
                skill_name='escalation_decision',
                success=True,
                output={
                    'should_escalate': should_escalate,
                    'reason': reason.value if hasattr(reason, 'value') else str(reason),
                    'priority': priority,
                    'route_to': route_to,
                    'context': context or {}
                },
                confidence=0.9,
                execution_time_ms=elapsed
            )

        except Exception as e:
            return SkillResult(
                skill_name='escalation_decision',
                success=False,
                output={'should_escalate': False, 'reason': 'error'},
                confidence=0.0,
                error=str(e)
            )


# ─── Skill 4: Channel Adaptation ───────────────────────────────────────────

class ChannelAdaptationSkill:
    """
    Channel Adaptation Skill
    
    When to use: Before sending any response
    Inputs: response text, target channel, customer name
    Outputs: formatted response appropriate for the channel
    
    Adapts the response text to match the communication style, length
    constraints, and formatting conventions of each channel.
    """

    CHANNEL_CONFIGS = {
        'email': {
            'max_length': 2000,
            'style': 'formal',
            'requires_greeting': True,
            'requires_signature': True,
            'supports_formatting': True,
            'emoji_allowed': False
        },
        'whatsapp': {
            'max_length': 1600,
            'preferred_length': 300,
            'style': 'casual',
            'requires_greeting': True,
            'requires_signature': False,
            'supports_formatting': False,
            'emoji_allowed': True
        },
        'web_form': {
            'max_length': 1000,
            'style': 'semi_formal',
            'requires_greeting': False,
            'requires_signature': True,
            'supports_formatting': True,
            'emoji_allowed': False
        }
    }

    def __init__(self, formatter):
        self.formatter = formatter

    def execute(self, response_text: str, channel: str,
                customer_name: str = "", ticket_id: str = "") -> SkillResult:
        """Execute channel adaptation."""
        start = datetime.utcnow()

        try:
            config = self.CHANNEL_CONFIGS.get(channel, self.CHANNEL_CONFIGS['web_form'])

            # Format using the response formatter
            formatted = self.formatter.format_for_channel(
                response_text, channel, ticket_id, customer_name
            )

            # Truncate if exceeds max length
            if len(formatted) > config['max_length']:
                formatted = formatted[:config['max_length'] - 3] + "..."

            elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)

            return SkillResult(
                skill_name='channel_adaptation',
                success=True,
                output={
                    'formatted_response': formatted,
                    'channel': channel,
                    'length': len(formatted),
                    'within_limits': len(formatted) <= config['max_length'],
                    'style': config['style']
                },
                confidence=1.0,
                execution_time_ms=elapsed
            )

        except Exception as e:
            return SkillResult(
                skill_name='channel_adaptation',
                success=False,
                output={'formatted_response': response_text},
                confidence=0.0,
                error=str(e)
            )


# ─── Skill 5: Customer Identification ──────────────────────────────────────

class CustomerIdentificationSkill:
    """
    Customer Identification Skill
    
    When to use: On every incoming message
    Inputs: message metadata (email, phone, name)
    Outputs: unified customer_id, profile summary, cross-channel flag
    
    Identifies or creates a customer record and detects if they've
    contacted us through multiple channels.
    """

    def __init__(self, memory_manager):
        self.memory = memory_manager

    def execute(self, email: str = None, phone: str = None,
                name: str = "") -> SkillResult:
        """Execute customer identification."""
        start = datetime.utcnow()

        try:
            customer = self.memory.get_or_create_customer(
                email=email, phone=phone, name=name
            )

            history = self.memory.get_customer_history(customer.id)
            is_new = history.get('total_conversations', 0) == 0

            # Check for cross-channel activity
            channels_used = set()
            for conv in history.get('conversations', []):
                channels_used.add(conv.get('initial_channel'))
                for ch in conv.get('channels_used', []):
                    channels_used.add(ch)

            is_cross_channel = len(channels_used) > 1

            elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)

            return SkillResult(
                skill_name='customer_identification',
                success=True,
                output={
                    'customer_id': customer.id,
                    'name': customer.name,
                    'email': customer.email,
                    'phone': customer.phone,
                    'is_new_customer': is_new,
                    'is_cross_channel': is_cross_channel,
                    'total_interactions': customer.total_interactions,
                    'avg_sentiment': customer.avg_sentiment,
                    'channels_used': list(channels_used)
                },
                confidence=0.95 if email or phone else 0.5,
                execution_time_ms=elapsed
            )

        except Exception as e:
            return SkillResult(
                skill_name='customer_identification',
                success=False,
                output={'customer_id': None},
                confidence=0.0,
                error=str(e)
            )


# ─── Skills Manifest (Registry) ────────────────────────────────────────────

class SkillsManifest:
    """
    Registry of all agent skills with metadata.
    
    This manifest describes all available skills, when to use them,
    and how they compose together.
    """

    SKILLS = {
        'knowledge_retrieval': {
            'description': 'Search product documentation for relevant information',
            'trigger': 'Customer asks product/feature questions',
            'inputs': ['query: str', 'max_results: int = 5', 'category: str = None'],
            'outputs': ['results: list', 'count: int', 'best_match: str', 'best_score: float'],
            'priority': 'high',  # Run early in conversation processing
            'required': True
        },
        'sentiment_analysis': {
            'description': 'Analyze emotional tone of customer message',
            'trigger': 'Every incoming customer message',
            'inputs': ['message: str'],
            'outputs': ['score: float', 'label: str', 'recommendation: str', 'requires_attention: bool'],
            'priority': 'critical',  # Run first, affects escalation decision
            'required': True
        },
        'escalation_decision': {
            'description': 'Determine if human intervention is needed',
            'trigger': 'After generating response, before sending',
            'inputs': ['message: str', 'sentiment_score: float', 'context: dict'],
            'outputs': ['should_escalate: bool', 'reason: str', 'priority: str', 'route_to: str'],
            'priority': 'high',  # Run after response generation
            'required': True
        },
        'channel_adaptation': {
            'description': 'Format response for the target channel',
            'trigger': 'Before sending any response',
            'inputs': ['response_text: str', 'channel: str', 'customer_name: str', 'ticket_id: str'],
            'outputs': ['formatted_response: str', 'length: int', 'within_limits: bool', 'style: str'],
            'priority': 'critical',  # Must run before sending
            'required': True
        },
        'customer_identification': {
            'description': 'Identify or create customer from message metadata',
            'trigger': 'Every incoming message',
            'inputs': ['email: str', 'phone: str', 'name: str'],
            'outputs': ['customer_id: str', 'is_new: bool', 'is_cross_channel: bool', 'history: dict'],
            'priority': 'critical',  # Run first for context
            'required': True
        }
    }

    # Skill execution order (pipeline)
    EXECUTION_PIPELINE = [
        'customer_identification',   # 1. Who is this?
        'sentiment_analysis',        # 2. How are they feeling?
        'knowledge_retrieval',       # 3. What do they need?
        'escalation_decision',       # 4. Do we need a human?
        'channel_adaptation',        # 5. Format for channel
    ]

    @classmethod
    def get_skill_info(cls, skill_name: str) -> dict:
        """Get metadata for a specific skill."""
        return cls.SKILLS.get(skill_name, {})

    @classmethod
    def get_pipeline(cls) -> list:
        """Get the ordered skill execution pipeline."""
        return cls.EXECUTION_PIPELINE

    @classmethod
    def get_all_skills(cls) -> dict:
        """Get all skill definitions."""
        return cls.SKILLS

    @classmethod
    def to_dict(cls) -> dict:
        """Export full manifest as dictionary."""
        return {
            'version': '1.0.0',
            'skills': cls.SKILLS,
            'execution_pipeline': cls.EXECUTION_PIPELINE,
            'total_skills': len(cls.SKILLS)
        }


# ─── Usage Example ──────────────────────────────────────────────────────────

def create_all_skills(knowledge_base, sentiment_analyzer, escalation_engine,
                      response_formatter, memory_manager):
    """Create all skill instances with their dependencies."""
    return {
        'knowledge_retrieval': KnowledgeRetrievalSkill(knowledge_base),
        'sentiment_analysis': SentimentAnalysisSkill(sentiment_analyzer),
        'escalation_decision': EscalationDecisionSkill(escalation_engine),
        'channel_adaptation': ChannelAdaptationSkill(response_formatter),
        'customer_identification': CustomerIdentificationSkill(memory_manager)
    }


if __name__ == "__main__":
    # Print skills manifest
    import json
    manifest = SkillsManifest.to_dict()
    print(json.dumps(manifest, indent=2))
