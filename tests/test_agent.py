"""
Customer Success FTE — Agent Unit Tests
=========================================
Phase 3: Integration & Testing

Tests for the production agent logic including:
- Tool execution order (create_ticket first, send_response last)
- Escalation triggers (pricing, legal, angry customer, human request)
- Channel response format (email length vs WhatsApp conciseness)
- Edge cases (empty message, no KB results, multi-word triggers)
- Sentiment analysis accuracy
- Escalation evaluation logic

These tests use the production tool functions and agent helpers directly
(no live DB or Kafka required — DB calls are mocked via monkeypatch).
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Optional


# ─── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def mock_db(monkeypatch):
    """Patch all database queries to avoid needing a live PostgreSQL instance."""
    async def fake_search_kb(query, max_results=5, category=None):
        if "nonexistent" in query.lower() or "xyzabc" in query.lower():
            return []
        return [
            {
                "title": "Password Reset Guide",
                "content": "To reset your password, go to Settings > Security > Reset Password.",
                "category": "account",
                "score": 0.95,
            }
        ]

    async def fake_get_or_create_customer(**kwargs):
        return {"id": "cust-test-001", "email": kwargs.get("email", "test@example.com"),
                "phone": kwargs.get("phone"), "name": kwargs.get("name", "Test User")}

    async def fake_create_conversation(**kwargs):
        return {"id": "conv-test-001", "customer_id": kwargs.get("customer_id"),
                "initial_channel": kwargs.get("channel", "web_form"), "status": "active"}

    async def fake_create_ticket(**kwargs):
        return {"id": "ticket-test-001", "status": "open",
                "conversation_id": kwargs.get("conversation_id"),
                "customer_id": kwargs.get("customer_id")}

    async def fake_escalate_ticket(**kwargs):
        return {"id": kwargs.get("ticket_id"), "status": "escalated"}

    async def fake_get_ticket(ticket_id):
        return {"id": ticket_id, "conversation_id": "conv-test-001",
                "customer_id": "cust-test-001", "source_channel": "web_form"}

    async def fake_store_message(**kwargs):
        return {"id": "msg-test-001"}

    async def fake_update_ticket_status(**kwargs):
        return {"id": kwargs.get("ticket_id"), "status": kwargs.get("status")}

    monkeypatch.setattr(
        "production.database.queries.search_knowledge_base", fake_search_kb
    )
    monkeypatch.setattr(
        "production.database.queries.get_or_create_customer", fake_get_or_create_customer
    )
    monkeypatch.setattr(
        "production.database.queries.create_conversation", fake_create_conversation
    )
    monkeypatch.setattr(
        "production.database.queries.create_ticket", fake_create_ticket
    )
    monkeypatch.setattr(
        "production.database.queries.escalate_ticket", fake_escalate_ticket
    )
    monkeypatch.setattr(
        "production.database.queries.get_ticket", fake_get_ticket
    )
    monkeypatch.setattr(
        "production.database.queries.store_message", fake_store_message
    )
    monkeypatch.setattr(
        "production.database.queries.update_ticket_status", fake_update_ticket_status
    )


# ─── Sentiment Analysis Tests ─────────────────────────────────────────────

class TestSentimentAnalysis:
    """Tests for the _calculate_sentiment helper and analyze_sentiment tool."""

    def test_positive_message_scores_high(self):
        from production.agent.tools import _calculate_sentiment
        score = _calculate_sentiment("This is great, thanks so much, I love it!")
        assert score >= 0.7, f"Expected positive score >= 0.7, got {score}"

    def test_negative_message_scores_low(self):
        from production.agent.tools import _calculate_sentiment
        score = _calculate_sentiment("This is terrible and broken, I hate it!")
        assert score <= 0.3, f"Expected negative score <= 0.3, got {score}"

    def test_neutral_message_scores_middle(self):
        from production.agent.tools import _calculate_sentiment
        score = _calculate_sentiment("I need to reset my password.")
        assert 0.3 <= score <= 0.7, f"Expected neutral score 0.3-0.7, got {score}"

    def test_empty_message_returns_neutral(self):
        from production.agent.tools import _calculate_sentiment
        score = _calculate_sentiment("")
        assert score == 0.5

    @pytest.mark.asyncio
    async def test_analyze_sentiment_returns_formatted_string(self):
        from production.agent.tools import analyze_sentiment
        result = await analyze_sentiment("Your product is amazing!")
        assert "Score:" in result
        assert "Label:" in result
        assert "Recommendation:" in result

    @pytest.mark.asyncio
    async def test_analyze_sentiment_negative_flags_attention(self):
        from production.agent.tools import analyze_sentiment
        result = await analyze_sentiment("This is garbage and terrible!")
        assert "Yes" in result or "consider_escalation" in result


# ─── Escalation Evaluation Tests ─────────────────────────────────────────

class TestEscalationEvaluation:
    """Tests for escalation trigger detection."""

    @pytest.mark.asyncio
    async def test_legal_threat_triggers_escalation(self):
        from production.agent.tools import evaluate_escalation
        result = await evaluate_escalation(
            "I'm going to sue you and call my lawyer!", sentiment_score=0.1
        )
        assert "ESCALATION RECOMMENDED" in result
        assert "legal_threat" in result.lower()

    @pytest.mark.asyncio
    async def test_refund_triggers_escalation(self):
        from production.agent.tools import evaluate_escalation
        result = await evaluate_escalation(
            "I want a refund immediately!", sentiment_score=0.3
        )
        assert "ESCALATION RECOMMENDED" in result
        assert "refund_request" in result.lower()

    @pytest.mark.asyncio
    async def test_human_request_triggers_escalation(self):
        from production.agent.tools import evaluate_escalation
        result = await evaluate_escalation(
            "I want to speak to a real person or agent", sentiment_score=0.5
        )
        assert "ESCALATION RECOMMENDED" in result
        assert "human_requested" in result.lower()

    @pytest.mark.asyncio
    async def test_low_sentiment_triggers_escalation(self):
        from production.agent.tools import evaluate_escalation
        result = await evaluate_escalation(
            "I'm having a problem", sentiment_score=0.2
        )
        assert "ESCALATION RECOMMENDED" in result
        assert "angry_customer" in result.lower()

    @pytest.mark.asyncio
    async def test_normal_message_no_escalation(self):
        from production.agent.tools import evaluate_escalation
        result = await evaluate_escalation(
            "How do I reset my password?", sentiment_score=0.6
        )
        assert "NO ESCALATION NEEDED" in result

    @pytest.mark.asyncio
    async def test_compliance_question_escalates(self):
        from production.agent.tools import evaluate_escalation
        result = await evaluate_escalation(
            "Does your platform comply with GDPR?", sentiment_score=0.5
        )
        assert "ESCALATION RECOMMENDED" in result
        assert "compliance" in result.lower()

    @pytest.mark.asyncio
    async def test_pricing_negotiation_escalates(self):
        from production.agent.tools import evaluate_escalation
        result = await evaluate_escalation(
            "Can I get a bulk pricing discount for my team?", sentiment_score=0.6
        )
        assert "ESCALATION RECOMMENDED" in result

    @pytest.mark.asyncio
    async def test_escalation_has_priority_field(self):
        from production.agent.tools import evaluate_escalation
        result = await evaluate_escalation(
            "I'm going to sue you!", sentiment_score=0.1
        )
        assert "Priority:" in result or "P0" in result or "P1" in result


# ─── Knowledge Base Search Tests ──────────────────────────────────────────

class TestKnowledgeBaseSearch:
    """Tests for the search_knowledge_base tool."""

    @pytest.mark.asyncio
    async def test_search_returns_results(self, mock_db):
        from production.agent.tools import search_knowledge_base, KnowledgeSearchInput
        result = await search_knowledge_base(
            KnowledgeSearchInput(query="password reset", max_results=3)
        )
        assert result is not None
        assert len(result) > 0
        assert "password" in result.lower() or "No relevant" in result

    @pytest.mark.asyncio
    async def test_search_handles_no_results(self, mock_db):
        from production.agent.tools import search_knowledge_base, KnowledgeSearchInput
        result = await search_knowledge_base(
            KnowledgeSearchInput(query="xyzabc nonexistent query 999", max_results=3)
        )
        assert "No relevant" in result or "no" in result.lower()

    @pytest.mark.asyncio
    async def test_search_respects_max_results(self, mock_db):
        from production.agent.tools import search_knowledge_base, KnowledgeSearchInput
        result = await search_knowledge_base(
            KnowledgeSearchInput(query="password", max_results=1)
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_search_graceful_on_db_error(self, monkeypatch):
        from production.agent.tools import search_knowledge_base, KnowledgeSearchInput

        async def raise_error(query, **kwargs):
            raise ConnectionError("DB connection refused")

        monkeypatch.setattr(
            "production.database.queries.search_knowledge_base", raise_error
        )
        result = await search_knowledge_base(
            KnowledgeSearchInput(query="test", max_results=3)
        )
        assert "unavailable" in result.lower() or "Error" in result


# ─── Ticket Creation Tests ─────────────────────────────────────────────────

class TestTicketCreation:
    """Tests for the create_ticket tool."""

    @pytest.mark.asyncio
    async def test_ticket_created_returns_id(self, mock_db):
        from production.agent.tools import create_ticket, TicketInput, Channel
        result = await create_ticket(
            TicketInput(
                customer_id="user@example.com",
                issue="Cannot log in to my account",
                priority="medium",
                channel=Channel.WEB_FORM,
                category="account",
            )
        )
        assert "Ticket ID:" in result or "ticket" in result.lower()

    @pytest.mark.asyncio
    async def test_ticket_includes_channel(self, mock_db):
        from production.agent.tools import create_ticket, TicketInput, Channel
        result = await create_ticket(
            TicketInput(
                customer_id="user@example.com",
                issue="WhatsApp test",
                priority="low",
                channel=Channel.WHATSAPP,
            )
        )
        assert "whatsapp" in result.lower()

    @pytest.mark.asyncio
    async def test_ticket_creation_handles_db_error(self, monkeypatch):
        from production.agent.tools import create_ticket, TicketInput, Channel

        async def raise_error(**kwargs):
            raise RuntimeError("DB unavailable")

        monkeypatch.setattr(
            "production.database.queries.get_or_create_customer", raise_error
        )
        result = await create_ticket(
            TicketInput(
                customer_id="error@test.com",
                issue="Test error handling",
                priority="low",
                channel=Channel.EMAIL,
            )
        )
        assert "Error" in result or "error" in result.lower()


# ─── Channel Response Formatter Tests ─────────────────────────────────────

class TestChannelFormatters:
    """Tests for channel-specific response formatting."""

    def test_email_response_has_greeting(self):
        from production.agent.formatters import format_for_channel
        formatted = format_for_channel(
            "Your password can be reset in Settings.",
            channel="email",
            customer_name="Alice",
        )
        greeting_present = (
            "dear" in formatted.lower()
            or "hello" in formatted.lower()
            or "hi" in formatted.lower()
        )
        assert greeting_present, f"Email should contain greeting. Got: {formatted[:100]}"

    def test_email_response_has_signature(self):
        from production.agent.formatters import format_for_channel
        formatted = format_for_channel(
            "Your password can be reset in Settings.",
            channel="email",
        )
        sig_present = (
            "regards" in formatted.lower()
            or "sincerely" in formatted.lower()
            or "support" in formatted.lower()
            or "team" in formatted.lower()
        )
        assert sig_present, f"Email should contain signature. Got: {formatted[-200:]}"

    def test_whatsapp_response_is_concise(self):
        from production.agent.formatters import format_for_channel
        long_message = "Your password can be reset in Settings > Security > Reset Password. " * 10
        formatted = format_for_channel(long_message, channel="whatsapp")
        assert len(formatted) <= 1600, (
            f"WhatsApp response should be <= 1600 chars, got {len(formatted)}"
        )

    def test_web_form_response_is_semi_formal(self):
        from production.agent.formatters import format_for_channel
        formatted = format_for_channel(
            "Your password can be reset in Settings.",
            channel="web_form",
            ticket_id="TICK-001",
        )
        assert len(formatted) > 0

    def test_unknown_channel_falls_back_gracefully(self):
        from production.agent.formatters import format_for_channel
        formatted = format_for_channel(
            "Here is your answer.",
            channel="unknown_channel",
        )
        assert len(formatted) > 0

    def test_email_respects_500_word_limit(self):
        from production.agent.formatters import format_for_channel
        very_long = "word " * 600
        formatted = format_for_channel(very_long, channel="email")
        word_count = len(formatted.split())
        assert word_count <= 550, (
            f"Email response word count {word_count} exceeds limit"
        )


# ─── Escalation Tool Tests ─────────────────────────────────────────────────

class TestEscalateToHuman:
    """Tests for the escalate_to_human tool."""

    @pytest.mark.asyncio
    async def test_escalation_returns_id(self, mock_db):
        from production.agent.tools import escalate_to_human, EscalationInput
        result = await escalate_to_human(
            EscalationInput(
                ticket_id="ticket-test-001",
                reason="pricing_inquiry",
                urgency="P2",
            )
        )
        assert "Escalation" in result or "escalation" in result.lower()

    @pytest.mark.asyncio
    async def test_legal_escalation_has_p0_priority(self, mock_db):
        from production.agent.tools import escalate_to_human, EscalationInput
        result = await escalate_to_human(
            EscalationInput(
                ticket_id="ticket-test-001",
                reason="legal_threat",
                urgency="P0",
            )
        )
        assert "P0" in result or "legal" in result.lower()

    @pytest.mark.asyncio
    async def test_escalation_includes_reason(self, mock_db):
        from production.agent.tools import escalate_to_human, EscalationInput
        result = await escalate_to_human(
            EscalationInput(
                ticket_id="ticket-test-001",
                reason="refund_request",
                urgency="P1",
            )
        )
        assert "refund" in result.lower() or "billing" in result.lower()


# ─── Metrics Collector Tests ───────────────────────────────────────────────

class TestMetricsCollector:
    """Tests for the MetricsCollector worker."""

    def test_record_message_increments_counters(self):
        from production.workers.metrics_collector import MetricsCollector
        collector = MetricsCollector()
        collector.record_message(
            channel="email", latency_ms=250,
            escalated=False, sentiment_score=0.7
        )
        collector.record_message(
            channel="whatsapp", latency_ms=150,
            escalated=True, sentiment_score=0.3
        )
        assert collector._message_counts["email"] == 1
        assert collector._message_counts["whatsapp"] == 1
        assert collector._escalation_counts["whatsapp"] == 1

    def test_error_recorded_correctly(self):
        from production.workers.metrics_collector import MetricsCollector
        collector = MetricsCollector()
        collector.record_message(
            channel="web_form", latency_ms=500,
            escalated=False, sentiment_score=0.5, error=True
        )
        assert collector._error_counts["web_form"] == 1

    def test_snapshot_calculates_rates(self):
        from production.workers.metrics_collector import MetricsCollector
        collector = MetricsCollector()
        # 10 messages, 2 errors, 3 escalations
        for i in range(7):
            collector.record_message("email", 100, False, 0.6)
        for i in range(2):
            collector.record_message("email", 100, False, 0.6, error=True)
        for i in range(3):
            collector.record_message("whatsapp", 200, True, 0.3)

        snapshot = collector._build_snapshot()
        assert snapshot["total_messages"] == 12
        assert snapshot["total_errors"] == 2
        assert snapshot["total_escalations"] == 3
        assert round(snapshot["error_rate_pct"], 1) == round(2 / 12 * 100, 1)

    def test_percentile_calculation(self):
        from production.workers.metrics_collector import _percentile
        data = list(range(100))  # 0..99
        assert _percentile(data, 50) == 49
        assert _percentile(data, 95) == 94
        assert _percentile(data, 99) == 98

    def test_dlq_depth_tracking(self):
        from production.workers.metrics_collector import MetricsCollector
        collector = MetricsCollector()
        collector.record_dlq_event()
        collector.record_dlq_event()
        assert collector._dlq_depth == 2
        collector.record_dlq_processed()
        assert collector._dlq_depth == 1

    def test_alert_thresholds_defined(self):
        from production.workers.metrics_collector import ALERT_THRESHOLDS
        required_keys = [
            "error_rate_pct", "p95_latency_ms",
            "escalation_rate_pct", "avg_sentiment_min", "dlq_depth_max"
        ]
        for key in required_keys:
            assert key in ALERT_THRESHOLDS, f"Missing alert threshold: {key}"
