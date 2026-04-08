"""
Customer Success FTE — WhatsApp/Twilio Integration Handler
===========================================================
Phase 2: Specialization

Handles Twilio WhatsApp API integration for:
- Receiving messages via Twilio webhook
- Webhook signature validation (security)
- Sending messages via Twilio API
- Response splitting for WhatsApp character limits
- Delivery status tracking
"""

import os
import logging
from typing import Optional
from datetime import datetime

from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)


class WhatsAppHandler:
    """Handles all Twilio WhatsApp API interactions."""

    def __init__(self, account_sid: str = None, auth_token: str = None,
                 whatsapp_number: str = None):
        self.account_sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN", "")
        self.whatsapp_number = whatsapp_number or os.getenv(
            "TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886"
        )
        self.client = None
        self.validator = None
        self._initialized = False

        # Try to initialize Twilio client (graceful fallback if credentials missing)
        try:
            if self.account_sid and self.auth_token:
                from twilio.rest import Client
                from twilio.request_validator import RequestValidator

                self.client = Client(self.account_sid, self.auth_token)
                self.validator = RequestValidator(self.auth_token)
                self._initialized = True
                logger.info("Twilio WhatsApp API initialized successfully")
            else:
                logger.warning("Twilio credentials not provided (using mock mode)")
        except Exception as e:
            logger.warning(f"Twilio API not available (using mock mode): {e}")
            self._initialized = False

    async def validate_webhook(self, request: Request) -> bool:
        """Validate incoming Twilio webhook signature.
        
        This is a critical security check to ensure the webhook
        request actually came from Twilio.
        
        Args:
            request: FastAPI request object
            
        Returns:
            True if signature is valid
        """
        if not self._initialized:
            logger.debug("Skipping webhook validation (mock mode)")
            return True

        try:
            signature = request.headers.get('X-Twilio-Signature', '')
            url = str(request.url)

            # Get form data for validation
            form_data = await request.form()
            params = dict(form_data)

            is_valid = self.validator.validate(url, params, signature)

            if not is_valid:
                logger.warning("Invalid Twilio webhook signature")

            return is_valid

        except Exception as e:
            logger.error(f"Error validating Twilio webhook: {e}")
            return False

    async def process_webhook(self, form_data: dict) -> dict:
        """Process incoming WhatsApp message from Twilio webhook.
        
        Args:
            form_data: Form data from Twilio webhook
            
        Returns:
            Normalized message dict
        """
        message_body = form_data.get('Body', '').strip()
        from_number = form_data.get('From', '').replace('whatsapp:', '')
        profile_name = form_data.get('ProfileName', '')
        message_sid = form_data.get('MessageSid', '')
        num_media = form_data.get('NumMedia', '0')

        logger.info(
            f"Received WhatsApp message from {from_number}: "
            f"{message_body[:50]}..."
        )

        return {
            'channel': 'whatsapp',
            'channel_message_id': message_sid,
            'customer_phone': from_number,
            'customer_name': profile_name,
            'content': message_body,
            'received_at': datetime.utcnow().isoformat(),
            'metadata': {
                'num_media': int(num_media),
                'profile_name': profile_name,
                'wa_id': form_data.get('WaId', ''),
                'status': form_data.get('SmsStatus', ''),
                'has_media': int(num_media) > 0
            }
        }

    async def send_message(self, to_phone: str, body: str) -> dict:
        """Send WhatsApp message via Twilio.
        
        Args:
            to_phone: Recipient phone number (with or without whatsapp: prefix)
            body: Message text
            
        Returns:
            Delivery status dict
        """
        if not self._initialized:
            logger.info(f"[MOCK] Would send WhatsApp to {to_phone}: {body[:100]}...")
            return {
                'channel_message_id': f"mock-{datetime.utcnow().timestamp()}",
                'delivery_status': 'sent'
            }

        try:
            # Ensure phone number is in WhatsApp format
            if not to_phone.startswith('whatsapp:'):
                to_phone = f'whatsapp:{to_phone}'

            message = self.client.messages.create(
                body=body,
                from_=self.whatsapp_number,
                to=to_phone
            )

            logger.info(
                f"WhatsApp message sent to {to_phone}, SID: {message.sid}"
            )
            return {
                'channel_message_id': message.sid,
                'delivery_status': message.status  # 'queued', 'sent', 'delivered', 'failed'
            }

        except Exception as e:
            logger.error(f"Failed to send WhatsApp to {to_phone}: {e}")
            return {
                'channel_message_id': None,
                'delivery_status': 'failed',
                'error': str(e)
            }

    def format_response(self, response: str,
                        max_length: int = 1600) -> list[str]:
        """Format and split response for WhatsApp.
        
        WhatsApp has a 1600 character limit per message.
        This method splits long responses into multiple messages
        at natural break points (sentence endings).
        
        Args:
            response: Response text to format
            max_length: Maximum characters per message (default 1600)
            
        Returns:
            List of message chunks
        """
        if len(response) <= max_length:
            return [response]

        messages = []
        remaining = response

        while remaining:
            if len(remaining) <= max_length:
                messages.append(remaining.strip())
                break

            # Find a good break point (prefer sentence end, then word boundary)
            break_point = remaining.rfind('. ', 0, max_length)
            if break_point == -1:
                break_point = remaining.rfind('! ', 0, max_length)
            if break_point == -1:
                break_point = remaining.rfind('? ', 0, max_length)
            if break_point == -1:
                break_point = remaining.rfind(' ', 0, max_length)
            if break_point == -1:
                break_point = max_length

            chunk = remaining[:break_point + 1].strip()
            messages.append(chunk)
            remaining = remaining[break_point + 1:].strip()

        logger.info(f"Split WhatsApp response into {len(messages)} messages")
        return messages

    async def send_multi_message(self, to_phone: str, body: str,
                                  max_length: int = 1600) -> list[dict]:
        """Send a potentially long message, splitting if needed.
        
        Args:
            to_phone: Recipient phone number
            body: Message text (may be split if too long)
            max_length: Maximum characters per message
            
        Returns:
            List of delivery status dicts
        """
        chunks = self.format_response(body, max_length)
        results = []

        for chunk in chunks:
            result = await self.send_message(to_phone, chunk)
            results.append(result)

            # Small delay between messages to avoid rate limiting
            if len(chunks) > 1:
                import asyncio
                await asyncio.sleep(1)

        return results

    async def update_delivery_status(self, message_sid: str,
                                      status: str) -> dict:
        """Update message delivery status in database.
        
        Called by the status callback webhook.
        
        Args:
            message_sid: Twilio message SID
            status: New delivery status
            
        Returns:
            Update result
        """
        from production.database.queries import get_pool

        try:
            pool = await get_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE messages
                    SET delivery_status = $1,
                        metadata = jsonb_set(
                            metadata,
                            '{delivery_updated_at}',
                            to_jsonb(NOW()::text)
                        )
                    WHERE channel_message_id = $2
                """, status, message_sid)

            logger.info(f"Updated delivery status for {message_sid}: {status}")
            return {'status': 'updated', 'message_sid': message_sid}

        except Exception as e:
            logger.error(f"Failed to update delivery status: {e}")
            return {'status': 'error', 'error': str(e)}
