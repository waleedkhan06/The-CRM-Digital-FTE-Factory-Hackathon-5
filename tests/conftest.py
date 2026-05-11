"""
pytest configuration — loads .env and sets asyncio mode.
"""
import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# ── Make sure project root is on sys.path ──────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ── Load .env so tests pick up POSTGRES_*, OPENAI_API_KEY, etc. ────────────
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT, ".env"), override=False)
except ImportError:
    pass  # python-dotenv not installed — env vars must be set manually


# ── Session-scoped DB pool mock — prevents asyncpg event loop conflicts ─────

def _make_mock_pool():
    """Build a mock asyncpg pool that never touches a real DB."""
    fake_row = {"id": "test-id-001", "email": "test@example.com",
                "phone": None, "name": "Test User", "status": "active",
                "conversation_id": "conv-001", "customer_id": "cust-001",
                "ticket_id": "TK-TEST-001", "source_channel": "web_form",
                "created_at": "2026-01-01T00:00:00"}

    mock_conn = AsyncMock()
    mock_conn.fetchrow = AsyncMock(return_value=fake_row)
    mock_conn.fetch = AsyncMock(return_value=[fake_row])
    mock_conn.fetchval = AsyncMock(return_value="TK-TEST-001")
    mock_conn.execute = AsyncMock(return_value="INSERT 0 1")

    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock(return_value=mock_ctx)
    mock_pool.close = AsyncMock()
    return mock_pool


@pytest.fixture(scope="session", autouse=True)
def mock_db_pool():
    """Patch the asyncpg pool for the entire test session."""
    mock_pool = _make_mock_pool()
    with patch("production.database.queries._pool", mock_pool), \
         patch("production.database.queries.get_pool", AsyncMock(return_value=mock_pool)):
        yield mock_pool
