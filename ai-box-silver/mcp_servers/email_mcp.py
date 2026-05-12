"""
Email MCP Server for AI Employee Silver Tier
Provides email sending capabilities via Gmail API

This MCP server can be used by Claude Code to send emails
after human approval for sensitive actions.
"""
import os
import sys
import json
import base64
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class EmailMCPServer:
    """MCP Server for email operations"""
    
    def __init__(self):
        self.service = None
        self.demo_mode = True
        self.logger = None
        self._setup_logging()
        self._initialize_service()
    
    def _setup_logging(self):
        """Setup logging for the MCP server"""
        import logging
        log_dir = project_root / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / f'email_mcp_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _initialize_service(self):
        """Initialize the Gmail API service"""
        try:
            # Load environment variables
            env_file = project_root / '.env'
            if env_file.exists():
                from dotenv import load_dotenv
                load_dotenv(env_file)
            
            client_id = os.getenv('GMAIL_CLIENT_ID')
            client_secret = os.getenv('GMAIL_CLIENT_SECRET')
            refresh_token = os.getenv('GMAIL_REFRESH_TOKEN')
            
            if not all([client_id, client_secret, refresh_token]):
                self.logger.warning("Gmail credentials not configured. Running in demo mode.")
                self.demo_mode = True
                return
            
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            from google.auth.transport.requests import Request
            
            credentials = Credentials(
                None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret,
            )
            
            credentials.refresh(Request())
            self.service = build('gmail', 'v1', credentials=credentials)
            self.demo_mode = False
            self.logger.info("Email MCP service initialized successfully")
            
        except Exception as e:
            self.logger.warning(f"Could not initialize Email MCP: {e}. Running in demo mode.")
            self.demo_mode = True
            self.service = None
    
    def send_email(self, to: str, subject: str, body: str, 
                   cc: str = None, bcc: str = None, 
                   attachment_path: str = None) -> dict:
        """
        Send an email via Gmail API
        
        Args:
            to (str): Recipient email address
            subject (str): Email subject
            body (str): Email body (plain text or HTML)
            cc (str, optional): CC recipients
            bcc (str, optional): BCC recipients
            attachment_path (str, optional): Path to attachment file
            
        Returns:
            dict: Result of the send operation
        """
        try:
            if self.demo_mode or self.service is None:
                return self._demo_send_email(to, subject, body, cc, bcc, attachment_path)
            
            # Create the message
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = cc
            
            # Add body
            message.attach(MIMEText(body, 'html' if '<' in body else 'plain'))
            
            # Add attachment if provided
            if attachment_path and Path(attachment_path).exists():
                self._attach_file(message, attachment_path)
            
            # Encode the message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send the email
            sent_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            # Log the action
            self._log_action('email_send', {
                'to': to,
                'subject': subject,
                'message_id': sent_message.get('id')
            })
            
            return {
                "status": "success",
                "message": f"Email sent successfully to {to}",
                "message_id": sent_message.get('id'),
                "thread_id": sent_message.get('threadId'),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error sending email: {str(e)}"
            self.logger.error(error_msg)
            self._log_action('email_send_failed', {
                'to': to,
                'subject': subject,
                'error': str(e)
            })
            return {
                "status": "error",
                "message": error_msg,
                "timestamp": datetime.now().isoformat()
            }
    
    def _attach_file(self, message: MIMEMultipart, file_path: str):
        """Attach a file to the email message"""
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(Path(file_path).read_bytes())
        encoders.encode_base64(part)
        
        filename = Path(file_path).name
        part.add_header(
            'Content-Disposition',
            f'attachment; filename="{filename}"'
        )
        message.attach(part)
    
    def _demo_send_email(self, to: str, subject: str, body: str,
                         cc: str = None, bcc: str = None,
                         attachment_path: str = None) -> dict:
        """Demo mode - simulate sending email"""
        # Create a record of the email that would have been sent
        sent_folder = project_root / 'logs' / 'sent_emails'
        sent_folder.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        email_file = sent_folder / f'email_{timestamp}.md'
        
        email_content = f"""---
type: sent_email
status: demo_mode
to: {to}
subject: {subject}
cc: {cc or 'N/A'}
bcc: {bcc or 'N/A'}
has_attachment: {attachment_path is not None}
sent_at: {datetime.now().isoformat()}
---

# Email Sent (Demo Mode)

## Recipients
- **To**: {to}
- **CC**: {cc or 'N/A'}
- **BCC**: {bcc or 'N/A'}

## Subject
{subject}

## Body
{body}

## Attachment
{attachment_path or 'None'}

---
*This email was recorded in demo mode. No actual email was sent.*
*Configure Gmail credentials in .env to enable real sending.*
"""
        
        email_file.write_text(email_content, encoding='utf-8')
        
        self.logger.info(f"Demo email recorded: {email_file}")
        self._log_action('email_send_demo', {
            'to': to,
            'subject': subject,
            'file': str(email_file)
        })
        
        return {
            "status": "success",
            "message": f"Demo email recorded at {email_file}",
            "demo_mode": True,
            "email_file": str(email_file),
            "timestamp": datetime.now().isoformat()
        }
    
    def _log_action(self, action_type: str, details: dict):
        """Log an action for audit purposes"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "actor": "email_mcp",
            "details": details,
            "demo_mode": self.demo_mode
        }
        
        # Append to daily log file
        log_file = project_root / 'logs' / f'email_actions_{datetime.now().strftime("%Y%m%d")}.json'
        
        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text())
            except:
                logs = []
        
        logs.append(log_entry)
        log_file.write_text(json.dumps(logs, indent=2))
    
    def draft_email(self, to: str, subject: str, body: str,
                    cc: str = None, attachment_path: str = None) -> dict:
        """
        Create a draft email (doesn't send)
        
        Args:
            to (str): Recipient email address
            subject (str): Email subject
            body (str): Email body
            cc (str, optional): CC recipients
            attachment_path (str, optional): Path to attachment
            
        Returns:
            dict: Result with draft information
        """
        try:
            if self.demo_mode or self.service is None:
                return self._demo_draft_email(to, subject, body, cc, attachment_path)
            
            # Create the message
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            if cc:
                message['cc'] = cc
            
            message.attach(MIMEText(body, 'html' if '<' in body else 'plain'))
            
            if attachment_path and Path(attachment_path).exists():
                self._attach_file(message, attachment_path)
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Create draft
            draft = self.service.users().drafts().create(
                userId='me',
                body={'message': {'raw': raw_message}}
            ).execute()
            
            self._log_action('email_draft', {
                'to': to,
                'subject': subject,
                'draft_id': draft.get('id')
            })
            
            return {
                "status": "success",
                "message": f"Draft email created",
                "draft_id": draft.get('id'),
                "message_id": draft.get('message', {}).get('id'),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error creating draft: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _demo_draft_email(self, to: str, subject: str, body: str,
                          cc: str = None, attachment_path: str = None) -> dict:
        """Demo mode - simulate creating draft"""
        drafts_folder = project_root / 'drafts'
        drafts_folder.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        draft_file = drafts_folder / f'draft_{timestamp}.md'
        
        draft_content = f"""---
type: email_draft
to: {to}
subject: {subject}
cc: {cc or 'N/A'}
has_attachment: {attachment_path is not None}
created_at: {datetime.now().isoformat()}
---

# Email Draft

## To: {to}
## Subject: {subject}

{body}
"""
        
        draft_file.write_text(draft_content, encoding='utf-8')
        
        return {
            "status": "success",
            "message": f"Draft created at {draft_file}",
            "demo_mode": True,
            "draft_file": str(draft_file),
            "timestamp": datetime.now().isoformat()
        }


# MCP Protocol Implementation
def create_message(method: str, params: dict) -> dict:
    """Create an MCP message"""
    return {
        "jsonrpc": "2.0",
        "id": params.get("id", 1),
        "method": method,
        "params": params
    }


def handle_request(request: dict, server: EmailMCPServer) -> dict:
    """Handle an MCP request"""
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id", 1)
    
    try:
        if method == "email/send":
            result = server.send_email(
                to=params.get("to"),
                subject=params.get("subject"),
                body=params.get("body"),
                cc=params.get("cc"),
                bcc=params.get("bcc"),
                attachment_path=params.get("attachment_path")
            )
        elif method == "email/draft":
            result = server.draft_email(
                to=params.get("to"),
                subject=params.get("subject"),
                body=params.get("body"),
                cc=params.get("cc"),
                attachment_path=params.get("attachment_path")
            )
        elif method == "email/status":
            result = {
                "status": "success",
                "demo_mode": server.demo_mode,
                "service_available": server.service is not None,
                "timestamp": datetime.now().isoformat()
            }
        else:
            result = {
                "status": "error",
                "message": f"Unknown method: {method}"
            }
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }


# CLI interface for testing
def main():
    """Test the Email MCP server"""
    server = EmailMCPServer()
    
    print("=== Email MCP Server Test ===\n")
    print(f"Demo mode: {server.demo_mode}")
    print(f"Service available: {server.service is not None}\n")
    
    # Test sending an email
    print("Testing email send...")
    result = server.send_email(
        to="test@example.com",
        subject="Test Email from AI Employee",
        body="<h1>Hello!</h1><p>This is a test email from the AI Employee system.</p>"
    )
    print(json.dumps(result, indent=2))
    
    # Test creating a draft
    print("\nTesting draft creation...")
    result = server.draft_email(
        to="test@example.com",
        subject="Draft Test",
        body="This is a draft email."
    )
    print(json.dumps(result, indent=2))
    
    # Test status
    print("\nTesting status check...")
    result = server.send_email.__class__.__doc__  # Just checking the server
    status_request = {"method": "email/status", "params": {"id": 1}}
    response = handle_request(status_request, server)
    print(json.dumps(response, indent=2))


if __name__ == "__main__":
    main()
