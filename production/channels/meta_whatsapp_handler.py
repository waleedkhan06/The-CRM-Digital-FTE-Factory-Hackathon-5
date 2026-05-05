"""
Customer Success FTE — Meta WhatsApp Cloud API Handler
=======================================================
Handles Meta (Facebook) WhatsApp Business Cloud API for:
- Receiving messages via Meta webhook
- Webhook verification (GET challenge)
- Sending messages via Meta Graph API
- No Twilio required — uses Meta directly
"""

import os
import json
import logging
import hashlib
import hmac
from typing import Optional
from datetime import datetime

import httpx
from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)

GRAPH_API_VERSION = "v19.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


class MetaWhatsAppHandler:
    """Handles Meta WhatsApp Cloud API interactions."""

    def __init__(self):
        self.phone_number_id = os.getenv("META_WA_PHONE_NUMBER_ID", "")
        self.access_token = os.getenv("META_WA_ACCESS_TOKEN", "")
        self.verify_token = os.getenv("META_WA_VERIFY_TOKEN", "crm_fte_verify")
        self.app_secret = os.getenv("META_WA_APP_SECRET", "")
        self._initialized = bool(self.phone_number_id and self.access_token)

        if self._initialized:
            logger.info("Meta WhatsApp Cloud API initialized")
        else:
            logger.warning("Meta WhatsApp credentials not set (mock mode)")

    # ── Webhook Verification ──────────────────────────────────────────────

    def verify_webhook(self, mode: str, token: str, challenge: str) -> str:
        """Handle Meta webhook verification (GET request).

        Meta sends a GET with hub.mode, hub.verify_token, hub.challenge.
        We must return hub.challenge if the token matches.
        """
        if mode == "subscribe" and token == self.verify_token:
            logger.info("Meta WhatsApp webhook verified successfully")
            return challenge
        raise HTTPException(status_code=403, detail="Webhook verification failed")

    def validate_signature(self, body: bytes, signature: str) -> bool:
        """Validate X-Hub-Signature-256 header from Meta."""
        if not self.app_secret:
            return True  # skip validation in dev if no secret set
        expected = "sha256=" + hmac.new(
            self.app_secret.encode(), body, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    # ── Parse Incoming Webhook ────────────────────────────────────────────

    def parse_incoming(self, payload: dict) -> list[dict]:
        """Parse Meta webhook payload into list of normalised message dicts."""
        messages = []
        try:
            for entry in payload.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    contacts = {
                        c["wa_id"]: c.get("profile", {}).get("name", "")
                        for c in value.get("contacts", [])
                    }
                    for msg in value.get("messages", []):
                        wa_id = msg.get("from", "")
                        msg_type = msg.get("type", "text")
                        if msg_type != "text":
                            logger.debug(f"Skipping non-text message type: {msg_type}")
                            continue
                        body = msg.get("text", {}).get("body", "")
                        messages.append({
                            "channel": "whatsapp",
                            "channel_message_id": msg.get("id", ""),
                            "customer_phone": f"+{wa_id}",
                            "customer_name": contacts.get(wa_id, ""),
                            "content": body,
                            "received_at": datetime.utcnow().isoformat(),
                            "metadata": {
                                "wa_id": wa_id,
                                "msg_type": msg_type,
                                "timestamp": msg.get("timestamp", ""),
                                "phone_number_id": value.get("metadata", {}).get("phone_number_id", ""),
                            }
                        })
        except Exception as e:
            logger.error(f"Error parsing Meta WhatsApp payload: {e}")
        return messages

    # ── Send Message ──────────────────────────────────────────────────────

    async def send_message(self, to_phone: str, body: str) -> dict:
        """Send a WhatsApp text message via Meta Cloud API."""
        to_phone = to_phone.lstrip("+")  # Meta wants number without +

        if not self._initialized:
            logger.info(f"[MOCK] Would send Meta WhatsApp to +{to_phone}: {body[:80]}...")
            return {"channel_message_id": f"mock-{datetime.utcnow().timestamp()}", "delivery_status": "sent"}

        url = f"{GRAPH_API_BASE}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "text",
            "text": {"preview_url": False, "body": body},
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                msg_id = data.get("messages", [{}])[0].get("id", "")
                logger.info(f"Meta WhatsApp sent to +{to_phone}, id: {msg_id}")
                return {"channel_message_id": msg_id, "delivery_status": "sent"}
        except Exception as e:
            logger.error(f"Failed to send Meta WhatsApp to +{to_phone}: {e}")
            return {"channel_message_id": None, "delivery_status": "failed", "error": str(e)}

    # ── Mark as Read ──────────────────────────────────────────────────────

    async def mark_read(self, message_id: str) -> None:
        """Mark an incoming message as read (shows double blue tick)."""
        if not self._initialized:
            return
        url = f"{GRAPH_API_BASE}/{self.phone_number_id}/messages"
        payload = {"messaging_product": "whatsapp", "status": "read", "message_id": message_id}
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                await client.post(url, json=payload, headers=headers)
        except Exception as e:
            logger.debug(f"Mark-read failed (non-critical): {e}")
