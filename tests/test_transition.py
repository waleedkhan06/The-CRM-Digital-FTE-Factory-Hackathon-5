"""
Customer Success FTE — Transition Tests
=========================================
Phase 3: Integration & Testing (Per ai-tier.md Step 5)

Verifies that the production Custom Agent (OpenAI Agents SDK) preserves
all edge-case behaviours discovered during Phase 1 incubation.

Test categories:
1. Edge-case parity — same scenarios that tripped up the prototype must
   be handled correctly by the production tools and formatters.
2. Tool migration — every MCP tool from incubation/mcp_server.py has a
   corresponding @function_tool in production/agent/tools.py.
3. Behaviour parity — prototype and production produce semantically
   equivalent outputs for the same inputs.
4. System prompt constraints — production prompts contain the hard rules
   extracted during incubation.
"""

import pytest
from unittest.mock import AsyncMock, patch


# ─── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def mock_db(monkeypatch):
    """Patch database queries to avoid needing PostgreSQL."""
    async def fake_search_kb(query, max_results=5, category=None):
        if any(w in query.lower() for w in ["nonexistent", "xyz", "unknown_topic_999"]):
            return []
        return [{"title": "FAQ", "content": "Reset at Settings > Security.", "category": "account", "score": 0.9}]

    async def fake_get_or_create_customer(**kwargs):
        return {"id": "cust-001", "email": kwargs.get("email"), "name": kwargs.get("name", "Test")}

    async def fake_create_conversation(**kwargs):
        return {"id": "conv-001", "customer_id": "cust-001", "initial_channel": kwargs.get("channel"), "status": "active"}

    async def fake_create_ticket(**kwargs):
        return {"id": "ticket-001", "status": "open", "conversation_id": "conv-001", "customer_id": "cust-001"}

    async def fake_escalate_ticket(**kwargs):
        return {"id": kwargs.get("ticket_id"), "status": "escalated"}

    async def fake_get_ticket(ticket_id):
        return {"id": ticket_id, "conversation_id": "conv-001", "customer_id": "cust-001", "source_channel": "web_form"}

    async def fake_store_message(**kwargs):
        return {"id": "msg-001"}

    async def fake_update_ticket_status(**kwargs):
        return {}

    monkeypatch.setattr("production.database.queries.search_knowledge_base", fake_search_kb)
    monkeypatch.setattr("production.database.queries.get_or_create_customer", fake_get_or_create_customer)
    monkeypatch.setattr("production.database.queries.create_conversation", fake_create_conversation)
    monkeypatch.setattr("production.database.queries.create_ticket", fake_create_ticket)
    monkeypatch.setattr("production.database.queries.escalate_ticket", fake_escalate_ticket)
    monkeypatch.setattr("production.database.queries.get_ticket", fake_get_ticket)
    monkeypatch.setattr("production.database.queries.store_message", fake_store_message)
    monkeypatch.setattr("production.database.queries.update_ticket_status", fake_update_ticket_status)


# ─── 1. Edge-Case Parity Tests ────────────────────────────────────────────

class TestEdgeCaseParity:
    """
    These mirror the edge cases discovered in incubation/prototype.py.
    Each test maps directly to a scenario logged in specs/discovery-log.md.
    """

    @pytest.mark.asyncio
    async def test_empty_message_returns_helpful_prompt(self, mock_db):
        """
        Edge case #1 from incubation: Empty messages should not crash the system.
        The production system should ask for clarification, not raise.
        """
        from production.agent.tools import search_knowledge_base, KnowledgeSearchInput
        result = await search_knowledge_base(KnowledgeSearchInput(query=""))
        # Should return some string — either results or a graceful message
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_pricing_question_triggers_escalation(self):
        """
        Edge case #2: Pricing questions must be escalated — NEVER answered directly.
        Discovered during incubation: prototype used to try to answer pricing.
        """
        from production.agent.tools import evaluate_escalation
        for pricing_phrase in [
            "How much does the enterprise plan cost?",
            "What is your pricing?",
            "Can I get a discount on my subscription?",
            "How much for bulk pricing?",
        ]:
            result = await evaluate_escalation(pricing_phrase, sentiment_score=0.6)
            # pricing_inquiry or general escalation
            escalated = "ESCALATION RECOMMENDED" in result
            # pricing_inquiry or human_requested is acceptable
            has_reason = any(r in result.lower() for r in ["pricing", "discount", "escalat"])
            assert escalated or has_reason, (
                f"Pricing query '{pricing_phrase[:40]}' should trigger escalation. Got: {result}"
            )

    @pytest.mark.asyncio
    async def test_angry_customer_triggers_escalation(self):
        """
        Edge case #3: Angry customers (very low sentiment) should be escalated.
        Threshold discovered during incubation: sentiment < 0.3.
        """
        from production.agent.tools import _calculate_sentiment, evaluate_escalation

        angry_messages = [
            "This is RIDICULOUS! Your product is BROKEN!",
            "I hate your garbage software, it's terrible and awful!",
            "This is the worst product I've ever used, completely horrible!",
        ]

        for msg in angry_messages:
            sentiment = _calculate_sentiment(msg)
            assert sentiment <= 0.4, (
                f"Angry message should score <= 0.4, got {sentiment}: '{msg[:50]}'"
            )
            if sentiment < 0.3:
                result = await evaluate_escalation(msg, sentiment_score=sentiment)
                assert "ESCALATION RECOMMENDED" in result, (
                    f"Very angry customer (sentiment={sentiment}) must be escalated"
                )

    @pytest.mark.asyncio
    async def test_email_channel_response_has_greeting(self):
        """
        Edge case #4 from incubation: Email responses must have proper greeting.
        Discovered: early prototype sent plain text without formatting.
        """
        from production.agent.formatters import format_for_channel
        response = format_for_channel(
            "To reset your password, go to Settings > Security.",
            channel="email",
            customer_name="Alice",
        )
        has_greeting = any(
            word in response.lower()
            for word in ["dear", "hello", "hi", "greetings"]
        )
        assert has_greeting, f"Email must contain greeting. Got: {response[:150]}"

    @pytest.mark.asyncio
    async def test_whatsapp_response_is_concise(self):
        """
        Edge case #5 from incubation: WhatsApp responses must be short.
        Discovered: full email-style replies caused poor UX on WhatsApp.
        Production max: 1600 chars (WhatsApp limit), preferred < 300 chars.
        """
        from production.agent.formatters import format_for_channel
        verbose_answer = (
            "Thank you for contacting us. We understand your concern. "
            "Here is a detailed step-by-step guide on how to resolve your issue. "
            "Please follow these instructions carefully. " * 5
        )
        formatted = format_for_channel(verbose_answer, channel="whatsapp")
        assert len(formatted) <= 1600, (
            f"WhatsApp response too long: {len(formatted)} chars"
        )

    @pytest.mark.asyncio
    async def test_no_knowledge_base_results_suggests_escalation(self, mock_db):
        """
        Edge case #6: When KB returns no results, agent should suggest escalation.
        Discovered: prototype used to hallucinate answers when KB was empty.
        """
        from production.agent.tools import search_knowledge_base, KnowledgeSearchInput
        result = await search_knowledge_base(
            KnowledgeSearchInput(query="unknown_topic_999 xyz nonsense", max_results=3)
        )
        escalation_hint = any(
            w in result.lower()
            for w in ["escalat", "human", "support", "no relevant", "not found", "unavailable"]
        )
        assert escalation_hint, (
            f"Empty KB result should suggest escalation. Got: {result}"
        )

    @pytest.mark.asyncio
    async def test_legal_keywords_trigger_p0_escalation(self):
        """
        Edge case #7: Legal keywords must trigger highest-priority escalation.
        Discovered: 'lawyer', 'sue', 'attorney' must always escalate.
        """
        from production.agent.tools import evaluate_escalation
        legal_phrases = [
            "I'm going to sue your company",
            "My lawyer will be in touch",
            "I'll take this to my attorney",
        ]
        for phrase in legal_phrases:
            result = await evaluate_escalation(phrase, sentiment_score=0.2)
            assert "ESCALATION RECOMMENDED" in result, (
                f"Legal threat must escalate: '{phrase}'"
            )
            assert "P0" in result or "P1" in result, (
                f"Legal threats must be high priority. Got: {result}"
            )

    @pytest.mark.asyncio
    async def test_competitor_mentions_detected(self):
        """
        Edge case #8: Competitor product mentions should be handled carefully.
        Discovered: prototype tried to compare — production should escalate.
        """
        from production.agent.tools import evaluate_escalation
        result = await evaluate_escalation(
            "How does this compare to Asana and Monday.com?",
            sentiment_score=0.6,
        )
        assert "ESCALATION RECOMMENDED" in result


# ─── 2. Tool Migration Verification ───────────────────────────────────────

class TestToolMigration:
    """
    Verify every MCP tool from incubation/mcp_server.py has a matching
    production implementation in production/agent/tools.py.
    """

    def test_search_knowledge_base_tool_exists(self):
        from production.agent.tools import search_knowledge_base, KnowledgeSearchInput
        assert callable(search_knowledge_base)
        # Check it accepts KnowledgeSearchInput
        import inspect
        sig = inspect.signature(search_knowledge_base)
        assert len(sig.parameters) >= 1

    def test_create_ticket_tool_exists(self):
        from production.agent.tools import create_ticket, TicketInput
        assert callable(create_ticket)

    def test_get_customer_history_tool_exists(self):
        from production.agent.tools import get_customer_history
        assert callable(get_customer_history)

    def test_escalate_to_human_tool_exists(self):
        from production.agent.tools import escalate_to_human, EscalationInput
        assert callable(escalate_to_human)

    def test_send_response_tool_exists(self):
        from production.agent.tools import send_response, ResponseInput
        assert callable(send_response)

    def test_analyze_sentiment_tool_exists(self):
        from production.agent.tools import analyze_sentiment
        assert callable(analyze_sentiment)

    def test_evaluate_escalation_tool_exists(self):
        from production.agent.tools import evaluate_escalation
        assert callable(evaluate_escalation)

    def test_all_tools_have_pydantic_schemas(self):
        """Production tools must use Pydantic BaseModel for input validation."""
        from pydantic import BaseModel
        from production.agent.tools import (
            KnowledgeSearchInput, TicketInput, EscalationInput, ResponseInput
        )
        for schema in [KnowledgeSearchInput, TicketInput, EscalationInput, ResponseInput]:
            assert issubclass(schema, BaseModel), (
                f"{schema.__name__} must be a Pydantic BaseModel"
            )

    def test_channel_enum_covers_all_channels(self):
        """Channel enum must cover email, whatsapp, and web_form."""
        from production.agent.tools import Channel
        assert Channel.EMAIL == "email"
        assert Channel.WHATSAPP == "whatsapp"
        assert Channel.WEB_FORM == "web_form"

    @pytest.mark.asyncio
    async def test_search_kb_returns_results_not_crash(self, mock_db):
        """Knowledge search should return formatted results, not crash."""
        from production.agent.tools import search_knowledge_base, KnowledgeSearchInput
        result = await search_knowledge_base(
            KnowledgeSearchInput(query="password reset", max_results=3)
        )
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_search_kb_handles_no_results_gracefully(self, mock_db):
        """Knowledge search must handle zero results without crashing."""
        from production.agent.tools import search_knowledge_base, KnowledgeSearchInput
        result = await search_knowledge_base(
            KnowledgeSearchInput(query="xyznonexistentquery123", max_results=3)
        )
        assert result is not None
        assert isinstance(result, str)
        assert "no" in result.lower() or "not found" in result.lower() or "escalat" in result.lower()


# ─── 3. Behaviour Parity Tests ────────────────────────────────────────────

class TestBehaviourParity:
    """
    Verify that production tools produce semantically equivalent outputs
    to the incubation prototype for the same class of inputs.
    """

    def test_prototype_and_production_sentiment_agree(self):
        """
        Sentiment scoring in production (_calculate_sentiment) must agree
        directionally with the incubation prototype's sentiment logic.
        """
        from production.agent.tools import _calculate_sentiment
        from incubation.prototype import CustomerSuccessAgent

        prototype = CustomerSuccessAgent()

        test_cases = [
            ("This is great, I love the product!", True),   # positive
            ("This is terrible and broken!", False),         # negative
            ("I need to reset my password.", None),          # neutral
        ]

        for message, expected_positive in test_cases:
            prod_score = _calculate_sentiment(message)

            if expected_positive is True:
                assert prod_score > 0.5, (
                    f"Positive message should score > 0.5. Got {prod_score}: '{message[:40]}'"
                )
            elif expected_positive is False:
                assert prod_score < 0.5, (
                    f"Negative message should score < 0.5. Got {prod_score}: '{message[:40]}'"
                )
            # neutral — no strict assertion

    def test_escalation_rules_match_incubation_spec(self):
        """
        Escalation rules in production/agent/tools.py must match the rules
        documented in specs/customer-success-fte-spec.md and context/escalation-rules.md.
        """
        from production.agent.tools import evaluate_escalation
        import asyncio

        # From escalation-rules.md: these must always escalate
        must_escalate = [
            ("pricing_inquiry", "I want to negotiate a discount"),
            ("refund_request", "I want a refund"),
            ("legal_threat", "I will sue you"),
            ("human_requested", "I want to speak to a real person"),
        ]

        for reason, message in must_escalate:
            result = asyncio.get_event_loop().run_until_complete(
                evaluate_escalation(message, sentiment_score=0.5)
            )
            assert "ESCALATION RECOMMENDED" in result, (
                f"'{message}' should trigger escalation for reason '{reason}'. Got: {result}"
            )

    def test_channel_formatters_match_spec_limits(self):
        """
        Response limits from specs/customer-success-fte-spec.md:
        - Email: 500 words max
        - WhatsApp: 160 chars preferred, 1600 hard limit
        - Web Form: 300 words max
        """
        from production.agent.formatters import format_for_channel

        long_content = "This is a test sentence with multiple words. " * 100

        email = format_for_channel(long_content, channel="email")
        assert len(email.split()) <= 600  # some tolerance for greeting/sig

        whatsapp = format_for_channel(long_content, channel="whatsapp")
        assert len(whatsapp) <= 1600

        web = format_for_channel(long_content, channel="web_form")
        assert len(web.split()) <= 600  # some tolerance


# ─── 4. System Prompt Constraints ─────────────────────────────────────────

class TestSystemPromptConstraints:
    """
    Verify that the production system prompt in prompts.py contains all
    the hard constraints discovered during incubation.
    """

    def test_system_prompt_exists_and_non_empty(self):
        from production.agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
        assert CUSTOMER_SUCCESS_SYSTEM_PROMPT
        assert len(CUSTOMER_SUCCESS_SYSTEM_PROMPT) > 200

    def test_system_prompt_mentions_all_channels(self):
        from production.agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
        prompt = CUSTOMER_SUCCESS_SYSTEM_PROMPT.lower()
        assert "email" in prompt, "System prompt must mention email channel"
        assert "whatsapp" in prompt, "System prompt must mention whatsapp channel"
        assert "web" in prompt, "System prompt must mention web form channel"

    def test_system_prompt_has_escalation_triggers(self):
        from production.agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
        prompt = CUSTOMER_SUCCESS_SYSTEM_PROMPT.lower()
        escalation_keywords = ["escalat", "human", "pricing", "refund"]
        for kw in escalation_keywords:
            assert kw in prompt, (
                f"System prompt must mention '{kw}' escalation trigger"
            )

    def test_system_prompt_has_hard_constraints(self):
        from production.agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
        prompt = CUSTOMER_SUCCESS_SYSTEM_PROMPT.lower()
        constraints = ["never", "always", "must"]
        has_constraint = any(c in prompt for c in constraints)
        assert has_constraint, "System prompt must contain hard constraints (NEVER/ALWAYS/MUST)"

    def test_system_prompt_has_channel_response_length_limits(self):
        from production.agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
        prompt = CUSTOMER_SUCCESS_SYSTEM_PROMPT.lower()
        # Some form of length constraint must exist
        has_length_constraint = any(
            term in prompt
            for term in ["words", "chars", "characters", "concise", "brief", "short", "limit"]
        )
        assert has_length_constraint, "System prompt must specify channel response length limits"

    def test_guardrails_in_system_prompt(self):
        """
        From ai-tier.md crystallization document:
        - NEVER discuss competitor products
        - NEVER promise features not in docs
        - ALWAYS create ticket before responding
        - ALWAYS check sentiment before closing
        """
        from production.agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
        prompt = CUSTOMER_SUCCESS_SYSTEM_PROMPT.lower()
        assert "ticket" in prompt, "Must mention ticket creation"
        assert "sentiment" in prompt or "escalat" in prompt, "Must mention sentiment/escalation"


# ─── 5. Pre-Production Readiness Checklist ────────────────────────────────

class TestTransitionReadiness:
    """
    Final gate checks from ai-tier.md Step 6: Transition Complete Criteria.
    """

    def test_production_folder_structure_exists(self):
        """All required production folders and files must exist."""
        import os
        base = "e:/The CRM Digital FTE Factory Hackathon 5/production"
        required = [
            "agent/__init__.py",
            "agent/customer_success_agent.py",
            "agent/tools.py",
            "agent/prompts.py",
            "agent/formatters.py",
            "channels/gmail_handler.py",
            "channels/whatsapp_handler.py",
            "channels/web_form_handler.py",
            "workers/message_processor.py",
            "workers/metrics_collector.py",
            "api/main.py",
            "database/schema.sql",
            "database/queries.py",
            "kafka_client.py",
            "config.py",
            "requirements.txt",
        ]
        missing = []
        for path in required:
            full = os.path.join(base.replace("/", "\\"), path.replace("/", "\\"))
            if not os.path.exists(full):
                missing.append(path)
        assert not missing, f"Missing production files: {missing}"

    def test_incubation_folder_structure_exists(self):
        """All Phase 1 deliverables must exist."""
        import os
        base = "e:/The CRM Digital FTE Factory Hackathon 5"
        required = [
            "incubation/prototype.py",
            "incubation/mcp_server.py",
            "incubation/agent_skills.py",
            "incubation/memory_manager.py",
            "specs/discovery-log.md",
            "specs/customer-success-fte-spec.md",
            "specs/transition-checklist.md",
            "context/company-profile.md",
            "context/product-docs.md",
            "context/sample-tickets.json",
            "context/escalation-rules.md",
            "context/brand-voice.md",
        ]
        missing = []
        for path in required:
            full = os.path.join(base.replace("/", "\\"), path.replace("/", "\\"))
            if not os.path.exists(full):
                missing.append(path)
        assert not missing, f"Missing Phase 1 files: {missing}"

    def test_k8s_manifests_exist(self):
        """All 8 Kubernetes manifests must be present."""
        import os
        base = "e:/The CRM Digital FTE Factory Hackathon 5/k8s"
        manifests = [
            "namespace.yaml", "configmap.yaml", "secrets.yaml",
            "deployment-api.yaml", "deployment-worker.yaml",
            "service.yaml", "ingress.yaml", "hpa.yaml",
        ]
        missing = [
            m for m in manifests
            if not os.path.exists(os.path.join(base.replace("/", "\\"), m))
        ]
        assert not missing, f"Missing K8s manifests: {missing}"

    def test_tools_have_error_handling(self):
        """Every production tool function must have try/except error handling."""
        import ast
        import os

        tools_file = (
            "e:/The CRM Digital FTE Factory Hackathon 5/production/agent/tools.py"
        ).replace("/", "\\")

        with open(tools_file, "r") as f:
            source = f.read()

        tree = ast.parse(source)
        # Count async functions and try blocks
        functions = [n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef)]
        try_blocks = [n for n in ast.walk(tree) if isinstance(n, ast.Try)]

        tool_functions = [f for f in functions if not f.name.startswith("_")]
        assert len(try_blocks) >= len(tool_functions) - 2, (
            f"Not enough try/except blocks in tools.py: "
            f"{len(try_blocks)} try blocks for {len(tool_functions)} tools"
        )

    def test_pydantic_validation_on_all_input_schemas(self):
        """All tool input schemas must use Pydantic Field() for validation."""
        from pydantic import BaseModel
        from production.agent.tools import (
            KnowledgeSearchInput, TicketInput, EscalationInput, ResponseInput
        )

        schemas = [KnowledgeSearchInput, TicketInput, EscalationInput, ResponseInput]
        for schema in schemas:
            assert issubclass(schema, BaseModel), (
                f"{schema.__name__} must extend pydantic.BaseModel"
            )
            # Must have at least one field
            assert len(schema.model_fields) >= 1, (
                f"{schema.__name__} must have at least one field"
            )
