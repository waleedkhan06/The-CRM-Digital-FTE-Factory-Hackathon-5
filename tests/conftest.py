"""
pytest configuration — loads .env and sets asyncio mode.
"""
import os
import sys
import pytest

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
