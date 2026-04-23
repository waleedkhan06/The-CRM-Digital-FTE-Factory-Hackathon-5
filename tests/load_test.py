"""
Customer Success FTE — Load Test Suite
========================================
Phase 3: Integration

Locust-based load tests simulating real-world traffic patterns:
- Web form submissions (most common)
- Health checks (monitoring)
- Ticket status checks
- Agent processing

Usage:
    locust -f tests/load_test.py --host=http://localhost:8000

Or headless:
    locust -f tests/load_test.py --host=http://localhost:8000 \
      --headless -u 100 -r 10 --run-time 5m
"""

from locust import HttpUser, task, between
import random
import json


# ─── Sample Test Data ──────────────────────────────────────────────────────

SAMPLE_MESSAGES = [
    "How do I reset my password?",
    "I need help setting up workflow automation",
    "How do I invite team members to my workspace?",
    "What are the API rate limits for the Professional plan?",
    "How do I create a custom dashboard?",
    "Can you help me with task dependencies?",
    "How do I export my project data?",
    "The mobile app isn't syncing properly",
    "How do I enable two-factor authentication?",
    "I need help with the Slack integration",
]

CATEGORIES = ["general", "technical", "billing", "feedback", "bug_report"]
PRIORITIES = ["low", "medium", "high"]


class WebFormUser(HttpUser):
    """Simulates users submitting the web support form.
    
    This is the most common user pattern (weight=3).
    """
    wait_time = between(2, 10)
    weight = 3

    @task
    def submit_support_form(self):
        """Submit a support form with random data."""
        self.client.post("/support/submit", json={
            "name": f"Load Test User {random.randint(1, 10000)}",
            "email": f"loadtest{random.randint(1, 10000)}@example.com",
            "subject": f"Load Test Query {random.randint(1, 100)}",
            "category": random.choice(CATEGORIES),
            "message": random.choice(SAMPLE_MESSAGES),
            "priority": random.choice(PRIORITIES)
        })

    @task(2)
    def check_ticket_status(self):
        """Check status of a previously submitted ticket."""
        ticket_id = f"test-{random.randint(1, 1000):04d}"
        self.client.get(f"/support/ticket/{ticket_id}")


class APIUser(HttpUser):
    """Simulates API consumers using the agent directly.
    
    These are programmatic users (integrations, bots).
    """
    wait_time = between(1, 5)
    weight = 2

    @task
    def process_customer_message(self):
        """Submit a message for agent processing."""
        self.client.post("/agent/process", json={
            "content": random.choice(SAMPLE_MESSAGES),
            "channel": random.choice(["email", "whatsapp", "web_form"]),
            "customer_email": f"api{random.randint(1, 1000)}@example.com",
            "customer_name": f"API User {random.randint(1, 100)}",
            "subject": f"API Test {random.randint(1, 50)}"
        })

    @task
    def lookup_customer(self):
        """Look up a customer by email."""
        self.client.get("/customers/lookup", params={
            "email": f"customer{random.randint(1, 1000)}@example.com"
        })


class HealthCheckUser(HttpUser):
    """Simulates monitoring systems checking health.
    
    Low frequency, consistent pattern.
    """
    wait_time = between(5, 15)
    weight = 1

    @task(3)
    def check_health(self):
        """Check system health endpoint."""
        self.client.get("/health")

    @task
    def check_readiness(self):
        """Check system readiness endpoint."""
        self.client.get("/health/ready")

    @task
    def check_metrics(self):
        """Check channel metrics."""
        self.client.get("/metrics/channels")


class ChannelWebhookUser(HttpUser):
    """Simulates webhook traffic from external channels.
    
    Simulates Gmail and WhatsApp incoming messages.
    """
    wait_time = between(3, 12)
    weight = 2

    @task
    def gmail_webhook(self):
        """Simulate Gmail push notification."""
        self.client.post("/webhooks/gmail", json={
            "message": {
                "data": f"base64_notification_{random.randint(1, 1000)}",
                "messageId": f"test-{random.randint(1, 1000)}"
            },
            "subscription": "projects/test/subscriptions/gmail-push"
        })

    @task
    def whatsapp_webhook(self):
        """Simulate Twilio WhatsApp webhook."""
        self.client.post("/webhooks/whatsapp", data={
            "MessageSid": f"SM{random.randint(1000, 9999)}",
            "From": f"whatsapp:+1{random.randint(2000000000, 9999999999)}",
            "Body": random.choice(SAMPLE_MESSAGES),
            "ProfileName": f"User{random.randint(1, 100)}"
        })


# ─── Test Events ───────────────────────────────────────────────────────────

def on_test_start(environment):
    """Called when load test starts."""
    print("=" * 60)
    print("🚀 Load Test Started")
    print(f"Target: {environment.host}")
    print("=" * 60)


def on_test_stop(environment):
    """Called when load test completes."""
    print("=" * 60)
    print("✅ Load Test Complete")
    print("=" * 60)


events = {"test_start": on_test_start, "test_stop": on_test_stop}
