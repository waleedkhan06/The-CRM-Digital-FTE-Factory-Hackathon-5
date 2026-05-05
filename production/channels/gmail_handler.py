"""
Customer Success FTE — Gmail Integration Handler
==================================================
Phase 2: Specialization

Handles Gmail API integration for:
- Receiving emails via Pub/Sub push notifications
- Parsing email content (headers, body, attachments)
- Sending replies via Gmail API
- Thread management
"""

import base64
import email as email_module
import os
import re
import logging
from typing import Optional
from datetime import datetime
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


class GmailHandler:
    """Handles all Gmail API interactions."""

    def __init__(self, credentials_path: str = None):
        self.credentials_path = credentials_path or os.getenv(
            "GMAIL_CREDENTIALS_PATH", "credentials/gmail.json"
        )
        self.service = None
        self._initialized = False

        # Try to initialize Gmail API (graceful fallback if credentials missing)
        try:
            self._initialize_service()
        except Exception as e:
            logger.warning(f"Gmail API not available (using mock mode): {e}")
            self._initialized = False

    def _initialize_service(self):
        """Initialize Gmail API service.

        Supports two credential types (auto-detected):
        1. OAuth2 client secret JSON  — produced by Google Cloud Console
           (the client_secret_*.json file in the project root)
        2. Service account JSON       — for server-to-server auth

        For OAuth2 client secrets a pre-authorised token file is expected at
        GMAIL_TOKEN_PATH (default: credentials/gmail_token.json).  If the
        token file does not exist the handler starts in mock mode so the
        rest of the system is not blocked.
        """
        from googleapiclient.discovery import build

        # ── Option 1: try OAuth2 token (from client secret flow) ──────────
        token_path = os.getenv("GMAIL_TOKEN_PATH", "credentials/gmail_token.json")
        if os.path.exists(token_path):
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request

            creds = Credentials.from_authorized_user_file(
                token_path,
                scopes=['https://www.googleapis.com/auth/gmail.modify']
            )
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # persist refreshed token
                with open(token_path, "w") as f:
                    f.write(creds.to_json())

            self.service = build('gmail', 'v1', credentials=creds)
            self._initialized = True
            logger.info("Gmail API initialized via OAuth2 token")
            return

        # ── Option 2: try service account JSON ────────────────────────────
        if os.path.exists(self.credentials_path):
            from google.oauth2.service_account import Credentials as SACredentials
            creds = SACredentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/gmail.modify']
            )
            self.service = build('gmail', 'v1', credentials=creds)
            self._initialized = True
            logger.info("Gmail API initialized via service account")
            return

        logger.warning(
            f"No Gmail credentials found at '{token_path}' or '{self.credentials_path}'. "
            "Running in mock mode."
        )
        self._initialized = False

    async def setup_push_notifications(self, topic_name: str) -> dict:
        """Set up Gmail push notifications via Pub/Sub.
        
        Args:
            topic_name: Google Cloud Pub/Sub topic name
            
        Returns:
            Setup response from Gmail API
        """
        if not self._initialized:
            logger.warning("Gmail API not initialized, skipping push notification setup")
            return {"status": "mock", "topic": topic_name}

        try:
            request = {
                'labelIds': ['INBOX'],
                'topicName': topic_name,
                'labelFilterAction': 'include'
            }
            response = self.service.users().watch(
                userId='me',
                body=request
            ).execute()
            logger.info(f"Gmail push notifications configured: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to set up Gmail push notifications: {e}")
            raise

    async def process_notification(self, pubsub_message: dict) -> list[dict]:
        """Process incoming Pub/Sub notification from Gmail.
        
        Args:
            pubsub_message: Pub/Sub message containing Gmail notification
            
        Returns:
            List of parsed email messages
        """
        if not self._initialized:
            return [self._mock_email_message()]

        try:
            history_id = pubsub_message.get('historyId')

            if not history_id:
                logger.warning("No historyId in Pub/Sub notification")
                return []

            # Get new messages since last history ID
            history = self.service.users().history().list(
                userId='me',
                startHistoryId=history_id,
                historyTypes=['messageAdded']
            ).execute()

            messages = []
            for record in history.get('history', []):
                for msg_added in record.get('messagesAdded', []):
                    msg_id = msg_added['message']['id']
                    try:
                        message = await self.get_message(msg_id)
                        messages.append(message)
                    except Exception as e:
                        logger.error(f"Failed to get message {msg_id}: {e}")

            logger.info(f"Processed {len(messages)} new emails from Gmail")
            return messages

        except Exception as e:
            logger.error(f"Error processing Gmail notification: {e}")
            return []

    async def fetch_unread(self, max_results: int = 10) -> list[dict]:
        """Fetch unread emails from Gmail inbox.

        Returns list of normalised message dicts, newest first.
        Marks each fetched message as read.
        """
        if not self._initialized:
            logger.warning("Gmail not initialised — returning mock message")
            return [self._mock_email_message()]

        results = self.service.users().messages().list(
            userId='me',
            q='is:unread in:inbox',
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])
        parsed = []
        for m in messages:
            try:
                parsed.append(await self.get_message(m['id']))
                # Mark as read
                self.service.users().messages().modify(
                    userId='me',
                    id=m['id'],
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()
            except Exception as e:
                logger.error(f"Error fetching message {m['id']}: {e}")
        return parsed

    async def get_message(self, message_id: str) -> dict:
        """Fetch and parse a Gmail message.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            Normalized message dict
        """
        if not self._initialized:
            return self._mock_email_message()

        msg = self.service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()

        # Parse headers
        headers = {
            h['name']: h['value']
            for h in msg['payload']['headers']
        }

        # Extract body
        body = self._extract_body(msg['payload'])

        # Extract email address
        customer_email = self._extract_email(headers.get('From', ''))

        return {
            'channel': 'email',
            'channel_message_id': message_id,
            'customer_email': customer_email,
            'customer_name': self._extract_name(headers.get('From', '')),
            'subject': headers.get('Subject', ''),
            'content': body,
            'received_at': datetime.utcnow().isoformat(),
            'thread_id': msg.get('threadId'),
            'metadata': {
                'headers': headers,
                'labels': msg.get('labelIds', []),
                'internal_date': headers.get('Date', ''),
                'message_id': headers.get('Message-ID', '')
            }
        }

    def _extract_body(self, payload: dict) -> str:
        """Extract text body from email payload.
        
        Handles multipart emails by preferring text/plain over text/html.
        """
        # Try direct body
        if 'body' in payload and payload['body'].get('data'):
            return base64.urlsafe_b64decode(
                payload['body']['data']
            ).decode('utf-8')

        # Try parts
        if 'parts' in payload:
            # First try text/plain
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain' and part['body'].get('data'):
                    return base64.urlsafe_b64decode(
                        part['body']['data']
                    ).decode('utf-8')

            # Then try text/html (fallback)
            for part in payload['parts']:
                if part['mimeType'] == 'text/html' and part['body'].get('data'):
                    html_content = base64.urlsafe_b64decode(
                        part['body']['data']
                    ).decode('utf-8')
                    # Strip HTML tags
                    return re.sub(r'<[^>]+>', '', html_content)

            # Recursive search in nested parts
            for part in payload['parts']:
                if 'parts' in part:
                    body = self._extract_body(part)
                    if body:
                        return body

        return ''

    def _extract_email(self, from_header: str) -> str:
        """Extract email address from From header."""
        match = re.search(r'<(.+?)>', from_header)
        return match.group(1) if match else from_header.strip()

    def _extract_name(self, from_header: str) -> str:
        """Extract name from From header."""
        match = re.match(r'^"?(.+?)"?\s*<', from_header)
        if match:
            return match.group(1).strip('"')
        return ''

    async def send_reply(self, to_email: str, subject: str, body: str,
                         thread_id: str = None) -> dict:
        """Send email reply via Gmail API.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body text
            thread_id: Optional thread ID for threading
            
        Returns:
            Delivery status dict
        """
        if not self._initialized:
            logger.info(f"[MOCK] Would send email to {to_email}: {body[:100]}...")
            return {
                'channel_message_id': f"mock-{datetime.utcnow().timestamp()}",
                'delivery_status': 'sent'
            }

        try:
            message = MIMEText(body)
            message['to'] = to_email
            message['subject'] = (
                f"Re: {subject}" if not subject.startswith('Re:') else subject
            )

            raw = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode('utf-8')

            send_request = {'raw': raw}
            if thread_id:
                send_request['threadId'] = thread_id

            result = self.service.users().messages().send(
                userId='me',
                body=send_request
            ).execute()

            logger.info(f"Email sent to {to_email}, message ID: {result['id']}")
            return {
                'channel_message_id': result['id'],
                'delivery_status': 'sent'
            }

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return {
                'channel_message_id': None,
                'delivery_status': 'failed',
                'error': str(e)
            }

    def parse_pubsub_payload(self, payload: dict) -> dict:
        """Decode and parse a Google Cloud Pub/Sub push payload.

        Args:
            payload: Raw Pub/Sub push body with 'message.data' (base64)

        Returns:
            Decoded dict (emailAddress, historyId, etc.)
        """
        try:
            message = payload.get("message", {})
            data_b64 = message.get("data", "")
            # Add padding if needed
            padding = 4 - len(data_b64) % 4
            if padding != 4:
                data_b64 += "=" * padding
            decoded = base64.b64decode(data_b64).decode("utf-8")
            import json
            return json.loads(decoded)
        except Exception as e:
            logger.warning(f"Failed to parse Pub/Sub payload: {e}")
            return {}

    def parse_email_message(self, gmail_message: dict) -> dict:
        """Parse a raw Gmail API message object into a normalised dict.

        Args:
            gmail_message: Full message dict from Gmail API (format='full')

        Returns:
            Normalised message dict with from_email, subject, body, etc.
        """
        payload = gmail_message.get("payload", {})
        headers = {
            h["name"]: h["value"]
            for h in payload.get("headers", [])
        }

        body = self._extract_body(payload)
        from_header = headers.get("From", "")

        return {
            "id": gmail_message.get("id", ""),
            "thread_id": gmail_message.get("threadId", ""),
            "from_email": self._extract_email(from_header),
            "from_name": self._extract_name(from_header),
            "subject": headers.get("Subject", ""),
            "body": body,
            "date": headers.get("Date", ""),
            "message_id": headers.get("Message-ID", ""),
            "in_reply_to": headers.get("In-Reply-To", ""),
        }

    def build_reply_message(self, to_email: str, subject: str, body: str,
                             thread_id: str = None,
                             in_reply_to: str = None) -> dict:
        """Build a base64-encoded MIME reply message ready for Gmail API send.

        Args:
            to_email: Recipient email
            subject: Subject line
            body: Plain-text body
            thread_id: Optional Gmail thread ID for threading
            in_reply_to: Optional Message-ID of the message being replied to

        Returns:
            Dict with 'raw' (base64url-encoded MIME) and optional 'threadId'
        """
        msg = MIMEText(body, "plain", "utf-8")
        msg["To"] = to_email
        msg["Subject"] = subject if subject.startswith("Re:") else f"Re: {subject}"
        if in_reply_to:
            msg["In-Reply-To"] = in_reply_to
            msg["References"] = in_reply_to

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        result = {"raw": raw}
        if thread_id:
            result["threadId"] = thread_id
        return result

    def _mock_email_message(self) -> dict:
        """Return a mock email for testing when Gmail API is unavailable."""
        return {
            'channel': 'email',
            'channel_message_id': f"mock-{datetime.utcnow().timestamp()}",
            'customer_email': 'test@example.com',
            'customer_name': 'Test User',
            'subject': 'Test Email',
            'content': 'This is a mock email for testing purposes.',
            'received_at': datetime.utcnow().isoformat(),
            'thread_id': 'mock-thread',
            'metadata': {}
        }
