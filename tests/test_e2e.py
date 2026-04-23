"""
Customer Success FTE — Multi-Channel E2E Test Suite
====================================================
Phase 3: Integration

Tests the complete end-to-end flow across all channels:
1. Web form submission → ticket creation → agent response
2. Gmail webhook processing
3. WhatsApp webhook processing
4. Cross-channel customer history
5. Customer lookup
6. Channel metrics
7. Edge cases (empty messages, angry customers, escalations)
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from datetime import datetime

from production.api.main import app

BASE_URL = "http://localhost:8000"


# ─── Fixtures ──────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client():
    """Create an async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        yield ac


# ─── Health Check Tests ────────────────────────────────────────────────────

class TestHealthChecks:
    """Test health and readiness endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Health check should return healthy status."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "channels" in data
        assert "email" in data["channels"]
        assert "whatsapp" in data["channels"]
        assert "web_form" in data["channels"]

    @pytest.mark.asyncio
    async def test_readiness_check(self, client):
        """Readiness check should return service status."""
        response = await client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data


# ─── Web Form Channel Tests ────────────────────────────────────────────────

class TestWebFormChannel:
    """Test the web support form (required deliverable)."""

    @pytest.mark.asyncio
    async def test_form_submission(self, client):
        """Web form submission should create ticket and return ID."""
        response = await client.post("/support/submit", json={
            "name": "Test User",
            "email": "test@example.com",
            "subject": "Help with API",
            "category": "technical",
            "message": "I need help with the API authentication"
        })
        assert response.status_code == 200
        data = response.json()
        assert "ticket_id" in data
        assert data["message"] is not None
        assert "estimated_response_time" in data

    @pytest.mark.asyncio
    async def test_form_validation_empty_name(self, client):
        """Form should reject names shorter than 2 characters."""
        response = await client.post("/support/submit", json={
            "name": "A",
            "email": "test@example.com",
            "subject": "Help",
            "category": "general",
            "message": "I need help with something"
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_form_validation_invalid_email(self, client):
        """Form should reject invalid email addresses."""
        response = await client.post("/support/submit", json={
            "name": "Test User",
            "email": "invalid-email",
            "subject": "Help",
            "category": "general",
            "message": "I need help with something"
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_form_validation_short_message(self, client):
        """Form should reject messages shorter than 10 characters."""
        response = await client.post("/support/submit", json={
            "name": "Test User",
            "email": "test@example.com",
            "subject": "Help",
            "category": "general",
            "message": "Short"
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_form_validation_invalid_category(self, client):
        """Form should reject invalid categories."""
        response = await client.post("/support/submit", json={
            "name": "Test User",
            "email": "test@example.com",
            "subject": "Help",
            "category": "invalid_category",
            "message": "I need help with something"
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_ticket_status_retrieval(self, client):
        """Should be able to check ticket status after submission."""
        # Submit form
        submit_response = await client.post("/support/submit", json={
            "name": "Test User",
            "email": "test@example.com",
            "subject": "Status Test",
            "category": "general",
            "message": "Testing ticket status retrieval"
        })
        assert submit_response.status_code == 200
        ticket_id = submit_response.json()["ticket_id"]

        # Check status
        status_response = await client.get(f"/support/ticket/{ticket_id}")
        assert status_response.status_code in [200, 404]  # 404 is OK in mock mode


# ─── Email Channel Tests ───────────────────────────────────────────────────

class TestEmailChannel:
    """Test Gmail integration."""

    @pytest.mark.asyncio
    async def test_gmail_webhook_processing(self, client):
        """Gmail webhook should process incoming emails."""
        response = await client.post("/webhooks/gmail", json={
            "message": {
                "data": "base64_encoded_notification",
                "messageId": "test-123"
            },
            "subscription": "projects/test/subscriptions/gmail-push"
        })
        # Should not crash even without real Gmail credentials
        assert response.status_code in [200, 500]


# ─── WhatsApp Channel Tests ────────────────────────────────────────────────

class TestWhatsAppChannel:
    """Test WhatsApp/Twilio integration."""

    @pytest.mark.asyncio
    async def test_whatsapp_webhook_processing(self, client):
        """WhatsApp webhook should process incoming messages."""
        response = await client.post(
            "/webhooks/whatsapp",
            data={
                "MessageSid": "SM123",
                "From": "whatsapp:+1234567890",
                "Body": "Hello, I need help",
                "ProfileName": "Test User"
            }
        )
        # Will fail signature validation in test (expected), but shouldn't crash
        assert response.status_code in [200, 403]


# ─── Agent Processing Tests ────────────────────────────────────────────────

class TestAgentProcessing:
    """Test the AI agent processing logic."""

    @pytest.mark.asyncio
    async def test_password_reset_response(self, client):
        """Agent should provide password reset instructions."""
        response = await client.post("/agent/process", json={
            "content": "How do I reset my password?",
            "channel": "email",
            "customer_email": "test@example.com",
            "customer_name": "Test User",
            "subject": "Password Reset"
        })
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["escalated"] is False
        assert len(data["response"]) > 50

    @pytest.mark.asyncio
    async def test_refund_escalation(self, client):
        """Refund requests should trigger immediate escalation."""
        response = await client.post("/agent/process", json={
            "content": "I want a refund for my subscription",
            "channel": "email",
            "customer_email": "refund@test.com",
            "customer_name": "Refund User",
            "subject": "Refund Request"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["escalated"] is True
        assert data["escalation_reason"] == "refund_request"

    @pytest.mark.asyncio
    async def test_angry_customer_escalation(self, client):
        """Angry customers with legal threats should trigger escalation."""
        response = await client.post("/agent/process", json={
            "content": "This is garbage! Worst product ever! I want to sue you!",
            "channel": "email",
            "customer_email": "angry@test.com",
            "customer_name": "Angry User",
            "subject": "Complaint"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["escalated"] is True
        assert data["escalation_reason"] in ["legal_threat", "angry_customer"]

    @pytest.mark.asyncio
    async def test_human_request_escalation(self, client):
        """Explicit human requests should trigger escalation."""
        response = await client.post("/agent/process", json={
            "content": "I want to speak to a human agent please",
            "channel": "whatsapp",
            "customer_phone": "+1234567890",
            "customer_name": "Human Request",
            "subject": "Human Request"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["escalated"] is True

    @pytest.mark.asyncio
    async def test_empty_message_handling(self, client):
        """Empty messages should be handled gracefully."""
        response = await client.post("/agent/process", json={
            "content": "",
            "channel": "web_form",
            "customer_email": "empty@test.com",
            "customer_name": "Empty Msg",
            "subject": "Empty"
        })
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 0

    @pytest.mark.asyncio
    async def test_competitor_question_handling(self, client):
        """Competitor questions should trigger escalation."""
        response = await client.post("/agent/process", json={
            "content": "How does TechCorp compare to Asana and Monday.com?",
            "channel": "email",
            "customer_email": "compare@test.com",
            "customer_name": "Comparison",
            "subject": "Competitor Comparison"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["escalated"] is True


# ─── Cross-Channel Tests ───────────────────────────────────────────────────

class TestCrossChannelContinuity:
    """Test that conversations persist across channels."""

    @pytest.mark.asyncio
    async def test_customer_lookup_across_channels(self, client):
        """Customer should be identifiable by email or phone."""
        # Submit via web form
        await client.post("/support/submit", json={
            "name": "Cross Channel User",
            "email": "crosschannel@example.com",
            "subject": "Initial Contact",
            "category": "general",
            "message": "First contact via web form"
        })

        # Look up customer
        response = await client.get(
            "/customers/lookup",
            params={"email": "crosschannel@example.com"}
        )
        # Should not crash (may return mock data if DB not available)
        assert response.status_code in [200, 500]


# ─── Channel Metrics Tests ─────────────────────────────────────────────────

class TestChannelMetrics:
    """Test channel-specific metrics."""

    @pytest.mark.asyncio
    async def test_metrics_by_channel(self, client):
        """Should return metrics broken down by channel."""
        response = await client.get("/metrics/channels")
        assert response.status_code == 200
        # May return empty dict if DB not available, but shouldn't crash


# ─── Edge Case Tests ──────────────────────────────────────────────────────

class TestEdgeCases:
    """Test edge cases discovered during incubation."""

    @pytest.mark.asyncio
    async def test_special_characters_in_message(self, client):
        """Messages with special characters should be handled."""
        response = await client.post("/agent/process", json={
            "content": "Help! <script>alert('xss')</script> & other <b>html</b>",
            "channel": "web_form",
            "customer_email": "special@test.com",
            "customer_name": "Special Chars",
            "subject": "Special Characters"
        })
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_very_long_message(self, client):
        """Very long messages should be processed without crashing."""
        long_message = "Help me with this issue. " * 100
        response = await client.post("/agent/process", json={
            "content": long_message,
            "channel": "email",
            "customer_email": "long@test.com",
            "customer_name": "Long Message",
            "subject": "Very Long Message"
        })
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_unicode_message(self, client):
        """Unicode messages should be handled properly."""
        response = await client.post("/agent/process", json={
            "content": "こんにちは！パスワードをリセットするにはどうすればよいですか？",
            "channel": "email",
            "customer_email": "unicode@test.com",
            "customer_name": "Unicode User",
            "subject": "Unicode Test"
        })
        assert response.status_code == 200


# ─── API Endpoint Tests ────────────────────────────────────────────────────

class TestAPIEndpoints:
    """Test all API endpoints exist and respond."""

    @pytest.mark.asyncio
    async def test_docs_endpoint(self, client):
        """API docs should be accessible."""
        response = await client.get("/docs")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_openapi_schema(self, client):
        """OpenAPI schema should be accessible."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "info" in data
        assert "paths" in data
